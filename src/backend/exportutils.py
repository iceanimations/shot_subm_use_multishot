'''
Created on Oct 14, 2014

@author: qurban.ali
'''
import pymel.core as pc
import os
osp = os.path
import shutil
import time
import qutil

errorsList = []

__original_camera__ = None
__original_frame__ = None
__selection__ = None
__resolutionGate__ = True
__safeAction__ = True
__safeTitle__ = True
__resolutionGateMask__ = True
__hud_frame_1__ = '__hud_frame_1__'
__hud_frame_2__ = '__hud_frame_2__'
__labelColor__ = None
__valueColor__ = None

__fps_mapping__ = {
                   'game': '15 fps', 'film': 'Film (24 fps)',
                   'pal': 'PAL (25 fps)', 'ntsc': 'NTSC (30 fps)',
                   'show': 'Show 48 fps', 'palf': 'PAL Field 50 fps',
                   'ntscf': 'NTSC Field 60 fps', 'millisec': 'milliseconds',
                   'sec': 'seconds', 'min': 'minutes', 'hour': 'hours'
                   }

home = osp.join(osp.expanduser('~'), 'temp_shots_export')
if not osp.exists(home):
    os.mkdir(home)
    
def isConnected(_set):
    return pc.PyNode(_set).hasAttr('forCache') and pc.PyNode(_set).forCache.outputs()
    
def isCompatible(_set):
    try:
        return pc.polyEvaluate(_set, f=True) == pc.PyNode(_set).forCache.outputs()[0]
    except Exception, ex:
        pc.warning(str(ex))
        return True
    
def removeFile(path):
    try:
        os.remove(path)
    except Exception as ex:
        pc.warning(ex)

def copyFile(src, des):
    src = osp.normpath(src)
    des = osp.normpath(des)
    try:
        existingFile = osp.join(des, osp.basename(src))
        if osp.exists(existingFile):
            print 'removing %s...'%existingFile
            os.remove(existingFile)
            print 'removed...'
        shutil.copy(src, des)
    except Exception as ex:
        try:
            basename3 = qutil.basename3(des)
            tempPath = osp.join(home, basename3)
            if not osp.exists(tempPath):
                qutil.mkdir(home, basename3)
            tempPath2 = osp.join(tempPath, osp.basename(src))
            if osp.exists(tempPath2):
                os.remove(tempPath2)
            shutil.copy(src, tempPath)
        except Exception, ex2:
            pc.warning(ex2)
        errorsList.append(str(ex))
    finally:
        os.remove(src)

def hideFaceUi():
    sel = pc.ls(sl=True)
    pc.select(pc.ls(regex='(?i).*:?UI_grp'))
    pc.Mel.eval('HideSelectedObjects')
    pc.select(sel)
    
def showFaceUi():
    sel = pc.ls(sl=True)
    pc.select(pc.ls(regex='(?i).*:?UI_grp'))
    pc.showHidden(b=True)
    pc.select(sel)

def getDefaultResolution():
    node = pc.ls('defaultResolution')[0]
    return node.width.get(), node.height.get()

def saveHUDColor():
    global __labelColor__
    __labelColor__ = pc.general.displayColor('headsUpDisplayLabels', dormant=True, q=True)
    global __valueColor__
    __valueColor__ = pc.general.displayColor('headsUpDisplayValues', dormant=True, q=True)
    
def restoreHUDColor():
    if __labelColor__ and __valueColor__:
        setHUDColor(__labelColor__, __valueColor__)
    
def setHUDColor(color1, color2):
    try:
        pc.general.displayColor('headsUpDisplayLabels', color1, dormant=True)
    except: pass
    try:
        pc.general.displayColor('headsUpDisplayValues', color2, dormant=True)
    except: pass

def getFrameRate():
    global __fps_mapping__
    unit = pc.general.currentUnit(q=True, time=True)
    fps = __fps_mapping__.get(unit)
    return fps if fps else unit

