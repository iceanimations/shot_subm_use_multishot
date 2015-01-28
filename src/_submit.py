'''
Created on Sep 1, 2014

@author: Qurban Ali
'''
from uiContainer import uic
from PyQt4.QtGui import QIcon, QMessageBox, QFileDialog, qApp, QCheckBox
from PyQt4 import QtCore
import os
import os.path as osp
import shutil
import qtify_maya_window as qtfy
import pymel.core as pc
import re
import subprocess
import backend
import appUsageApp
reload(backend)
import msgBox

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

        self.__colors_mapping__ = {'Red': 4, 'Green': 14, 'Yellow': 17,
                                   'Black': 1}

        self.progressBar.hide()

        self.collapsed = False
        self.breakdownWindow = None
        
        self.addButton.setIcon(QIcon(osp.join(icon_path, 'ic_add.png')))
        self.collapseButton.setIcon(QIcon(osp.join(icon_path,
                                                   'ic_toggle_collapse')))
        self.deleteSelectedButton.setIcon(QIcon(osp.join(icon_path, 'ic_delete.png')))
        self.sceneBreakdownButton.setIcon(QIcon(osp.join(icon_path, 'ic_update.png')))
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
        self.browseButton.clicked.connect(self.browseFolder)
        self.cacheEnableAction.triggered.connect(self.enableCacheSelected)
        self.cacheDisableAction.triggered.connect(self.disableCacheSelected)
        self.playblastEnableAction.triggered.connect(self.enablePlayblastSelected)
        self.playblastDisableAction.triggered.connect(self.disablePlayblastSelected)
        self.sceneBreakdownButton.clicked.connect(self.sceneBreakdown)

        # Populating Items
        self._playlist = Playlist()
        self.items = []
        self.populate()

        appUsageApp.updateDatabase('shot_subm')
        
    def sceneBreakdown(self):
        if self.breakdownWindow:
            self.breakdownWindow.activateWindow()
            return
        # get the user
        import login
        import auth.user as user
    
        if not user.user_registered():
            if not login.Dialog().exec_():
                return
    
        import breakdown
        self.breakdownWindow =  breakdown.Breakdown(self)
        self.breakdownWindow.show()
        self.breakdownWindow.closeEvent = self.breakdownCloseEvent
        
    def breakdownCloseEvent(self, event):
        self.breakdownWindow.thread.terminate()
        self.breakdownWindow.deleteLater()
        self.breakdownWindow = None
        
    def enableCacheSelected(self):
        for item in self._playlist.getItems():
            if item.selected:
                CacheExport.getActionFromList(item.actions).enabled = True
                item.saveToScene()
    
    def disableCacheSelected(self):
        for item in self._playlist.getItems():
            if item.selected:
                CacheExport.getActionFromList(item.actions).enabled = False
                item.saveToScene()
    
    def enablePlayblastSelected(self):
        for item in self._playlist.getItems():
            if item.selected:
                PlayblastExport.getActionFromList(item.actions).enabled = True
                item.saveToScene()
    
    def disablePlayblastSelected(self):
        for item in self._playlist.getItems():
            if item.selected:
                PlayblastExport.getActionFromList(item.actions).enabled = False
                item.saveToScene()
        
    def browseFolder(self):
        path = QFileDialog.getExistingDirectory(self, 'Select Folder', '')
        if path:
            self.pathBox.setText(path)
        
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

        btn = msgBox.showMessage(self, title="Remove Selected",
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

    def setHUDColor(self):
        #color = str(self.colorBox.currentText())
        #if color and color != 'Default':
        color = 'Green'
        exportutils.setHUDColor(self.__colors_mapping__.get(color),
                                self.__colors_mapping__.get(color))
        
    def isItemSelected(self):
        selected = False
        for item in self._playlist.getItems():
            if item.selected:
                selected = True
                break
        return selected
        
    def isActionEnabled(self):
        shots = []
        for item in self.playlist.getItems():
            if item.selected:
                enabled = False
                for action in item.actions.getActions():
                    if action.enabled:
                        enabled = True
                        break
                if not enabled:
                    shots.append(item.name)
        return shots
    
    def allPathsExist(self):
        shots = {}
        for item in self.playlist.getItems():
            if item.selected:
                for action in item.actions.getActions():
                    if action.enabled:
                        if not osp.exists(action.path):
                            if shots.has_key(item.name):
                                shots[item.name].append(action.path)
                            else:
                                shots[item.name] = [action.path]
        return shots

    def export(self):
        # check if at least one item is selected
        if not self.isItemSelected():
            msgBox.showMessage(self, title='No selection',
                        msg='No shot selected to export',
                        icon=QMessageBox.Information)
            return
        # check if at least one action is enaled for all selected items
        badShots = self.isActionEnabled()
        if badShots:
            numShots = len(badShots)
            s = 's' if numShots > 1 else ''
            detail = ''
            for i, shot in enumerate(badShots):
                detail += str(i+1) +' - '+ shot + '\n\n'
            msgBox.showMessage(self, title='No Action',
                        msg=str(numShots) +' shot'+ s +' selected, but no action enabled',
                        details = detail,
                        icon=QMessageBox.Information)
            return
        # check if paths for playblast and cache exist for all selected items
        badShots = self.allPathsExist()
        if badShots:
            numShots = len(badShots)
            s = 's' if numShots > 1 else ''
            detail = ''
            for shot, paths in badShots.items():
                detail += shot +'\n'
                for path in paths:
                    detail += path +'\n'
                detail += '\n'
            msgBox.showMessage(self, title='Path not found',
                        msg=str(numShots) +' shot'+ s +' selected, but no path found',
                        details = detail,
                        icon=QMessageBox.Information)
            return
        # checks for audio node and file
        audioNodes = exportutils.getAudioNodes()
        if not audioNodes:
            btn = msgBox.showMessage(self, title='No Audio',
                                     msg='No audio found in the scene',
                                     ques='Do you want to proceed anyway?',
                                     icon=QMessageBox.Question,
                                     btns=QMessageBox.Yes|QMessageBox.No)
            if btn == QMessageBox.No:
                return
        if len(audioNodes) > 1:
            msgBox.showMessage(self, title='Audio Files',
                                msg='More than one audio files found in the scene, '+
                                'keep only one audio file',
                                icon=QMessageBox.Information)
            return
        
        try:
            for directory in os.listdir(exportutils.home):
                    shutil.rmtree(osp.join(exportutils.home, directory))
        except Exception, ex:
            pass
        try:
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
            exportutils.saveHUDColor()
            exportutils.hideShowCurves(True)
            exportutils.hideFaceUi()
            self.setHUDColor()
            backend.playblast.showNameLabel()
            errors = {}
            self.progressBar.setValue(0)
            qApp.processEvents()
            count = 1
            for pl_item in self._playlist.getItems():
                try:
                    if pl_item.selected:
                        qApp.processEvents()
                        pl_item.actions.perform(sound=self.audioButton.isChecked(),
                                                hd=self.hdButton.isChecked())
                        self.progressBar.setValue(count)
                        qApp.processEvents()
                        count += 1
                except Exception as ex:
                    errors[pl_item.name] = str(ex)
            temp = ' shots ' if len(errors) > 1 else ' shot '
            if errors:
                detail = ''
                for shot in errors:
                    detail += 'Shot: '+ shot +'\nReason: '+ errors[shot] +'\n\n'
                msgBox.showMessage(self, title='Error', msg=str(len(errors))+temp+
                            'not exported successfully',
                            icon=QMessageBox.Critical, details=detail)
        except Exception as ex:
            msgBox.showMessage(self, title='Error', msg=str(ex),
                        icon=QMessageBox.Critical)
        finally:
            self.progressBar.hide()
            PlayListUtils.restoreDisplayLayersState(state)
            exportutils.restoreOriginalCamera()
            exportutils.restoreOriginalFrame()
            exportutils.restoreSelection()
            exportutils.restoreHUDColor()
            exportutils.hideShowCurves(False)
            exportutils.showFaceUi()
            backend.playblast.removeNameLabel()
            self.exportButton.setEnabled(True)
            self.closeButton.setEnabled(True)

        if exportutils.errorsList:
            detail = ''
            for error in exportutils.errorsList:
                detail += error +'\n\n'
            msgBox.showMessage(self, title='Error',
                        msg='Unable to copy files to destination\n'+
                        'your files copied to: '+ exportutils.home,
                        details=detail,
                        icon=QMessageBox.Warning)
            exportutils.errorsList[:] = []

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
        
        self.startFrame = None
        self.endFrame = None
        self.pl_item = pl_item
        self.layerButtons = []
        self.objectButtons = []
        self.cameraButtons = []
        
        self.addCameras()
        self.addObjects()
        self.addLayers()
        
        if self.pl_item:
            self.createButton.setText('Ok')
            self.populate()
            self.autoCreateButton.setChecked(False)
            self.stackedWidget.setCurrentIndex(0)
            self.autoCreateButton.hide()
        else:
            self.fillPathBoxes()

        self.fillButton.setIcon(QIcon(osp.join(icon_path, 'ic_fill.png')))


        self.cameraBox.activated.connect(self.handleCameraBox)
        self.createButton.clicked.connect(self.callCreate)
        self.keyFrameButton.clicked.connect(self.handleKeyFrameClick)
        self.playblastBrowseButton.clicked.connect(self.playblastBrowseFolder)
        self.cacheBrowseButton.clicked.connect(self.cacheBrowseFolder)
        self.fillButton.clicked.connect(self.fillName)
        self.selectAllButton.clicked.connect(self.selectAll)
        self.selectAllButton2.clicked.connect(self.selectAll2)
        self.selectAllButton3.clicked.connect(self.handleSelectAllButton3)
        self.autoCreateButton.toggled.connect(self.switchStackedWidget)
        
    def switchStackedWidget(self, stat):
        self.stackedWidget.setCurrentIndex(int(stat))
        
    def selectAll(self):
        checked = self.selectAllButton.isChecked()
        for btn in self.layerButtons:
            btn.setChecked(checked)
            
    def selectAll2(self):
        checked = self.selectAllButton2.isChecked()
        for btn in self.objectButtons:
            btn.setChecked(checked)
            
    def setSelectAllButton(self):
        flag = True
        for btn in self.layerButtons:
            if not btn.isChecked():
                flag = False
                break
        self.selectAllButton.setChecked(flag)
        
    def setSelectAllButton2(self):
        flag = True
        for btn in self.objectButtons:
            if not btn.isChecked():
                flag = False
                break
        self.selectAllButton2.setChecked(flag)
        
    def fillPathBoxes(self):
        path1 = self.getPlayblastPath(self.getCurrentCameraName())
        if osp.exists(path1): 
            self.playblastPathBox.setText(path1)
        path2 = self.getCachePath(self.getCurrentCameraName())
        if osp.exists(path2):
            self.cachePathBox.setText(path2)
        
    def addLayers(self):
        for layer in PlayListUtils.getDisplayLayers():
            btn = QCheckBox(layer.name(), self)
            btn.setChecked(layer.visibility.get())
            self.layerLayout.addWidget(btn)
            self.layerButtons.append(btn)
        self.setSelectAllButton()
        map(lambda btn: btn.clicked.connect(self.setSelectAllButton), self.layerButtons)
            
    def addObjects(self):
        for obj in exportutils.getObjects():
            btn = QCheckBox(obj, self)
            self.objectsLayout.addWidget(btn)
            self.objectButtons.append(btn)
        map(lambda btn: btn.clicked.connect(self.setSelectAllButton2), self.objectButtons)
            
    def getCurrentCameraName(self):
        return self.cameraBox.currentText().replace(':', '_').replace('|', '_')

    def fillName(self):
        self.nameBox.setText(self.getCurrentCameraName())
        
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
        path = QFileDialog.getExistingDirectory(self, 'Select Folder', path)
        if path:
            self.parentWin._previousPath = path
        return path

    def handleCameraBox(self, camera):
        camera = str(camera) # camera index in combobox
        if self.keyFrameButton.isChecked():
            self.startFrame, self.endFrame = self.getKeyFrame()
            self.startFrameBox.setValue(self.startFrame)
            self.endFrameBox.setValue(self.endFrame)
        self.fillPathBoxes()

    def addCameras(self):
        cams = pc.ls(type='camera')
        names = [cam.firstParent().name() for cam in cams
                 if cam.orthographic.get() == False]
        #names.remove('persp')
        self.cameraBox.addItems(names)
        #self.cameraBox.view().setFixedWidth(self.cameraBox.minimumSizeHint().width())
        self.camCountLabel.setText(str(len(names)))
        self.addCamerasToStackedWidget(names)
        
    def handleSelectAllButton3(self):
        for btn in self.cameraButtons:
            btn.setChecked(self.selectAllButton3.isChecked())
    
    def toggleSelectedAllButton3(self):
        flag = True
        for btn in self.cameraButtons:
            if not btn.isChecked():
                flag = False
                break
        self.selectAllButton3.setChecked(flag)
        
    def addCamerasToStackedWidget(self, names):
        for name in names:
            btn = QCheckBox(name, self)
            btn.clicked.connect(self.toggleSelectedAllButton3)
            btn.setChecked(True)
            self.cameraLayout.addWidget(btn)
            self.cameraButtons.append(btn)
    
    def getSelectedCameras(self):
        return [btn.text() for btn in self.cameraButtons if btn.isChecked()]

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
            msgBox.showMessage(self,
                        msg='No in out found on \"'+camera.name()+"\"",
                        icon=QMessageBox.Warning)
            self.keyFrameButton.setChecked(False)
            return 0, 1

        frames = pc.keyframe(animCurves[0], q=True)
        if not frames:
            msgBox.showMessage(self, msg='No in out found on \"'+camera.name()+"\"",
                        icon=QMessageBox.Warning)
            self.keyFrameButton.setChecked(False)
            return 0, 1

        return frames[0], frames[-1]

    def handleKeyFrameClick(self):
        if self.keyFrameButton.isChecked():
            self.startFrame, self.endFrame = self.getKeyFrame()
            self.startFrameBox.setValue(self.startFrame)
            self.endFrameBox.setValue(self.endFrame)
            
    def autoCreate(self):
        return self.autoCreateButton.isChecked()
            
    def callCreate(self):
        playblastPath = str(self.playblastPathBox.text())
        cachePath = str(self.cachePathBox.text())
        
        if self.playblastEnableButton.isChecked():
            if not self.autoCreate():
                if not playblastPath:
                    msgBox.showMessage(self,
                                msg='Playblast Path not specified', icon=QMessageBox.Warning)
                    return
                if not osp.exists(playblastPath):
                    msgBox.showMessage(self, title='Error', msg='Playblast path does not '+
                                'exist', icon=QMessageBox.Information)
                    return

        if self.cacheEnableButton.isChecked():
            if not self.autoCreate():
                if not cachePath:
                    msgBox.showMessage(self,
                                msg='Cache Path not specified', icon=QMessageBox.Warning)
                    return
                if not osp.exists(cachePath):
                    msgBox.showMessage(self, title='Error', msg='Cache path does not '+
                                'exist', icon=QMessageBox.Information)
                    return
            if not [obj for obj in self.objectButtons if obj.isChecked()]:
                msgBox.showMessage(self, title='Shot Export', msg='No object selected '+
                            'for cache, select at least one or uncheck the '+
                            '\"Enable\" button')
                return
        if self.autoCreateButton.isChecked():
            self.createAll(playblastPath, cachePath)
        else:
            name = str(self.nameBox.text())
            if not name:
                msgBox.showMessage(self, msg='Shot name not specified')
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
        prefixPath = self.getSeqPath()
        if not osp.exists(prefixPath):
            msgBox.showMessage(self, title='Error', msg='Sequence path does not exist',
                        icon=QMessageBox.Information)
            self.progressBar.hide()
            return
        cams = self.getSelectedCameras()
        if not cams:
            msgBox.showMessage(self, title='Shot Export',
                        msg='No camera selected',
                        icon=QMessageBox.Information)
            self.progressBar.hide()
            return
        _max = len(cams)
        self.progressBar.setMaximum(_max)
        self.progressBar.show()
        for i, name in enumerate(cams):
            pathName = name.split(':')[-1].split('|')[-1]
            cam = pc.PyNode(name)
            start, end = self.getKeyFrame(cam)
            playblastPath = self.getPlayblastPath(pathName)
            cachePath = self.getCachePath(pathName)
            self.create(name, cam, start, end, playblastPath, cachePath)
            self.progressBar.setValue(i+1)
            qApp.processEvents()
        self.progressBar.hide()
        self.progressBar.setValue(0)
        self.accept()
        
    def getSeqPath(self):
        return str(self.parentWin.pathBox.text())
        
    def getBasePath(self, cameraName):
        prefix = self.getSeqPath()
        prefixPath = osp.join(prefix, 'SHOTS')
        shotPath = osp.join(prefixPath, str(cameraName))
        return osp.join(shotPath, 'animation')
        
    def getCachePath(self, cameraName):
        animPath = self.getBasePath(cameraName)
        return osp.join(animPath, 'cache')
        
    def getPlayblastPath(self, cameraName):
        animPath = self.getBasePath(cameraName)
        return osp.join(animPath, 'preview')

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
                if playblastPath:
                    pb.path = playblastPath
                
                ce = CacheExport()
                ce.enabled = self.cacheEnableButton.isChecked()
                ce.addObjects(self.getSelectedObjects())
                if cachePath:
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
    #if version == 2014:
    clicked = QtCore.pyqtSignal()
    #else:
    #clicked = QtCore.Signal()

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
        self.titleFrame.mouseReleaseEvent = self.collapse
        
        self.label.mouseDoubleClickEvent = lambda event: self.openLocation()
        self.label_2.mouseDoubleClickEvent = lambda event: self.openLocation2()
        self.playblastPathLabel.mouseDoubleClickEvent = lambda event: self.openLocation()
        self.cachePathLabel.mouseDoubleClickEvent = lambda event: self.openLocation2()

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
        if not osp.exists(pb.path):
            msgBox.showMessage(self.parentWin, title='Path Error',
                        msg='Path does not exist',
                        icon=QMessageBox.Information)
            return
        subprocess.call('explorer %s'%pb.path, shell=True)

    def openLocation2(self):
        ce = CacheExport.getActionFromList(self.pl_item.actions)
        if not osp.exists(ce.path):
            msgBox.showMessage(self.parentWin, title='Path Error',
                        msg='Path does not exist',
                        icon=QMessageBox.Information)
            return
        subprocess.call('explorer %s'%ce.path, shell=True)

    def delete(self):
        btn = msgBox.showMessage(self, title='Delete Shot', msg='Are you sure, delete '
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