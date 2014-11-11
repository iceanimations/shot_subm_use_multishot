'''
Created on Oct 14, 2014

@author: qurban.ali
'''
import pymel.core as pc
import os
osp = os.path
import shutil
import time

__original_camera__ = None
__original_frame__ = None
__selection__ = None
__resolutionGate__ = False
__safeAction__ = False
__safeTitle__ = False
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

def copyFile(src, des):
    src = src.replace('/', '\\\\')
    try:
        existingFile = osp.join(des, osp.basename(src))
        if osp.exists(existingFile):
            print 'removing %s...'%existingFile
            os.remove(existingFile)
        shutil.copy(src, des)
    except Exception as ex:
        pc.warning(str(ex))
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
    pc.headsUpDisplay(__hud_frame_2__, lfs='large', label='In Out:', section=6, block=pc.headsUpDisplay(nfb=6), blockSize='large', dfs='large', command=getInOut)
    pc.Mel.eval('setCurrentFrameVisibility(1)')
    pc.headsUpDisplay('HUDCurrentFrame', e=True, lfs='large', dfs='large')
    pc.Mel.eval('setFocalLengthVisibility(1)')
    pc.headsUpDisplay('HUDFocalLength', e=True, lfs='large', dfs='large')
    pc.Mel.eval('setCameraNamesVisibility(1)')
    pc.headsUpDisplay('HUDCameraNames', e=True, lfs='large', dfs='large')
    
def removeFrameInfo():
    if pc.headsUpDisplay(__hud_frame_1__, exists=True):
        pc.headsUpDisplay(__hud_frame_1__, rem=True)
    if pc.headsUpDisplay(__hud_frame_2__, exists=True):
        pc.headsUpDisplay(__hud_frame_2__, rem=True)
    pc.Mel.eval('setCurrentFrameVisibility(`optionVar -q currentFrameVisibility`)')
    pc.Mel.eval('setFocalLengthVisibility(`optionVar -q focalLengthVisibility`)')
    pc.Mel.eval('setCameraNamesVisibility(`optionVar -q focalLengthVisibility`)')

def turnResolutionGateOff(camera):
    global __resolutionGate__
    global __safeAction__
    global __safeTitle__
    if pc.camera(camera, q=True, displayResolution=True):
        __resolutionGate__ = True
    if pc.camera(camera, q=True, displaySafeAction=True):
        __safeAction__ = True
    if pc.camera(camera, q=True, displaySafeTitle=True):
        __safeTitle__ = True
    pc.camera(camera, e=True, displayResolution=False, overscan=1.0)
    pc.camera(camera, e=True, displaySafeAction=False, overscan=1.0)
    pc.camera(camera, e=True, displaySafeTitle=False, overscan=1.0)

def turnResolutionGateOn(camera):
    global __resolutionGate__
    global __safeAction__
    global __safeTitle__
    if __resolutionGate__:
        pc.camera(camera, e=True, displayResolution=True, overscan=1.3)
        __resolutionGate__ = False
    if __safeAction__:
        pc.camera(camera, e=True, displaySafeAction=True, overscan=1.3)
        __safeAction__ = False
    if __safeTitle__:
        pc.camera(camera, e=True, displaySafeTitle=True, overscan=1.3)
        __safeTitle__ = False
        
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
