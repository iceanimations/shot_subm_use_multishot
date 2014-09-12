'''
.. module:: shotplaylist
   :platform: Windows
   :synopsis: defines the basic data types for defining a playlist

.. moduleauthor::
    Talha Ahmed <talha.ahmed@iceanimations.com>

.. date:: Thu 09/11/2014
.. license:: MIT
.. copyright:: ICE Animations Pvt. Ltd. <www.iceanimations.com>

'''

from . import shotactions as actions
import pymel.core as pc
import re
import json
from collections import OrderedDict


class Playlist(object):
    def __new__(cls, code=''):
        if not isinstance(code, (str, unicode)):
            raise TypeError, "code must be string or unicode"
        code = re.sub('[^a-z]', '', code.lower())
        if not plu.__playlistinstances__.get(code):
            plu.__playlistinstances__[code]=object.__new__(cls, code)
        else:
            plu.__playlistinstances__[code].sync()
        return plu.__playlistinstances__[code]

    def __init__(self, code='', populate=True):
        self._code = code
        self.__items = set() #!!
        if populate: self.populate()

    def getCode(self):
        return self._code
    code = property(getCode)

    def populate(self):
        attrs = plu.getSceneAttrs()
        for a in attrs:
            item = PlaylistItem(a)
            item.readFromScene()

    def __itemBelongs(self, item):
        if not self._code or self._code in item.__playlistcodes__:
            return True
        return False

    def __addCodeToItem(self, item):
        if self._code and not self.__itemBelongs():
            item.__playlistcodes__.append(self._code)

    def __removeCodeFromItem(self, item):
        if self._code and self.__itemBelongs():
            item.__playlistcodes__.remove(self._code)

    def sync(self, deleteBadItems=False):
        for item in plu.__iteminstances__.values():
            if self.__itemBelongs(item):
                try:
                    item.readFromScene()
                except pc.MayaNodeError:
                    if deleteBadItems:
                        item.__remove__()

    def store(self, removeBadItems=True):
        for item in plu.__iteminstances__.values():
            if self.__itemBelongs(item):
                try:
                    item.saveToScene()
                except pc.MayaNodeError:
                    if removeBadItems:
                        item.__remove__()

    def addItem(self, item):
        self.__addCodeToItem()

    def addNewItem(self, camera, inFrame, outFrame):
        newItem = PlaylistItem(plu.createNewAttr(camera), inFrame, outFrame)
        self.addItem(newItem)
        return newItem

    def removeItem(self, item):
        if not self._code:
            item.__remove__()
        else:
            self.__removeCodeFromItem(item)

    def getItems(self, name=''):
        for item in plu.__iteminstances__.values():
            if self.__itemBelongs(item):
                yield item
        raise StopIteration


class PlaylistItem(object):
    def __new__(cls, attr, *args, **kwargs):
        if not isinstance(attr, pc.Attribute):
            raise TypeError, "'attr' can only be of type pymel.core.Attribute"
        if not attr.objExists() or not attr.node().getShapes(type='camera'):
            raise TypeError, "Attribute %s does not exist on a camera"%attr.name
        if not plu.__iteminstances__.get(attr):
            plu.__iteminstances__[attr]=object.__new__(cls, attr, *args,
                    **kwargs)
        return plu.__iteminstances__[attr]

    def __init__(self, attr, name='', inframe=None, outframe=None,
            saveToScene=True, actions=None):
        if not isinstance(name, (str, unicode)):
            raise TypeError, "'name' can only be of type str or unicode"
        self.__attr=attr
        self._camera=self.__attr.node()
        data = {}
        data['name']=name
        data['playlistcodes']=[]
        self.__data = data
        self.saveToScene()

    def setInFrame(self, inFrame):
        if not isinstance(inFrame, (int, float)):
            return TypeError, "In frame must be a number"
        self.__data['inFrame'] = inFrame
    def getInFrame(self):
        return self.__data['inFrame']
    inFrame=property(getInFrame, setInFrame)

    def setOutFrame(self, outFrame):
        if not isinstance(outFrame, (int, float)):
            return TypeError, "Out frame must be a number"
        self.__data['outFrame'] = outFrame
    def getOutFrame(self):
        return self.__data['outFrame']
    outFrame=property(getOutFrame, setOutFrame)

    def getCamera(self):
        return self.__attr.node()
    def setCamera(self, camera, dontSave=False, dontDelete=False):
        if plu.isNodeValid(camera) and camera != self._camera:
            #"Create a new attr on the camera and replace instance"
            oldattr = self.__attr
            self.__attr = plu.createNewAttr(camera)
            if not dontDelete:
                plu.deleteAttr(oldattr)
            if not dontSave:
                self.saveToScene()
            Playlist.__instance[self.__attr] = self
            del plu.__iteminstances__[oldattr]
    camera = property(getCamera, setCamera)

    def actions():
        doc = "The actions property."
        def fget(self):
            return self.__data.get('actions')
        def fset(self, value):
            if isinstance(value, actions.ActionList):
                self.__data['actions'] = value
            else:
                raise (TypeError,
                        "Invalid type: %s Expected"%str(actions.ActionList))
        return locals()
    actions = property(**actions())

    def saveToScene(self):
        if not self.existsInScene():
            if self.nodeExistsInScene():
                self.setCamera(self.__attr.node(), True, True)
            else:
                raise (pc.MayaNodeError,
                        'camera %s does not exist'%self.__attr.node().name())
        datastring = json.dumps(self.__data)
        self.__attr.set(datastring)

    def readFromScene(self):
        if not self.existsInScene():
            raise (pc.MayaNodeError,
                    'Attribute %s Does not exist in scene'%self.__attr.name())
        datastring = self.__attr.get()
        self.__data=json.loads(datastring)
        if not self.__data.has_key('actions'):
            self.__data['actions']={}
        self.__data['actions'] = actions.ActionList(self.__data['actions'])

    def __getPlaylistCodes__(self):
        return self.__data['playlistcodes']
    __playlistcodes__ = property(__getPlaylistCodes__)

    def existsInScene(self):
        return pc.objExists(self.__attr)

    def nodeExistsInScene(self):
        return self.__attr.node().objExists()

    def __remove__(self):
        try:
            plu.__iteminstances__.pop(self.__attr)
        except KeyError:
            pass
        try:
            self.__attr.delete() # del attributes on refs and locked nodes?
        except pc.MayaAttributeError:
            pass


