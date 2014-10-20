'''
Created on Sep 1, 2014

@author: Qurban Ali
'''
import site
site.addsitedir(r'R:\Pipe_Repo\Users\Qurban\utilities')
from uiContainer import uic
from PyQt4.QtGui import QIcon, QMessageBox, QFileDialog, qApp, QCheckBox
from PyQt4 import QtCore
import os.path as osp
import qtify_maya_window as qtfy
import pymel.core as pc
import re
import subprocess
import backend
import appUsageApp
reload(backend)

CacheExport = backend.CacheExport
exportutils = backend.exportutils
Playlist = backend.Playlist
PlayblastExport = backend.PlayblastExport
PlayListUtils = backend.PlayListUtils

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
        self.deleteSelectedButton.setIcon(QIcon(osp.join(icon_path, 'ic_delete.png')))
        search_ic_path = osp.join(icon_path, 'ic_search.png').replace('\\','/')
        style_sheet = ('\nbackground-image: url(%s);'+
                       '\nbackground-repeat: no-repeat;'+
                       '\nbackground-position: center left;')%search_ic_path
        style_sheet = self.searchBox.styleSheet() + style_sheet
        self.searchBox.setStyleSheet(style_sheet)

        self.collapseButton.clicked.connect(self.toggleCollapseAll)
        self.addButton.clicked.connect(self.showForm)
        self.selectAllButton.clicked.connect(self.selectAll)
        self.deleteSelectedButton.clicked.connect(self.deleteSelected)
        self.searchBox.textChanged.connect(self.searchShots)
        self.searchBox.returnPressed.connect(lambda: self.searchShots
                                             (str(self.searchBox.text())))
        self.exportButton.clicked.connect(self.export)

        # Populating Items
        self._playlist = Playlist()
        self.items = []
        self.populate()

        appUsageApp.updateDatabase('shot_subm')
        
    def setSelectedCount(self):
        count = 0
        for item in self.items:
            if item.isChecked():
                count += 1
        self.selectedLabel.setText('Selected: '+ str(count))
    
    def setTotalCount(self):
        self.totalLabel.setText('Total: '+ str(len(self.items)))

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
        self.setSelectedCount()
            
    def deleteSelected(self):
        flag = False
        for i in self.items:
            if i.isChecked():
                flag = True
                break
        if not flag:
            msg = 'Shots not selected'
            icon = QMessageBox.Information
            btns = QMessageBox.Ok
        else:
            msg = 'Are you sure, remove selected shots?'
            icon = QMessageBox.Question
            btns = QMessageBox.Yes|QMessageBox.Cancel

        btn = showMessage(self, title="Remove Selected",
                          msg=msg,
                          btns=btns,
                          icon=icon)
        if btn == QMessageBox.Yes:
            temp = []
            for item in self.items:
                if item.isChecked():
                    item.deleteLater()
                    self._playlist.removeItem(item.pl_item)
                    temp.append(item)
            for itm in temp:
                self.items.remove(itm)
        self.setSelectedCount()
        self.setTotalCount()

    def itemClicked(self):
        flag = True
        for item in self.items:
            if not item.isChecked():
                flag = False
                break
        self.selectAllButton.setChecked(flag)
        self.setSelectedCount()

    def showForm(self):
        ShotForm(self).show()

    def removeItem(self, item):
        self.items.remove(item)
        item.deleteLater()
        self._playlist.removeItem(item.pl_item)
        self.setSelectedCount()
        self.setTotalCount()

    def clear(self):
        for item in self.items:
            item.deleteLater()
            self._playlist.removeItem(item.pl_item)
        del self.items[:]
        self.setSelectedCount()
        self.setTotalCount()

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
        self.setSelectedCount()
        self.setTotalCount()
        return item

    def export(self):
        self.exportButton.setEnabled(False)
        self.closeButton.setEnabled(False)
        self.progressBar.show()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(len([i for i in self.items
                                         if i.isChecked()]))
        state = PlayListUtils.getDisplayLayersState()
        exportutils.setOriginalCamera()
        exportutils.setOriginalFrame()
        exportutils.setSelection()
        errors = {}
        self.progressBar.setValue(0)
        qApp.processEvents()
        count = 1
        for pl_item in self._playlist.getItems():
            #try:
            if pl_item.selected:
                qApp.processEvents()
                print 'actions:', pl_item.actions
                pl_item.actions.perform()
                self.progressBar.setValue(count)
                qApp.processEvents()
                count += 1
            #except Exception as e:
                #import traceback
                #errors[pl_item.name] = str(traceback.format_exc())
        self.progressBar.hide()
        temp = ' shots ' if len(errors) > 1 else ' shot '
        if errors:
            detail = ''
            for shot in errors:
                detail += 'Shot: '+ shot +'\nReason: '+ errors[shot] +'\n\n'
            showMessage(self, title='Error', msg=str(len(errors))+temp+
                        'not exported successfully',
                        icon=QMessageBox.Critical, details=detail)
        PlayListUtils.restoreDisplayLayersState(state)
        exportutils.restoreOriginalCamera()
        exportutils.restoreOriginalFrame()
        exportutils.restoreSelection()
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
        self.progressBar.hide()
        self.addCameras()
        self.pl_item = pl_item
        self.objectsSearchTerm = 'combined_mesh'
        self.layerButtons = []
        self.objectButtons = []
        self.addObjects()
        self.addLayers()
        if self.pl_item:
            self.createButton.setText('Ok')
            self.populate()
            self.autoCreateButton.hide()
        self.startFrame = None
        self.endFrame = None

        self.fillButton.setIcon(QIcon(osp.join(icon_path, 'ic_fill.png')))



        self.cameraBox.activated.connect(self.handleCameraBox)
        self.createButton.clicked.connect(self.callCreate)
        self.keyFrameButton.clicked.connect(self.handleKeyFrameClick)
        self.playblastBrowseButton.clicked.connect(self.playblastBrowseFolder)
        self.cacheBrowseButton.clicked.connect(self.cacheBrowseFolder)
        self.fillButton.clicked.connect(self.fillName)
        
    def addLayers(self):
        for layer in PlayListUtils.getDisplayLayers():
            btn = QCheckBox(layer.name(), self)
            btn.setChecked(layer.visibility.get())
            self.layerLayout.addWidget(btn)
            self.layerButtons.append(btn)
            
    def addObjects(self):
        for obj in exportutils.getObjects():
            btn = QCheckBox(obj, self)
            self.objectsLayout.addWidget(btn)
            self.objectButtons.append(btn)

    def fillName(self):
        self.nameBox.setText(self.cameraBox.currentText())
        
    def cacheBrowseFolder(self):
        path = self.browseFolder()
        if path:
            self.cachePathBox.setText(path)
            
    def playblastBrowseFolder(self):
        path = self.browseFolder()
        if path:
            self.playblastPathBox.setText(path)

    def browseFolder(self):
        path = self.parentWin._previousPath
        if not path: path = ''
        path = QFileDialog.getExistingDirectory(self, 'Select Folder',
                path, QFileDialog.ShowDirsOnly)
        if path:
            self.parentWin._previousPath = path
        return path

    def handleCameraBox(self, camera):
        camera = str(camera)
        if self.keyFrameButton.isChecked():
            self.startFrame, self.endFrame = self.getKeyFrame()
            self.startFrameBox.setValue(self.startFrame)
            self.endFrameBox.setValue(self.endFrame)

    def addCameras(self):
        cams = pc.ls(type='camera')
        names = [cam.firstParent().name() for cam in cams
                 if cam.orthographic.get() == False]
        self.cameraBox.addItems(names)
        self.cameraBox.view().setFixedWidth(self.cameraBox.sizeHint().width())
        self.camCountLabel.setText(str(len(names)))

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
        self.playblastPathBox.setText(playblast.path)
        for layer in self.layerButtons:
            if str(layer.text()) in playblast.getLayers():
                layer.setChecked(True)
            else: layer.setChecked(False)
        self.playblastEnableButton.setChecked(playblast.enabled)
        cacheAction = CacheExport.getActionFromList(self.pl_item.actions)
        for btn in self.objectButtons:
            if str(btn.text()) in cacheAction.objects:
                btn.setChecked(True)
        self.cacheEnableButton.setChecked(cacheAction.enabled)
        self.cachePathBox.setText(cacheAction.path)

    def getKeyFrame(self, camera=None):
        if camera == None:
            camera = pc.PyNode(str(self.cameraBox.currentText()))
        animCurves = pc.listConnections(camera, scn=True,
                                        d=False, s=True)
        if not animCurves:
            showMessage(self,
                        msg='No in out found on \"'+camera.name()+"\"",
                        icon=QMessageBox.Warning)
            self.keyFrameButton.setChecked(False)
            return 0, 1

        frames = pc.keyframe(animCurves[0], q=True)
        if not frames:
            showMessage(self, msg='No in out found on \"'+camera.name()+"\"",
                        icon=QMessageBox.Warning)
            self.keyFrameButton.setChecked(False)
            return 0, 1

        return frames[0], frames[-1]

    def handleKeyFrameClick(self):
        if self.keyFrameButton.isChecked():
            self.startFrame, self.endFrame = self.getKeyFrame()
            self.startFrameBox.setValue(self.startFrame)
            self.endFrameBox.setValue(self.endFrame)
            
    def callCreate(self):
        playblastPath = str(self.playblastPathBox.text())
        cachePath = str(self.cachePathBox.text())
        if not self.playblastEnableButton.isChecked() and not self.cacheEnableButton.isChecked():
            showMessage(self, title='Shot Export', msg='No action is enabled, enable at least one',
                        icon=QMessageBox.Warning)
            return
        
        if self.playblastEnableButton.isChecked():
            if not playblastPath:
                showMessage(self,
                            msg='Playblast Path not specified', icon=QMessageBox.Warning)
                return
            if not osp.exists(playblastPath):
                showMessage(self, title='Error', msg='Playblast path does not '+
                            'exist', icon=QMessageBox.Information)
                return
