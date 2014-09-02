'''
Created on Sep 1, 2014

@author: Qurban Ali
'''
import site
site.addsitedir(r'R:\Pipe_Repo\Users\Qurban\utilities')
from uiContainer import uic
from PyQt4.QtGui import QIcon, QMessageBox
import os
import os.path as osp
import qtify_maya_window as qtfy
import pymel.core as pc

root_path = osp.dirname(osp.dirname(__file__))
ui_path = osp.join(root_path, 'ui')
icon_path = osp.join(root_path, 'icons')

Form, Base = uic.loadUiType(osp.join(ui_path, 'submitter.ui'))
class Submitter(Form, Base):
    def __init__(self, parent=qtfy.getMayaWindow()):
        super(Submitter, self).__init__(parent)
        self.setupUi(self)
        self.items = []
        self.addButton.setIcon(QIcon(osp.join(icon_path, 'ic_add.png')))
        search_ic_path = osp.join(icon_path, 'ic_search.png').replace('\\','/')
        style_sheet = ('\nbackground-image: url(%s);'+
                       '\nbackground-repeat: no-repeat;'+
                       '\nbackground-position: center left;')%search_ic_path
        style_sheet = self.searchBox.styleSheet() + style_sheet
        self.searchBox.setStyleSheet(style_sheet)
        
        self.addButton.clicked.connect(self.showForm)
        
    def showForm(self):
        form = ShotForm(self)
        form.show()
    
    def addItem(self, item):
        self.items.append(item)
        
    def addItems(self, items):
        self.items.extend(items)
        
    def clear(self):
        for item in self.items:
            item.deleteLater()
        del self.items[:]
    
    def getItems(self):
        return self.items
    
    def poplate(self):
        pass

    def editItem(self, item):
        ShotForm(self, item).show()
    
    def createItem(self, data):
        item = Item(self)
        item.setTitle(data['name'])
        item.setCamera(data['camera'])
        item.setFrame(' to '.join(data['frame'].split('_')))
        item.setPath(data['path'])
        self.items.append(item)
        self.layout.addWidget(item)
        
    def closeEvent(self, event):
        self.deleteLater()
        
Form1, Base1 = uic.loadUiType(osp.join(ui_path, 'form.ui'))
class ShotForm(Form1, Base1):
    
    def __init__(self, parent=None, item=None):
        super(ShotForm, self).__init__(parent)
        self.setupUi(self)
        self.parentWin = parent
        self.item = item
        if item:
            self.createButton.setText('Edit')
        self.startFrame = None
        self.endFrame = None
        self.addCameras()
        
        self.cameraBox.activated.connect(self.handleCameraBox)
        self.createButton.clicked.connect(self.create)
        self.keyFrameButton.clicked.connect(self.handleKeyFrameClick)
        
    def handleCameraBox(self, camera):
        camera = str(camera)
        if self.keyFrameButton.isChecked():
            self.startFrame, self.endFrame = self.getKeyFrame()
            self.startFrameBox.setValue(self.startFrame)
            self.endFrameBox.setValue(self.endFrame)
    
    def addCameras(self):
        cams = pc.ls(type='camera')
        self.cameraBox.addItems([cam.name() for cam in cams
                                if cam.orthographic.get() == False])
        
    def populate(self):
        pass
    
    def getKeyFrame(self):
        camera = pc.PyNode(str(self.cameraBox.currentText()))
        animCurves = pc.listConnections(camera.firstParent(), scn=True,
                                        d=False, s=True)
        if not animCurves:
            showMessage(self,
                        msg='No in out found on the selected camera',
                        icon=QMessageBox.Warning)
            self.keyFrameButton.setChecked(False)
            return 0, 1

        frames = pc.keyframe(animCurves[0], q=True)
        if not frames:
            showMessage(self, msg='No in out found on the selected camera',
                        icon=QMessageBox.Warning)
            self.keyFrameButton.setChecked(False)
            return 0, 1

        return frames[0], frames[-1]
    
    def handleKeyFrameClick(self):
        if self.keyFrameButton.isChecked():
            self.startFrame, self.endFrame = self.getKeyFrame()
            self.startFrameBox.setValue(self.startFrame)
            self.endFrameBox.setValue(self.endFrame)
    
    def create(self):
        data = {}
        name = str(self.nameBox.text())
        if not name:
            showMessage(self, msg='Shot name not specified')
            return
        data['name'] = name
        camera = str(self.cameraBox.currentText())
        data['camera'] = camera
        if self.keyFrameButton.isChecked():
            start = self.startFrame
            end = self.endFrame
        else:
            start = self.startFrameBox.value()
            end = self.endFrameBox.value()
        data['frame'] = str(start) +'_'+ str(end)
        path = str(self.pathBox.text())
        if not path:
            showMessage(self,
                        msg='Path not specified', icon=QMessageBox.Warning)
            return
        data['path'] = path
        if self.item:
            self.item.setTitle(name)
            self.item.setCamera(camera)
            self.item.setFrame(start +' to '+ end)
            self.item.setPath(path)
        else:
            self.parentWin.createItem(data)
        
    def closeEvent(self, event):
        self.deleteLater()

Form2, Base2 = uic.loadUiType(osp.join(ui_path, 'item.ui'))
class Item(Form2, Base2):
    def __init__(self, parent=None):
        super(Item, self).__init__(parent)
        self.setupUi(self)
        self.parentWin = parent
        
        self.editButton.setIcon(QIcon(osp.join(icon_path, 'ic_edit.png')))
        
        self.editButton.clicked.connect(self.edit)
        
    def setTitle(self, title):
        self.nameLabel.setText(title)
        
    def getTitle(self):
        return str(self.nameLabel.text())
        
    def setCamera(self, camera):
        self.cameraLabel.setText(camera)
        
    def getCamera(self):
        return str(self.cameraLabel.text())
    
    def setFrame(self, frame):
        self.frameLabel.setText(frame)
        
    def getFrame(self):
        return str(self.frameLabel.text())
        
    def setPath(self, path):
        self.pathLabel.setText(path)
        
    def getPath(self):
        return str(self.pathLabel.text())
    
    def setChecked(self, state):
        self.selectButton.setChecked(state)
        
    def isChecked(self):
        return self.selectButton.isChecked()
    
    def toggleSelection(self):
        self.selectButton.setChecked(not self.selectButton.isChecked())
        
    def mouseReleaseEvent(self, event):
        self.toggleSelection()
    
    def edit(self):
        self.parentWin.editItem(self)
        
def showMessage(parent, title = 'Shot Export',
                msg = 'Message', btns = QMessageBox.Ok,
                icon = None, ques = None, details = None):

    if msg:
        mBox = QMessageBox(parent)
        mBox.setWindowTitle(title)
        mBox.setText(msg)
        if ques:
            mBox.setInformativeText(ques)
        if icon:
            mBox.setIcon(icon)
        if details:
            mBox.setDetailedText(details)
        mBox.setStandardButtons(btns)
        buttonPressed = mBox.exec_()
        return buttonPressed