class PlaylistUtils(object):
    attrPattern = re.compile(r'.*\.ShotInfo_(\d{2})')
    __iteminstances__ = OrderedDict()
    __playlistinstances__ = OrderedDict()

    @staticmethod
    def isNodeValid(node):
        if (not isinstance(node, pc.nt.Transform()) or not
                node.getShapes(type='camera')):
            raise (TypeError,
                    "node must be a pc.nt.Transform of a camera shape")
        return True

    @staticmethod
    def getSceneAttrs():
        ''' Get all shotInfo attributes in the Scene (or current namespace)'''
        attrs = []
        nodes = []
        for camera in pc.ls(type='camera'):
            nodes = camera.getAllParents()
            for node in nodes:
                attrs.extend(PlaylistUtils.getAttrs(node))
        return attrs

    @staticmethod
    def getAttrs(node):
        ''' Get all ShotInfo attributes from the node '''
        if PlaylistUtils.isNodeValid(node):
            return [attr for attr in node.listAttr() if
                    PlaylistUtils.attrPattern.match(attr)]

    @staticmethod
    def getSmallestUnusedAttrName(node):
        attrs = PlaylistUtils.getAttrs(node)
        for i in range(100):
            attrName = 'ShotInfo_%02d'%i
            nodeattr = node + '.' + attrName
            if nodeattr not in attrs:
                return attrName

    @staticmethod
    def createNewAttr(node):
        ''' :type node: pymel.core.nodetypes.Transform() '''
        attrName = PlaylistUtils.getSmallestUnusedAttrName(node)
        pc.addAttr(node, ln=attrName, dt="string")
        attr = node.attr(attrName)
        attr.setLocked(True)
        return attr

    @staticmethod
    def isAttrValid(attr):
        ''' Check if the given attribute is where shot info should be stored.
        It must be a string attribute on a camera transform node

        :type attr: pymel.core.Attribute()
        :raises TypeError: if attribute is not the expected type
        '''
        if not isinstance(attr, pc.Attribute) or attr.get(type=1) != "string":
            raise (TypeError,
                    "'attr' can only be of type pymel.core.Attribute of type\
                    string")
        if not attr.objExists() or not attr.node().getShapes(type='camera'):
            raise TypeError, "Attribute %s does not exist on a camera"%attr.name
        if not PlaylistUtils.attrPattern.match(attr):
            raise TypeError, "Attribute %s does not have the correct name"%attr.name

        return True

    @staticmethod
    def deleteAttr(attr):
        '''
        :type attr: pymel.core.Attribute()
        '''
        attr.delete()

    @staticmethod
    def getAllPlaylists():
        codes = set()
        masterPlaylist = Playlist()
        playlists = [masterPlaylist, ]
        for item in masterPlaylist.getItems():
            codes.update(item.__playlistcodes__)
        for c in codes:
            playlists.append(Playlist(c, False))


plu = PlaylistUtils
