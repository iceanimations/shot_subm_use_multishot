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
                self[ak].__item__ = item
            else:
                self[ak]=item.actions[ak]

    def getActions(self):
        actions = [] 
        for ak in self.keys():
            if isinstance(self[ak], Action):
                print self[ak]
                actions.append(self[ak])
        return actions

    def perform(self):
        for action in self.getActions():
            action.perform()

    def add(self, action):
        if not isinstance(action, Action):
            raise TypeError, "only Actions can be added"
        classname = action.__class__.__name__
        action._item = self._item
        self[classname] = action
        return action

    def remove(self, action):
        key=action
        if isinstance(action, Action):
            key = action.__class__.__name__
        if self.has_key(key):
            del self[key]


class Action(OrderedDict):
    __metaclass__ = ABCMeta
    _conf = None
    __item__ = None

    def __init__(self, item=None, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)

    @abstractmethod
    def perform(self, item):
        pass

    def _item():
        doc = "The _item property."
        def fget(self):
            return self.__item__
        def fset(self, value):
            self.__item__ = value
        return locals()
    _item = property(**_item())

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

    @classmethod
    def getActionFromList(cls, actionlist, forceCreate=True):
        if not isinstance(actionlist, ActionList):
            raise TypeError, "Only Action lists can be added"
        action = actionlist.get(cls.__name__)
        if not action and forceCreate:
            action = cls()
        return action


class PlayblastExport(Action):
    _conf=None
    def __init__(self, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)
        self._conf = self.initConf()
        if not self.path:
            self.path = osp.expanduser('~')

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
        conf['playblastargs']=playblastargs
        conf['HUDs']=huds
        return conf

    def getPath(self):
        return self.get('path')
    def setPath(self, val):
        self['path'] = val
    path = property(getPath, setPath)

    def perform(self, readconf=True):
        item = self.__item__
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

    def addHUDs(self):
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
            item = self.__item__
            if not item:
                pc.warning("Item not set: cannot make playblast")

        conf = self._conf

        print self['path'], type(self['path']), item.name
        pc.playblast(st=item.getInFrame(),
                et=item.getOutFrame(),
                f=osp.join(self['path'], item.name),
                **conf['playblastargs'])

def test():
    import shot_subm.src.backend.shotactions as sa
    reload(sa)

    import shot_subm.src.backend.shotplaylist as spl
    reload(spl)

    from collections import OrderedDict
    import pymel.core as pc
    pc.mel.eval('file -f -options "v=0;" -loadReferenceDepth "none"  -typ "mayaAscii" -o "D:/talha.ahmed/Documents/Downloads/S02EP22_SEQ03_Sh01-Sh09(7).ma";addRecentFile("D:/talha.ahmed/Documents/Downloads/S02EP22_SEQ03_Sh01-Sh09(7).ma", "mayaAscii");')
    pl = spl.Playlist()
    for cam in pc.ls(type='camera'):
        pl.addNewItem(cam.firstParent())


    for item in pl.getItems():
        pb = sa.PlayblastExport(path='d:\\')
        item.actions.add(pb)
        item.saveToScene()

    spl.plu._PlaylistUtils__iteminstances = OrderedDict()
    spl.plu._PlaylistUtils__playlistinstances = OrderedDict()


    pl = spl.Playlist()
    counter = 0
    for item in pl.getItems():
        if counter < 3:
            item.selected = True
        counter += 1

    pl.performActions()


if __name__ == '__main__':
    al = ActionList()
    al.add(PlayblastExport())
    print json.dumps(al)
