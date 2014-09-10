'''
Created on Sep 1, 2014

@author: Qurban Ali
'''
import site
site.addsitedir(r'R:\Pipe_Repo\Users\Qurban\utilities')
from uiContainer import uic
from PyQt4.QtGui import QIcon, QMessageBox, QFileDialog, qApp
from PyQt4 import QtCore
import os.path as osp
import qtify_maya_window as qtfy
import pymel.core as pc
import re
import subprocess
import backend
reload(backend)

root_path = osp.dirname(osp.dirname(__file__))
ui_path = osp.join(root_path, 'ui')
icon_path = osp.join(root_path, 'icons')

Form, Base = uic.loadUiType(osp.join(ui_path, 'submitter.ui'))
class Submitter(Form, Base):
    _previousPath = ''
    def __init__(self, parent=qtfy.getMayaWindow()):
        super(Submitter, self).__init__(parent)
        self.setupUi(self)
        self.progressBar.hide()
        self.items = []
        self.collapsed = False
        self.addButton.setIcon(QIcon(osp.join(icon_path, 'ic_add.png')))
        self.collapseButton.setIcon(QIcon(osp.join(icon_path,
                                                   'ic_toggle_collapse')))
        search_ic_path = osp.join(icon_path, 'ic_search.png').replace('\\','/')
        style_sheet = ('\nbackground-image: url(%s);'+
                       '\nbackground-repeat: no-repeat;'+
                       '\nbackground-position: center left;')%search_ic_path
        style_sheet = self.searchBox.styleSheet() + style_sheet
        self.searchBox.setStyleSheet(style_sheet)
        
        self.collapseButton.clicked.connect(self.toggleCollapseAll)
        self.addButton.clicked.connect(self.showForm)
        self.selectAllButton.clicked.connect(self.selectAll)
        self.searchBox.textChanged.connect(self.searchShots)
        self.searchBox.returnPressed.connect(lambda: self.searchShots
                                             (str(self.searchBox.text())))
        self.exportButton.clicked.connect(self.export)
        self.poplate()
        
    def toggleCollapseAll(self):
        self.collapsed = not self.collapsed
        for item in self.items:
            item.toggleCollapse(self.collapsed)    
    
    def searchShots(self, text):
        text = str(text).lower()
        for item in self.items:
            if text in item.getTitle().lower():
                item.show()
            else:
                item.hide()
        
    def selectAll(self):
        for item in self.items:
            item.setChecked(self.selectAllButton.isChecked())
            
    def itemClicked(self):
        flag = True
        for item in self.items:
            if not item.isChecked():
                flag = False
                break
        self.selectAllButton.setChecked(flag)
        
    def showForm(self):
        ShotForm(self).show()
    
    def addItem(self, item):
        self.items.append(item)
        
    def addItems(self, items):
        self.items.extend(items)
        
    def removeItem(self, item):
        pc.PyNode(item.getCamera()).shotInfo.delete()
        self.items.remove(item)
        item.deleteLater()
        
    def clear(self):
        for item in self.items:
            item.deleteLater()
        del self.items[:]
    
    def getItems(self):
        return self.items
    
    def poplate(self):
        for cam in [x.firstParent() for x in pc.ls(type='camera')
                    if x.orthographic.get() == False]:
            if pc.attributeQuery('shotInfo', node=cam, exists=True):
                data = eval(cam.shotInfo.get())
                self.createItem(data)

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
        item.setChecked(self.selectAllButton.isChecked())
        item.toggleCollapse(self.collapsed)
        

    def export(self):
        data = {}
        self.exportButton.setEnabled(False)
        self.closeButton.setEnabled(False)
        self.progressBar.show()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(len([i for i in self.items
                                         if i.isChecked()]))
        self.progressBar.setValue(0)
        qApp.processEvents()
        count = 1
        origCam = pc.lookThru(q=True)
        errors = {}
        for item in self.items:
            try:
                if item.isChecked():
                    data.clear()
                    data['start'] = item.getFrame().split()[0]
                    data['end'] = item.getFrame().split()[-1]
                    data['path'] = osp.join(item.getPath(), item.getTitle())
                    pc.select(item.getCamera()); pc.lookThru(item.getCamera())
                    backend.playblast(data)
                    self.progressBar.setValue(count)
                    qApp.processEvents()
                    count += 1
            except Exception as e:
                errors[item.getTitle()] = str(e)
        self.progressBar.hide()
        pc.lookThru(origCam)
        if errors:
            detail = ''
            for shot in errors:
                detail += 'Shot: '+ shot +'\nReason: '+ errors[shot] +'\n\n'
            showMessage(self, title='Error', msg=str(len(errors))+
                        ' shot(s) was not exported successfully',
                        icon=QMessageBox.Critical, details=detail)
        self.exportButton.setEnabled(True)
        self.closeButton.setEnabled(True)
        
    def closeEvent(self, event):
        self.deleteLater()
        