#             if not [layer for layer in self.layerButtons if layer.isChecked()]:
#                 showMessage(self, title='Shot Export', msg='No layer enabled, enable'+
#                             ' at least one')
#                 return
        if self.cacheEnableButton.isChecked():
            if not cachePath:
                showMessage(self,
                            msg='Cache Path not specified', icon=QMessageBox.Warning)
                return
            if not osp.exists(cachePath):
                showMessage(self, title='Error', msg='Cache path does not '+
                            'exist', icon=QMessageBox.Information)
                return
            if not [obj for obj in self.objectButtons if obj.isChecked()]:
                showMessage(self, title='Shot Export', msg='No object selected, '+
                            'select at least one')
                return
        if self.autoCreateButton.isChecked():
            self.createAll(playblastPath, cachePath)
        else:
            name = str(self.nameBox.text())
            if not name:
                showMessage(self, msg='Shot name not specified')
                return
            camera = pc.PyNode(str(self.cameraBox.currentText()))
            if self.keyFrameButton.isChecked():
                start = self.startFrame
                end = self.endFrame
            else:
                start = self.startFrameBox.value()
                end = self.endFrameBox.value()
            self.create(name, camera, start, end, playblastPath, cachePath)
            
    def getSelectedLayers(self):
        return [str(layer.text()) for layer in self.layerButtons
                if layer.isChecked()]
        
    def createAll(self, playblastPath, cachePath):
        _max = self.cameraBox.count()
        self.progressBar.setMaximum(_max)
        self.progressBar.show()
        for i in range(_max):
            name = str(self.cameraBox.itemText(i))
            cam = pc.PyNode(name)
            start, end = self.getKeyFrame(cam)
            self.create(name, cam, start, end, playblastPath, cachePath)
            self.progressBar.setValue(i+1)
            qApp.processEvents()
        self.progressBar.hide()
        self.progressBar.setValue(0)
        self.accept()

    def getSelectedObjects(self):
        objs = []
        for obj in self.objectButtons:
            if obj.isChecked():
                objs.append(str(obj.text()))
        return objs

    def create(self, name, camera, start, end, playblastPath, cachePath):
        if self.pl_item: #update
            self.pl_item.name = name
            self.pl_item.camera = camera
            self.pl_item.inFrame = start
            self.pl_item.outFrame = end
            
            pb = PlayblastExport.getActionFromList(self.pl_item.actions)
            pb.enabled = self.playblastEnableButton.isChecked()
            pb.path = playblastPath
            pb.addLayers(self.getSelectedLayers())
            
            ce = CacheExport.getActionFromList(self.pl_item.actions)
            ce.enabled = self.cacheEnableButton.isChecked()
            ce.path = cachePath
            ce.addObjects(self.getSelectedObjects())
            
            self.pl_item.saveToScene()
            self.parentWin.getItem(self.pl_item, True).update()
            self.accept()
        else: # create New
            if not PlayListUtils.getAttrs(camera):
                playlist = self.parentWin.playlist
                newItem = playlist.addNewItem(camera)
                newItem.name = name
                newItem.inFrame = start
                newItem.outFrame = end
                
                pb = PlayblastExport()
                pb.enabled = self.playblastEnableButton.isChecked()
                pb.addLayers(self.getSelectedLayers())
                pb.path = playblastPath
                
                ce = CacheExport()
                ce.enabled = self.cacheEnableButton.isChecked()
                ce.addObjects(self.getSelectedObjects())
                ce.path = cachePath
                
                newItem.actions.add(pb)
                newItem.actions.add(ce)
                newItem.saveToScene()
                self.parentWin.createItem(newItem)

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
            playblastPath = PlayblastExport.getActionFromList(
                    self.pl_item.actions).path
            self.setPlayblastPath(playblastPath)
            self.setCachePath(CacheExport.getActionFromList(self.pl_item.actions
                                                            ).path)
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

    def setPlayblastPath(self, path):
        self.playblastPathLabel.setText(path)

    def getPlayblastPath(self):
        return str(self.playblastPathLabel.text())
    
    def setCachePath(self, path):
        self.cachePathLabel.setText(path)
        
    def getCachePath(self):
        return str(self.cachePathLabel.text())

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
        mBox.closeEvent = lambda event: mBox.deleteLater()
        buttonPressed = mBox.exec_()
        return buttonPressed
