'''

.. module:: shotactions
   :platform: Windows
   :synopsis: defines an actionlist, and an action interface

.. moduleauthor:: 
    Talha Ahmed <talha.ahmed@iceanimations.com>

.. date:: Thu 09/11/2014
.. license:: MIT
.. copyright:: ICE Animations Pvt. Ltd. <www.iceanimations.com>

'''

from abc import ABCMeta, abstractmethod, abstractproperty
from collections import OrderedDict
import pymel.core as pc
import json
import os.path as osp


dir_path = osp.dirname(__file__)


class ActionList(OrderedDict):
    """A list of Actions that can be performed on a :class:`shotplaylist.PlaylistItem`
    or :class:`playlist.Playlist` """

    def __init__(self, item, *args, **kwargs):
        """Create an Action List"""
        super(ActionList, self).__init__(*args, **kwargs)
        self._item = item
        actionsubs = Action.inheritors()
        if not item.actions:
            return
        for ak in item.actions.keys():
            cls = actionsubs.get(ak)
            if cls:
                self[ak]=cls(item.actions[ak])
            else:
                self[ak]=item.actions[ak]

    def getActions(self):
        actions = [] 
        for ak in self.keys():
            if isinstance(ak, Action):
                actions.append(self[ak])
        return actions

    def perform(self):
        for action in self.getActions():
            action.peform()

    def add(self, action):
        if not isinstance(action, Action):
            raise TypeError, "only Actions can be added"
        classname = action.__class__.__name__
        action.item = self._item
        self[classname] = action

    def remove(self, action):
        key=action
        if isinstance(action, Action):
            key = action.__class__.__name__
        if self.has_key(key):
            del self[key]


class Action(OrderedDict):
    __metaclass__ = ABCMeta
    _conf = None

    def __init__(self, item=None, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)

    @abstractmethod
    def perform(self, item):
        pass

    def setItem(self, item):
        self._item = item
    def getItem(self, item):
        return self._item
    item = property(getItem, setItem)

    def read_conf(self, confname=''):
        if not confname:
            confname = self.__class__.__name__
        with open(osp.join(dir_path, confname)) as conf:
            self._conf = json.load(conf)

    def write_conf(self, confname=''):
        if not confname:
            confname = self.__class__.__name__
        with open(osp.join(dir_path, confname), 'w+') as conf:
            json.dump(self._conf, conf)

    def get_conf(self):
        return self._conf
    conf = property(get_conf)

    @classmethod
    def inheritors(klass):
        subclasses = dict()
        work = [klass]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                if child not in subclasses.values():
                    scname = child.__name__
                    subclasses[scname] = child
                    work.append(child)
        return subclasses


class PlayblastExport(Action):
    _item=None
    _conf=None
    def __init__(self, path, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)
        self._conf = self.initConf()
        self['path']=path

    @staticmethod
    def initConf():
        conf = OrderedDict()
        playblastargs = OrderedDict()
        playblastargs['fo']=True
        playblastargs['quality']=100
        playblastargs['w']=1280
        playblastargs['h']=720
        playblastargs['percent']=100
        playblastargs['compression']='MS-CRAM'
        playblastargs['format']='avi'
        playblastargs['sequenceTime']=0
        playblastargs['clearCache']=True
        playblastargs['viewer']=False
        playblastargs['showOrnaments']=True
        playblastargs['fp']=4
        playblastargs['offScreen']=True
        huds = OrderedDict()
        huds['HUDDate'] = {}
        conf['playblastargs']=playblastargs
        conf['HUDs']=huds
        return conf

    def perform(self, readconf=True):
        item = self._item
        try:
            if readconf: self.read_conf()
        except IOError:
            self._conf = PlayblastExport.initConf()
        # Hide layers and gather info
        self.addHUDs()
        pc.select(item.camera)
        pc.lookThru(item.camera)
        self.makePlayblast()
        # Show layers back
        self.removeHUDs()

    def makeHUDs(self):
        conf = self._conf
        for hud in conf.get('HUDs', []):
            if pc.headsUpDisplay(hud, q=True, exists=True):
                pc.headsUpDisplay(hud)
            pc.headsUpDisplay(hud, **conf['HUDS'][hud])

    def removeHUDs(self):
        conf = self._conf
        for hud in conf.get('HUDs', []):
            if pc.headsUpDisplay(hud, q=True, exists=True):
                pc.headsUpDisplay(hud, remove=True)


    def makePlayblast(self, item=None):
        if not item:
            item = self._item
            if not item:
                pc.warning("Item not set: cannot make playblast")

        conf = self._conf

        pc.playblast(st=item.getInFrame(),
                et=item.getOutFrame(),
                f=osp.join(self['path'], item.name),
                **conf['playblastargs'])


if __name__ == '__main__':
    al = ActionList()
    al.add(PlayblastExport())
    print json.dumps(al)
