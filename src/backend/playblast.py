import shotactions
import shotplaylist
PlayListUtils = shotplaylist.PlaylistUtils
Action = shotactions.Action
from collections import OrderedDict
import pymel.core as pc
import os
import os.path as osp
import exportutils
import shutil
import maya.cmds as cmds
from exceptions import *



__poly_count__ = False
__HUD_DATE__ = '__HUD_DATE__'
__HUD_LABEL__ = '__HUD_LABEL__'
__HUD_USERNAME__ = '__HUD_USERNAME__'
__CURRENT_FRAME__ = 0.0

def playblast(data):
    pc.playblast(st=data['start'], et=data['end'], f=data['path'], fo=True,
                 quality=100, w=1280, h=720, compression='MS-CRAM', percent=100,
                 format='avi', sequenceTime=0, clearCache=True, viewer=False,
                 showOrnaments=True, fp=4, offScreen=True)

def getUsername():
    return os.environ.get('USERNAME').upper().replace('.', ' ')

def label():
    return 'ICE ANIMATIONS'

def recordCurrentFrame():
    global __CURRENT_FRAME__
    __CURRENT_FRAME__ = pc.currentTime()

def restoreCurrentFrame():
    global __CURRENT_FRAME__
    pc.currentTime(__CURRENT_FRAME__)

def hidePolyCount():
    global __poly_count__
    if pc.optionVar(q='polyCountVisibility'):
        __poly_count__ = True
        pc.Mel.eval('setPolyCountVisibility(0)')

def showPolyCount():
    global __poly_count__
    if __poly_count__:
        pc.Mel.eval('setPolyCountVisibility(1)')
        __poly_count__ = False

def showNameLabel():
    global __HUD_LABEL__
    global __HUD_USERNAME__
    if (pc.headsUpDisplay(__HUD_LABEL__, q=True, exists=True)):
        pc.headsUpDisplay(__HUD_LABEL__, remove=True) 
    pc.headsUpDisplay(__HUD_LABEL__, section=2, block=0, blockSize="large", dfs="large", command=label)
    if (pc.headsUpDisplay(__HUD_USERNAME__, q=True, exists=True)):
        pc.headsUpDisplay(__HUD_USERNAME__, remove=True)
    pc.headsUpDisplay(__HUD_USERNAME__, section=3, block=0, blockSize="large", dfs="large", command=getUsername)
    pc.headsUpDisplay(__HUD_USERNAME__, e=True, dfs='large')

def showDate():
    global __HUD_DATE__
    if (pc.headsUpDisplay(__HUD_DATE__, q=True, exists=True)):
        pc.headsUpDisplay(__HUD_DATE__, remove=True) 
    pc.headsUpDisplay(__HUD_DATE__, section=1, block=0, blockSize="large", dfs="large",
                      command="import pymel.core as pc;pc.date(format=\"DD/MM/YYYY hh:mm\")")

def removeNameLabel():
    global __HUD_LABEL__
    global __HUD_USERNAME__
    if pc.headsUpDisplay(__HUD_LABEL__, exists=True):
        pc.headsUpDisplay(__HUD_LABEL__, rem=True)
    if pc.headsUpDisplay(__HUD_USERNAME__, exists=True):
        pc.headsUpDisplay(__HUD_USERNAME__, rem=True)

def removeDate():
    global __HUD_DATE__
    if pc.headsUpDisplay(__HUD_DATE__, exists=True):
        pc.headsUpDisplay(__HUD_DATE__, rem=True)

class PlayblastExport(Action):
    _conf=None
    def __init__(self, *args, **kwargs):
        super(PlayblastExport, self).__init__(*args, **kwargs)
        self._conf = self.initConf()
        if not self.get('layers'): # display layers
            self['layers'] = []
        if not self.path:
            self.path = osp.expanduser('~')

    @staticmethod
    def initConf():
        width, height = exportutils.getDefaultResolution()
        conf = OrderedDict()
        playblastargs = OrderedDict()
        playblastargs['format']='qt'
        playblastargs['fo']=True
        playblastargs['quality']=100
        playblastargs['w']=width
        playblastargs['h']=height
        playblastargs['percent']=100
        playblastargs['compression']="H.264"
        playblastargs['sequenceTime']=0
        playblastargs['clearCache']=True
        playblastargs['viewer']=False
        playblastargs['showOrnaments']=True
        playblastargs['fp']=4
        playblastargs['offScreen']=True
        huds = OrderedDict()
        conf['playblastargs']=playblastargs
        conf['HUDs']=huds
        return conf

    def perform(self, readconf=True, **kwargs):
        if self.enabled:
            for layer in PlayListUtils.getDisplayLayers():
                if layer.name() in self.getLayers():
                    layer.visibility.set(1)
                else: layer.visibility.set(0)
            item = self.__item__
            try:
                if readconf: self.read_conf()
            except IOError:
                self._conf = PlayblastExport.initConf()
            
            pc.select(item.camera)
            pc.lookThru(item.camera)
            hidePolyCount()
            showDate()
            exportutils.turnResolutionGateOn(item.camera)
            exportutils.showFrameInfo(item)
            
            self.makePlayblast(sound=kwargs.get('sound'))
            
            exportutils.removeFrameInfo()
            removeDate()
            showPolyCount()
            exportutils.turnResolutionGateOff(item.camera)
            
            # hd playblast without huds
            if kwargs.get('hd'):
                removeNameLabel()
                exportutils.turnResolutionGateOffPer(item.camera)
                exportutils.setDefaultResolution((1920, 1080))
                self.makePlayblast(sound=kwargs.get('sound'), hd=True)
                exportutils.restoreDefaultResolution()
                #exportutils.turnResolutionGateOn(item.camera)
                showNameLabel()
        
    def addLayers(self, layers):
        self['layers'][:] = layers
    
    def getLayers(self):
        return self.get('layers', [])

    def getPath(self):
        return self.get('path')
    def setPath(self, val):
        self['path']=val
    path = property(getPath, setPath)

    def addHUDs(self):
        conf = self._conf
        for hud in conf.get('HUDs', {}):
            if pc.headsUpDisplay(hud, q=True, exists=True):
                pc.headsUpDisplay(hud, remove=True)
            pc.headsUpDisplay(hud, **conf['HUDS'][hud])

    def removeHUDs(self):
        conf = self._conf
        for hud in conf.get('HUDs', []):
            if pc.headsUpDisplay(hud, q=True, exists=True):
                pc.headsUpDisplay(hud, remove=True)


    def makePlayblast(self, item=None, sound=None, hd=False):
        if not item:
            item = self.__item__
            if not item:
                pc.warning("Item not set: cannot make playblast")

        conf = self._conf
        if sound:
            sound = exportutils.getAudioNode()
            if not sound:
                sound = ['']
        else: sound=['']
        itemName = item.name.split(':')[-1].split('|')[-1]
        tempFilePath = osp.join(self.tempPath, itemName)
        pc.playblast(format='qt', fo=1, st=item.getInFrame(), et=item.getOutFrame(),
                     f=tempFilePath,
                     s=str(sound[0]), sequenceTime=0, clearCache=1, viewer=0,
                     showOrnaments=1, fp=4, percent=100, compression="H.264",
                     quality=100, widthHeight=exportutils.getDefaultResolution(),
                     offScreen=1)
        tempFilePath += '.mov'
        if hd:
            path = osp.join(self.path, 'HD')
            try:
                os.mkdir(path)
            except: pass
        else:
            path = self.path
        exportutils.copyFile(tempFilePath, path)