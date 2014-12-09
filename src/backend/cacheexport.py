'''
contains class to export cache of the selected objects (meshes)
@author: Qurban Ali (qurban.ali@iceanimations.com)
'''

import shotactions
import shotplaylist
import pymel.core as pc
import maya.cmds as cmds
import os.path as osp
from collections import OrderedDict
import shutil
import os
import exportutils
from exceptions import *

PlayListUtils = shotplaylist.PlaylistUtils
Action = shotactions.Action

class CacheExport(Action):
    def __init__(self, *args, **kwargs):
        super(CacheExport, self).__init__(*args, **kwargs)
        if not self._conf:
            self._conf = CacheExport.initConf()
        if not self.path:
            self.path = osp.expanduser('~')
        if not self.get('objects'): # list to save objects for cache export
            self['objects'] = []
            
    @staticmethod
    def initConf():
        conf = dict()
        conf["version"] = 5
        conf["time_range_mode"] = 0
        conf["cache_file_dist"] = "OneFile"
        conf["refresh_during_caching"] = 0
        conf["cache_per_geo"] = "1"
        conf["cache_name"] = ""
        conf["cache_name_as_prefix"] = 0
        conf["action_to_perform"] = "export"
        conf["force_save"] = 0
        conf["simulation_rate"] = 1
        conf["sample_multiplier"] = 1
        conf["inherit_modf_from_cache"] = 1
        conf["store_doubles_as_float"] = 1
        conf["cache_format"] = "mcc"
        return conf
    
    def perform(self, **kwargs):
        if self.enabled:
            conf = self._conf
            item = self._item
            conf["start_time"] = item.getInFrame()
            conf["end_time"] = item.getOutFrame()
            conf["cache_dir"] = self.path.replace('\\', '/')
            
            self.exportCache(conf)
            
            pc.delete(map(lambda x: x.getParent(),self.combineMeshes))
            del self.combineMeshes[:]
            
            pc.select(item.camera)
            self.exportCam(self.path)
            
    def exportCam(self, path):
        location = osp.splitext(cmds.file(q=True, location=True))
        path = osp.join(osp.dirname(path), 'camera')
        itemName = self._item.name.split(':')[-1].split('|')[-1]+'_cam'
        tempFilePath = osp.join(self.tempPath, itemName)
        
        tempFilePath = pc.exportSelected(tempFilePath,
                  force=True,
                  expressions = False,
                  constructionHistory = False,
                  channels = True,
                  shader = False,
                  constraints = False,
                  options="v=0",
                  typ=cmds.file(q=True, type=True)[0],
                  pr = False)
        exportutils.copyFile(tempFilePath, path)
        
    def getPath(self):
        return self.get('path')
    def setPath(self, path):
        self['path'] = path
    path = property(getPath, setPath)
    
    def getObjects(self):
        return [pc.PyNode(obj) for obj in self.get('objects') if pc.objExists(obj)]
    def addObjects(self, objects):
        self['objects'][:] = objects
    objects = property(getObjects, addObjects)
    
    def MakeMeshes(self, objSets):
        self.combineMeshes = []
        for objectSet in [setName for setName in objSets
                          if type(pc.PyNode(setName)) != pc.nt.Mesh]:
            pc.select(pc.PyNode(objectSet).members())
            meshes = [shape
                      for transform in pc.PyNode(objectSet).dsm.inputs(
                              type = "transform")
                      for shape in transform.getShapes(type = "mesh",
                                                       ni = True)]
            combineMesh = pc.createNode("mesh")
            pc.rename(combineMesh, objectSet.split(":")[-1].split('|')[-1]+"_cache")
            self.combineMeshes.append(combineMesh)
            polyUnite = pc.createNode("polyUnite")
            for i in xrange(0, len(meshes)):
                meshes[i].outMesh >> polyUnite.inputPoly[i]
                meshes[i].worldMatrix[0] >> polyUnite.inputMat[i]
            polyUnite.output >> combineMesh.inMesh
        pc.select(self.combineMeshes)
    
    def exportCache(self, conf):
        pc.select(cl=True)
        if self.get('objects'):
            path = conf.get('cache_dir')
            tempFilePath = osp.join(self.tempPath, 'cache')
            tempFilePath = tempFilePath.replace('\\', '/')
            conf['cache_dir'] = tempFilePath
            command =  'doCreateGeometryCache2 {version} {{ "{time_range_mode}", "{start_time}", "{end_time}", "{cache_file_dist}", "{refresh_during_caching}", "{cache_dir}", "{cache_per_geo}", "{cache_name}", "{cache_name_as_prefix}", "{action_to_perform}", "{force_save}", "{simulation_rate}", "{sample_multiplier}", "{inherit_modf_from_cache}", "{store_doubles_as_float}", "{cache_format}"}};'.format(**conf)
            self.MakeMeshes(self.get('objects'))
            pc.Mel.eval(command)
            tempFilePath = tempFilePath.replace('/', '\\\\')
            try:
                for phile in os.listdir(tempFilePath):
                    philePath = osp.join(tempFilePath, phile)
                    exportutils.copyFile(philePath, path)
            except Exception as ex:
                pc.warning(str(ex))
