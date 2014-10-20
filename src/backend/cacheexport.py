'''
contains class to export cache of the selected objects (meshes)
@author: Qurban Ali (qurban.ali@iceanimations.com)
'''

import shotactions
import shotplaylist
import pymel.core as pc
import os.path as osp
from collections import OrderedDict

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
        conf["start_time"] = 0
        conf["end_time"] = 1
        conf["cache_file_dist"] = "OneFile"
        conf["refresh_during_caching"] = 1
        conf["cache_dir"] = ''
        conf["cache_per_geo"] = 1
        conf["cache_name"] = ""
        conf["cache_name_as_prefix"] = 0
        conf["action_to_perform"] = "export"
        conf["force_save"] = 0
        conf["simulation_rate"] = 1
        conf["sample_multiplier"] = 1
        conf["inherit_modf_from_cache"] = 0
        conf["store_doubles_as_float"] = 1
        conf["cache_format"] = "mcx"
        return conf
    
    def perform(self):
        print 'cache enabled:', self.enabled
        if self.enabled:
            conf = self._conf
            item = self._item
            conf["start_time"] = item.getInFrame()
            conf["end_time"] = item.getOutFrame()
            conf["cache_dir"] = self.path.replace('\\', '/')
            print 'conf:', conf
            self.exportCache(conf)
        
    def getPath(self):
        return self.get('path')
    def setPath(self, path):
        self['path'] = path
    path = property(getPath, setPath)
    
    def getObjects(self):
        return [pc.PyNode(obj) for obj in self.get('objects')]
    def addObjects(self, objects):
        self['objects'][:] = objects
    objects = property(getObjects, addObjects)
    
    def exportCache(self, conf):
        pc.select(cl=True)
        if self.get('objects'):
            command =  'doCreateGeometryCache2 {version} {{ "{time_range_mode}", "{start_time}", "{end_time}", "{cache_file_dist}", "{refresh_during_caching}", "{cache_dir}", "{cache_per_geo}", "{cache_name}", "{cache_name_as_prefix}", "{action_to_perform}", "{force_save}", "{simulation_rate}", "{sample_multiplier}", "{inherit_modf_from_cache}", "{store_doubles_as_float}", "{cache_format}"}};'.format(**conf)
            print 'command:', command
            for obj in self.get('objects'):
                pc.select(obj, add=True)
            pc.Mel.eval(command)
            