Form1, Base1 = uic.loadUiType(osp.join(ui_path, 'form.ui'))
class ShotForm(Form1, Base1):
    
    def __init__(self, parent=None, item=None):
        super(ShotForm, self).__init__(parent)
        self.setupUi(self)
        self.parentWin = parent
        self.addCameras()
        self.item = item
        if item:
            self.createButton.setText('Ok')
            self.populate()
        self.startFrame = None
        self.endFrame = None

        self.upButton.setIcon(QIcon(osp.join(icon_path, 'ic_up.png')))
        self.downButton.setIcon(QIcon(osp.join(icon_path, 'ic_down.png')))
        
        # this code shall remain here until the layer UI is populated
        self.upButton.hide()
        self.downButton.hide()
        self.allLayersBox.hide()
        self.selectedLayersBox.hide()
        self.resize(self.sizeHint())
        
        self.cameraBox.activated.connect(self.handleCameraBox)
        self.createButton.clicked.connect(self.create)
        self.keyFrameButton.clicked.connect(self.handleKeyFrameClick)
        self.browseButton.clicked.connect(self.browseFolder)
        
    def browseFolder(self):
        path = self.parentWin._previousPath
        if not path: 
            path = pc.workspace(q=1, dir=1)
        path = QFileDialog.getExistingDirectory(self, 'Select Folder',
                path, QFileDialog.ShowDirsOnly)
        if path:
            self.parentWin._previousPath = path
            self.pathBox.setText(path)
        
    def handleCameraBox(self, camera):
        camera = str(camera)
        if self.keyFrameButton.isChecked():
            self.startFrame, self.endFrame = self.getKeyFrame()
            self.startFrameBox.setValue(self.startFrame)
            self.endFrameBox.setValue(self.endFrame)
    
    def addCameras(self):
        cams = pc.ls(type='camera')
        self.cameraBox.addItems([cam.firstParent().name() for cam in cams
                                if cam.orthographic.get() == False])
        self.cameraBox.view().setFixedWidth(self.cameraBox.sizeHint().width())
        
    def populate(self):
        self.nameBox.setText(self.item.getTitle())
        camera = self.item.getCamera()
        for index in range(self.cameraBox.count()):
            if camera == str(self.cameraBox.itemText(index)):
                self.cameraBox.setCurrentIndex(index)
                break
        self.startFrameBox.setValue(float(self.item.getFrame().split()[0]))
        self.endFrameBox.setValue(float(self.item.getFrame().split()[-1]))
        self.pathBox.setText(self.item.getPath())
    
    def getKeyFrame(self):
        camera = pc.PyNode(str(self.cameraBox.currentText()))
        animCurves = pc.listConnections(camera, scn=True,
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
        if not osp.exists(path):
            showMessage(self, title='Error', msg='The system can not find '+
                        'the path specified', icon=QMessageBox.Information)
            return
        data['path'] = path
        for itm in self.parentWin.getItems():
            if itm.getCamera() == data['camera']:
                if self.item:
                    if itm != self.item:
                        self.parentWin.removeItem(itm)
                else:
                    self.parentWin.removeItem(itm)
        if self.item:
            if camera != self.item.getCamera():
                pc.PyNode(self.item.getCamera()).shotInfo.delete()
            self.item.setTitle(name)
            self.item.setCamera(camera)
            self.item.setFrame(str(start) +' to '+ str(end))
            self.item.setPath(path)
        else:
            self.parentWin.createItem(data)
            
        camera = pc.PyNode(camera)
        if not pc.attributeQuery('shotInfo', node=camera, exists=True):
            pc.addAttr(camera, ln='shotInfo', sn='shin', dt='string',
                       h=True)
#         else:
#             btn = showMessage(self, title='Shot Exists', msg='A shot named '+
#                         eval(camera.shotInfo.get())['name'] +' already '+
#                         'exists on this camera', ques='Do you want to '+
#                         'replace the existing shot?', icon=QMessageBox.Question,
#                         btns=QMessageBox.Yes|QMessageBox.No)
#             if btn == QMessageBox.Yes:
        camera.shotInfo.set(str(data))
#             else:
#                 pass
        if self.item:
            self.accept()
        
    def closeEvent(self, event):
        self.deleteLater()

Form2, Base2 = uic.loadUiType(osp.join(ui_path, 'item.ui'))
class Item(Form2, Base2):
    
    version = int(re.search('\\d{4}', pc.about(v=True)).group())
    if version < 2014:
        clicked = QtCore.pyqtSignal()
    else:
        clicked = QtCore.Signal()
    
    def __init__(self, parent=None):
        super(Item, self).__init__(parent)
        self.setupUi(self)
        self.parentWin = parent
        self.collapsed = False
        self.style = ('background-image: url(%s);\n'+
                      'background-repeat: no-repeat;\n'+
                      'background-position: center right')
        
        self.editButton.setIcon(QIcon(osp.join(icon_path, 'ic_edit.png')))
        self.deleteButton.setIcon(QIcon(osp.join(icon_path, 'ic_delete.png')))
        self.iconLabel.setStyleSheet(self.style%osp.join(icon_path,
                                                         'ic_collapse.png'))
        
        self.editButton.clicked.connect(self.edit)
        self.clicked.connect(self.parentWin.itemClicked)
        self.selectButton.clicked.connect(self.parentWin.itemClicked)
        self.deleteButton.clicked.connect(self.delete)
        self.browseButton.clicked.connect(self.openLocation)
        self.titleFrame.mouseReleaseEvent = self.collapse
        
    def collapse(self, event=None):
        if self.collapsed:
            self.frame.show()
            self.collapsed = False
            path = osp.join(icon_path, 'ic_collapse.png')
        else:
            self.frame.hide()
            self.collapsed = True
            path = osp.join(icon_path, 'ic_expand.png')
        path = path.replace('\\', '/')
        self.iconLabel.setStyleSheet(self.style%path)
    
    def toggleCollapse(self, state):
        self.collapsed = not state
        self.collapse()
        
    def openLocation(self):
        subprocess.call('explorer %s'%self.getPath(), shell=True)
        
    def delete(self):
        btn = showMessage(self, title='Delete Shot', msg='Are you sure, delete '
                    +'"'+ self.getTitle() +'"?', icon=QMessageBox.Critical,
                    btns=QMessageBox.Yes|QMessageBox.No)
        if btn == QMessageBox.Yes:
            self.parentWin.removeItem(self)
        else:
            pass
        
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
        self.clicked.emit()
    
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
