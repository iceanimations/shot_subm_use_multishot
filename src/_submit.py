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
import appUsageApp
reload(backend)

Playlist = backend.Playlist
PlayblastExport = backend.PlayblastExport

root_path = osp.dirname(osp.dirname(__file__))
ui_path = osp.join(root_path, 'ui')
icon_path = osp.join(root_path, 'icons')

Form, Base = uic.loadUiType(osp.join(ui_path, 'submitter.ui'))
class Submitter(Form, Base):
    _previousPath = ''
    _playlist = None
    def __init__(self, parent=qtfy.getMayaWindow()):
        super(Submitter, self).__init__(parent)
        self.setupUi(self)

        # setting up UI
        self.progressBar.hide()
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

        # Populating Items
        self._playlist = Playlist()
        self.items = []
        self.populate()

        appUsageApp.updateDatabase('shot_subm')

    def showPathBox(self):
        Path(self).show()
        
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

    def removeItem(self, item):
        self.items.remove(item)
        item.deleteLater()
        self._playlist.removeItem(item.pl_item)

    def clear(self):
        for item in self.items:
            item.deleteLater()
        del self.items[:]

    def getItems(self):
        return self.items

    def getItem(self, pl_item, forceCreate=False):
        thisItem = None
        for item in self.items:
            if item.pl_item == pl_item:
                thisItem = item
        if not thisItem and forceCreate:
            thisItem = self.createItem(pl_item)
        return thisItem

    def populate(self):
        for pl_item in self._playlist.getItems():
            self.createItem(pl_item)

    def editItem(self, pl_item):
        ShotForm(self, pl_item).show()

    def createItem(self, pl_item):
        item = Item(self, pl_item)
        self.items.append(item)
        self.layout.addWidget(item)
        item.setChecked(self.selectAllButton.isChecked())
        item.toggleCollapse(self.collapsed)
        item.update()
        return item

    def export(self):
        self.exportButton.setEnabled(False)
        self.closeButton.setEnabled(False)
        self.progressBar.show()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(len([i for i in self.items
                                         if i.isChecked()]))
        errors = {}
        self.progressBar.setValue(0)
        qApp.processEvents()
        count = 1
        for pl_item in self._playlist.getItems():
            try:
                if pl_item.selected:
                    qApp.processEvents()
                    pl_item.actions.perform()
                    self.progressBar.setValue(count)
                    qApp.processEvents()
                    count += 1
            except Exception as e:
                errors[pl_item.name] = str(e)
        self.progressBar.hide()
        temp = ' shots ' if len(errors) > 1 else ' shot '
        if errors:
            detail = ''
            for shot in errors:
                detail += 'Shot: '+ shot +'\nReason: '+ errors[shot] +'\n\n'
            showMessage(self, title='Error', msg=str(len(errors))+temp+
                        'not exported successfully',
                        icon=QMessageBox.Critical, details=detail)
        self.exportButton.setEnabled(True)
        self.closeButton.setEnabled(True)

    def getPlaylist(self):
        return self._playlist
    playlist = property(getPlaylist)

    def closeEvent(self, event):
        self.deleteLater()

Form1, Base1 = uic.loadUiType(osp.join(ui_path, 'form.ui'))
class ShotForm(Form1, Base1):
    def __init__(self, parent=None, pl_item=None):
        super(ShotForm, self).__init__(parent)
        self.setupUi(self)
        self.parentWin = parent
        self.addCameras()
        self.pl_item = pl_item
        if self.pl_item:
            self.createButton.setText('Ok')
            self.populate()
        self.startFrame = None
        self.endFrame = None

        self.fillButton.setIcon(QIcon(osp.join(icon_path, 'ic_fill.png')))



        self.cameraBox.activated.connect(self.handleCameraBox)
        self.createButton.clicked.connect(self.create)
        self.keyFrameButton.clicked.connect(self.handleKeyFrameClick)
        self.browseButton.clicked.connect(self.browseFolder)
        self.fillButton.clicked.connect(self.fillName)
        
    def fillName(self):
        self.nameBox.setText(self.cameraBox.currentText())

    def browseFolder(self):
        path = self.pathBox.text()
        if not path:
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
        self.nameBox.setText(self.pl_item.name)
        camera = self.pl_item.camera
        for index in range(self.cameraBox.count()):
            if camera == str(self.cameraBox.itemText(index)):
                self.cameraBox.setCurrentIndex(index)
                break
        self.startFrameBox.setValue(self.pl_item.inFrame)
        self.endFrameBox.setValue(self.pl_item.outFrame)
        playblast = PlayblastExport.getActionFromList(self.pl_item.actions)
        self.pathBox.setText(playblast.path)

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
        name = str(self.nameBox.text())
        if not name:
            showMessage(self, msg='Shot name not specified')
            return
        camera = pc.PyNode(self.cameraBox.currentText())
        if self.keyFrameButton.isChecked():
            start = self.startFrame
            end = self.endFrame
        else:
            start = self.startFrameBox.value()
            end = self.endFrameBox.value()
        path = str(self.pathBox.text())
        if not path:
            showMessage(self,
                        msg='Path not specified', icon=QMessageBox.Warning)
            return
        if not osp.exists(path):
            showMessage(self, title='Error', msg='The system can not find '+
                        'the path specified', icon=QMessageBox.Information)
            return

        if self.pl_item: #update
            self.pl_item.name = name
            self.pl_item.camera = camera
            self.pl_item.inFrame = start
            self.pl_item.outFrame = end
            pb = PlayblastExport.getActionFromList(self.pl_item.actions)
            pb.path = path
            self.pl_item.saveToScene()
            self.parentWin.getItem(self.pl_item, True).update()
        else: # create New
            playlist = self.parentWin.playlist
            newItem = playlist.addNewItem(camera)
            newItem.name = name
            newItem.inFrame = start
            newItem.outFrame = end
            pb = PlayblastExport()
            pb.path = path
            newItem.actions.add(pb)
            newItem.saveToScene()
            self.parentWin.createItem(newItem)
        if self.pl_item:
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

    pl_item=None

    def __init__(self, parent=None, pl_item=None):
        super(Item, self).__init__(parent)
        self.pl_item = pl_item
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
        self.selectButton.clicked.connect(self.toggleSelected)
        self.deleteButton.clicked.connect(self.delete)
        self.browseButton.clicked.connect(self.openLocation)
        self.titleFrame.mouseReleaseEvent = self.collapse

    def update(self):
        if self.pl_item:
            self.setTitle(self.pl_item.name)
            self.setCamera(self.pl_item.camera.name())
            path = PlayblastExport.getActionFromList(
                    self.pl_item.actions).path
            self.setPath(path)
            self.setFrame("%d to %d"%(self.pl_item.inFrame,
                self.pl_item.outFrame))

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
        pb = PlayblastExport.getActionFromList(self.pl_item.actions)
        subprocess.call('explorer %s'%pb.path, shell=True)

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
        if self.pl_item:
            self.pl_item.selected = state
        self.selectButton.setChecked(state)

    def isChecked(self):
        return self.selectButton.isChecked()

    def toggleSelected(self):
        if self.pl_item:
            self.pl_item.selected = not self.pl_item.selected


    def toggleSelection(self):
        if self.pl_item:
            self.pl_item.selected = not self.selectButton.isChecked()
        self.selectButton.setChecked(not self.selectButton.isChecked())

    def mouseReleaseEvent(self, event):
        self.toggleSelection()
        self.clicked.emit()

    def edit(self):
        self.parentWin.editItem(self.pl_item)
        

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
