'''

.. module:: shotactions
   :platform: Windows
   :synopsis: defines the basic data types for defining a playlist

.. moduleauthor:: 
    Talha Ahmed <talha.ahmed@iceanimations.com>

.. date:: Thu 09/11/2014
.. license:: MIT
.. copyright:: ICE Animations Pvt. Ltd. <www.iceanimations.com>

'''

from abc import ABCMeta, abstractmethod, abstractproperty
from collections import OrderedDict


class Action(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def loadconf(self):
        pass

    @abstractmethod
    def perform(self):
        pass

    name = abstractproperty()


class ActionList(OrderedDict):
    """A list of Actions that can be performed on a :class:`shotplaylist.PlaylistItem`
    or :class:`playlist.Playlist` """

    def __init__(self, *args, **kwargs):
        """Create an Action List"""
        super(ActionList, self).__init__(*args, **kwargs)

    def add(self, action):
        if not isinstance(action, Action):
            raise TypeError, "only Actions can be added"



class PlayblastExport(Action):
    pass