def showFrameInfo(pl_item):
    fps = getFrameRate()
    inOut = str(pl_item.inFrame) +' - '+ str(pl_item.outFrame)
    def getFps():
        return fps
    def getInOut():
        return inOut
    removeFrameInfo()
    pc.headsUpDisplay(__hud_frame_1__, lfs='large', label='FPS:', section=6, block=pc.headsUpDisplay(nfb=6), blockSize='large', dfs='large', command=getFps)
    pc.headsUpDisplay(__hud_frame_2__, lfs='large', label='IN OUT:', section=6, block=pc.headsUpDisplay(nfb=6), blockSize='large', dfs='large', command=getInOut)
    pc.Mel.eval('setCurrentFrameVisibility(1)')
    pc.headsUpDisplay('HUDCurrentFrame', e=True, lfs='large', dfs='large', bs='large')
    pc.Mel.eval('setFocalLengthVisibility(1)')
    pc.headsUpDisplay('HUDFocalLength', e=True, lfs='large', dfs='large', bs='large')
    pc.Mel.eval('setCameraNamesVisibility(1)')
    pc.headsUpDisplay('HUDCameraNames', e=True, lfs='large', dfs='large', bs='large')
    
def removeFrameInfo():
    if pc.headsUpDisplay(__hud_frame_1__, exists=True):
        pc.headsUpDisplay(__hud_frame_1__, rem=True)
    if pc.headsUpDisplay(__hud_frame_2__, exists=True):
        pc.headsUpDisplay(__hud_frame_2__, rem=True)
    pc.Mel.eval('setCurrentFrameVisibility(`optionVar -q currentFrameVisibility`)')
    pc.Mel.eval('setFocalLengthVisibility(`optionVar -q focalLengthVisibility`)')
    pc.Mel.eval('setCameraNamesVisibility(`optionVar -q focalLengthVisibility`)')

def turnResolutionGateOn(camera):
    oscan = 1.4
    global __resolutionGate__
    global __safeAction__
    global __safeTitle__
    global __resolutionGateMask__
    if not pc.camera(camera, q=True, displayResolution=True):
        __resolutionGate__ = False
        pc.camera(camera, e=True, displayResolution=True, overscan=oscan)
    if pc.camera(camera, q=True, displaySafeAction=True):
        __safeAction__ = False
        pc.camera(camera, e=True, displaySafeAction=False, overscan=oscan)
    if pc.camera(camera, q=True, displaySafeTitle=True):
        __safeTitle__ = False
        pc.camera(camera, e=True, displaySafeTitle=False, overscan=oscan)
    if not pc.camera(camera, q=True, dgm=True):
        __resolutionGateMask__ = False
        pc.camera(camera, e=True, dgm=True, overscan=oscan)

def turnResolutionGateOff(camera):
    global __resolutionGate__
    global __safeAction__
    global __safeTitle__
    global __resolutionGateMask__
    if not __resolutionGate__:
        pc.camera(camera, e=True, displayResolution=False, overscan=1.0)
        __resolutionGate__ = True
    if not __safeAction__:
        pc.camera(camera, e=True, displaySafeAction=True, overscan=1.0)
        __safeAction__ = True
    if not __safeTitle__:
        pc.camera(camera, e=True, displaySafeTitle=True, overscan=1.0)
        __safeTitle__ = True
    if not __resolutionGateMask__:
        pc.camera(camera, e=True, dgm=False, overscan=1.0)
        
def hideShowCurves(flag):
    sel = pc.ls(sl=True)
    try:
        if flag:
            pc.select(pc.ls(type=pc.nt.NurbsCurve))
            pc.Mel.eval('HideSelectedObjects')
        else:
            pc.select(pc.ls(type=pc.nt.NurbsCurve))
            pc.showHidden(b=True)
    except: pass
    pc.select(sel)
    
def getAudioNode():
    nodes = pc.ls(type=['audio'])
    return nodes if nodes else []

def setOriginalCamera():
    global __original_camera__
    __original_camera__ = pc.lookThru(q=True)
    
def restoreOriginalCamera():
    global __original_camera__
    pc.lookThru(__original_camera__)
    __original_camera__ = None
    
def setOriginalFrame():
    global __original_frame__
    __original_frame__ = pc.currentTime(q=True)
    
def restoreOriginalFrame():
    global __original_frame__
    pc.currentTime(__original_frame__)
    __original_frame__ = None
    
def setSelection():
    global __selection__
    __selection__ = pc.ls(sl=True)
    
def restoreSelection():
    global __selection__
    pc.select(__selection__)
    __selection__ = None
    
def getObjects():
    objSets = []
    for _set in pc.ls(type=pc.nt.ObjectSet):
        if 'geo_set' in str(_set).lower():
            objSets.append(_set.name())
    return objSets
