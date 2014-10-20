'''
Created on Oct 14, 2014

@author: qurban.ali
'''
import pymel.core as pc
import os

__original_camera__ = None
__original_frame__ = None
__selection__ = None

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
    combinedMeshes = []
    for mesh in pc.ls(type='mesh'):
        transform = mesh.firstParent().name()
        if 'combined_mesh' in transform.lower():
            combinedMeshes.append(transform)
    return combinedMeshes