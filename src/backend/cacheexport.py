'''
contains class to export cache of the selected objects (meshes)
@author: Qurban Ali (qurban.ali@iceanimations.com)
'''

import shotactions
import shotplaylist
import pymel.core as pc
import maya.cmds as cmds
import os.path as osp
import shutil
import os
import exportutils
from exceptions import *
import qutil
reload(qutil)
import re
reload(exportutils)

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
        conf["version"] = 6
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
        conf["do_texture_export"] = 1
        conf["texture_export_data"] = [
                ("(?i).*nano.*", ["ExpRenderPlaneMtl.outColor"])]
        conf["texture_resX"] = 1024
        conf["texture_resY"] = 1024
        conf["worldSpace"] = 1
        return conf

    def perform(self, **kwargs):
        if self.enabled:
            conf = self._conf
            item = self._item
            conf["start_time"] = item.getInFrame()
            conf["end_time"] = item.getOutFrame()
            conf["cache_dir"] = self.path.replace('\\', '/')

            if self.exportCache(conf, kwargs.get('local')):

                self.exportAnimatedTextures(conf, kwargs.get('local'))

                pc.delete(map(lambda x: x.getParent(),self.combineMeshes))
                del self.combineMeshes[:]

                pc.select(item.camera)
                self.exportCam(kwargs.get('local'))


    def exportCam(self, local=False):
        location = osp.splitext(cmds.file(q=True, location=True))
        path = osp.join(osp.dirname(self.path), 'camera')
        itemName = qutil.getNiceName(self.plItem.name)+'_cam'+qutil.getExtension()
        tempFilePath = osp.join(self.tempPath, itemName)

        tempFilePath = pc.exportSelected(tempFilePath,
                  force=True,
                  expressions = False,
                  constructionHistory = False,
                  channels = True,
                  shader = False,
                  constraints = False,
                  options="v=0",
                  typ=qutil.getFileType(),
                  pr = False)
        if local:
            path = exportutils.getLocalDestination(path)
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

    def appendObjects(self, objs):
        objects = set([obj.name() for obj in self.objects])
        objects.update(objs)
        self.objects = list(objects)

    def removeObjects(self, objs):
        objects = set([obj.name() for obj in self.objects])
        objects.difference_update(objs)
        self.objects = list(objects)
        if len(self.objects) == 0:
            self.enabled = False

    def MakeMeshes(self, objSets):
        mapping = {}
        self.combineMeshes = []
        names = set()
        count = 1
        for objectSet in [setName for setName in objSets
                          if type(pc.PyNode(setName)) != pc.nt.Mesh]:
            meshes = [shape
                      for transform in pc.PyNode(objectSet).dsm.inputs(
                              )
                      for shape in transform.getShapes(type = "mesh",
                                                       ni = True)]
            if not meshes:
                errorsList.append('Could not Create cache for '+ str(objectSet)
                                  +'\nReason: This set is no longer a valid set')
                continue
            combineMesh = pc.createNode("mesh")
            name = qutil.getNiceName(objectSet)+"_cache"

            if name in names:
                name += str(count)
                count += 1
            names.add(name)
            pc.rename(combineMesh, name)
            try:
                mapping[osp.normpath(osp.join(self.path, name))] = str(qutil.getRefFromSet(pc.PyNode(objectSet)).path)
            except:
                mapping[osp.normpath(osp.join(self.path, name))] = ''
            self.combineMeshes.append(combineMesh)
            polyUnite = pc.createNode("polyUnite")
            for i in xrange(0, len(meshes)):
                meshes[i].outMesh >> polyUnite.inputPoly[i]
                meshes[i].worldMatrix[0] >> polyUnite.inputMat[i]
            polyUnite.output >> combineMesh.inMesh
        if mapping:
            try:
                data = None
                mappingsPath = osp.join(self.path, 'mappings.txt')
                if osp.exists(mappingsPath):
                    with open(mappingsPath) as fr:
                        data = eval(fr.read())
                with open(osp.join(self.path, 'mappings.txt'), 'w') as f:
                    if data:
                        mapping.update(data)
                    f.write(str(mapping))
            except Exception as ex:
                errorsList.append(str(ex))
            try:
                envPath = exportutils.getEnvFilePath()
                with open(osp.join(self.path, 'environment.txt'), 'w') as f:
                    f.write(str(envPath))
            except Exception as ex:
                errorsList.append(str(ex))
        pc.select(self.combineMeshes)

    def exportCache(self, conf, local=False):
        pc.select(cl=True)
        if self.get('objects'):
            path = conf.get('cache_dir')
            tempFilePath = osp.join(self.tempPath, 'cache')
            tempFilePath = tempFilePath.replace('\\', '/')
            conf['cache_dir'] = tempFilePath
            command =  'doCreateGeometryCache3 {version} {{ "{time_range_mode}", "{start_time}", "{end_time}", "{cache_file_dist}", "{refresh_during_caching}", "{cache_dir}", "{cache_per_geo}", "{cache_name}", "{cache_name_as_prefix}", "{action_to_perform}", "{force_save}", "{simulation_rate}", "{sample_multiplier}", "{inherit_modf_from_cache}", "{store_doubles_as_float}", "{cache_format}", "{worldSpace}"}};'.format(**conf)
            self.MakeMeshes(self.get('objects'))
            pc.Mel.eval(command)
            tempFilePath = tempFilePath.replace('/', '\\\\')
            try:
                for phile in os.listdir(tempFilePath):
                    philePath = osp.join(tempFilePath, phile)
                    if local:
                        path = exportutils.getLocalDestination(path)
                    exportutils.copyFile(philePath, path)
            except Exception as ex:
                pc.warning(str(ex))
            return True
        else:
            errorsList.append('No objects found enabled in '+self.plItem.name)
            return False

    def getAnimatedTextures(self, conf):
        ''' Use the conf to find texture attributes to identify texture
        attributes in the present scene/shot '''
        texture_attrs = []
        for key, attrs in conf['texture_export_data']:
            for obj in self.objects:
                if re.match( key, obj.name() ):
                    #TODO: tex is creating even if there is no nano
                    name = obj.name()
                    namespace = ':'.join(name.split(':')[:-1])
                    for attr in attrs:
                        nombre = namespace + '.' + attr
                        attr = pc.Attribute(namespace + ':' + attr)
                        texture_attrs.append((nombre, attr))
        return texture_attrs

    def exportAnimatedTextures(self, conf, local=False):
        ''' bake export animated textures from the scene '''

        if not self.get('objects'):
            return False

        tempFilePath = osp.join(self.tempPath, 'tex')
        if osp.exists(tempFilePath):
            shutil.rmtree(tempFilePath)
        os.mkdir(tempFilePath)

        start_time = int(self._item.getInFrame())
        end_time = int(self._item.getOutFrame())
        rx = conf['texture_resX']
        ry = conf['texture_resY']
        textures_exported = False

        for curtime in range(start_time, end_time+1):
            num = '%04d'%curtime
            pc.currentTime(curtime, e=True)

            for name, attr in self.getAnimatedTextures(conf):
                fileImageName = osp.join(tempFilePath,
                        '.'.join([name, num, 'png']))
                newobj = pc.convertSolidTx(attr, samplePlane=True, rx=rx, ry=ry,
                        fil='png', fileImageName=fileImageName)
                pc.delete(newobj)
                textures_exported = True

        target_dir = osp.join(self.path, 'tex')
        try:
            if not osp.exists(target_dir):
                if not local:
                    os.mkdir(target_dir)
        except Exception as ex:
            errorsList.append(str(ex))

        for phile in os.listdir(tempFilePath):
            philePath = osp.join(tempFilePath, phile)
            if local:
                target_dir = exportutils.getLocalDestination(target_dir, depth=4)
            exportutils.copyFile(philePath, target_dir, depth=4)

        return textures_exported
