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
import qutil
reload(qutil)
import time

PlayListUtils = shotplaylist.PlaylistUtils
Action = shotactions.Action
errorsList = []

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
            self.exportCam()
            
            if kwargs.get('applyCache'):
                self.applyCache()
            
    def getCombinedMesh(self, ref):
        '''returns the top level meshes from a reference node'''
        meshes = []
        if ref:
            for node in pc.FileReference(ref).nodes():
                if type(node) == pc.nt.Mesh:
                    try:
                        node.firstParent().firstParent()
                    except pc.MayaNodeError:
                        if not node.isIntermediate():
                            meshes.append(node.firstParent())
                    except Exception as ex:
                        errorsList.append('Could not retrieve combined mesh for Reference\n'+ref.path+'\nReason: '+ str(ex))
        return meshes
    
    def getMeshFromSet(self, ref):
        meshes = []
        if ref:
            try:
                _set = [obj for obj in pc.ls(et=pc.nt.ObjectSet) if obj.name().endswith('_geo_set')][0]
                return [pc.polyUnite(ch=1, mergeUVSets=1, *_set.members())[0]] # put the first element in list and return
            except:
                return meshes
        return meshes     
        
    def addRef(self, path):
        try:
            return pc.createReference(path)
        except Exception as ex:
            errorsList.append('Could not create Reference for\n'+ path +'\nReason: '+ str(ex))
            
    def applyCache(self):
        '''applies cache on the combined models connected to geo_sets
        and exports the combined models'''
        mapping = {}
        for objectSet in [setName for setName in self.get('objects')
                          if type(pc.PyNode(setName)) == pc.nt.ObjectSet]:
            cacheFile = osp.join(self.path, qutil.getNiceName(objectSet)+'_cache.xml')
            if osp.exists(cacheFile):
                path = pc.PyNode(objectSet).forCache.get()
                if path:
                    if osp.exists(path):
                        ref = self.addRef(path)
                        meshes = self.getCombinedMesh(ref)
                        if len(meshes) != 1:
                            meshes = self.getMeshFromSet(ref)
                        if len(meshes) == 1:
                            pc.mel.doImportCacheFile(cacheFile.replace('\\', '/'), "", meshes, list())
                        else:
                            errorsList.append('Unable to identify Combined mesh or ObjectSet\n'+ path +'\n'+ '\n'.join(meshes))
                    else:
                        errorsList.append('LD path does not exist for '+objectSet+'\n'+ path)
                else:
                    errorsList.append('LD path not added or specified for '+objectSet)
            else:
                errorsList.append('cache file does not exist\n'+ cacheFile)
            
    def exportCam(self):
        location = osp.splitext(cmds.file(q=True, location=True))
        path = osp.join(osp.dirname(self.path), 'camera')
        itemName = qutil.getNiceName(self._item.name)+'_cam'
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
            if not meshes:
                errorsList.append('Could not Create cache for '+ str(objectSet)
                                  +'\nReason: This set is no longer a valid set')
                continue
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
