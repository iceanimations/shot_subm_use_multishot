import pymel.core as pc
import maya.OpenMaya as api

a = ''
def _memo(func):
    func._hash = {}
    def _wrapper(node):
        if func._hash.has_key(node):
            return func._hash[node]
        else:
            val = func(node)
            func._hash[node]=val
            return val
    return _wrapper

def getGeosets():
    geosets = []
    for node in pc.ls(exactType='objectSet'):
        if 'geo_set' in node.name().lower():
            geosets.append(node)
    return geosets

def getConnectedGeosets(mylist=None):
    geosets = set()
    if not mylist:
        mylist = pc.ls(sl=1)
    for node in mylist:
        for myset in node.outputs(type='objectSet'):
            if 'geo_set' in myset.name().lower():
                geosets.add(myset)
        for myset in node.firstParent2.outputs(type='objectSet'):
            if 'geo_set' in myset.name().lower():
                geosets.add(myset)

def findSetFromRootNode(root):
    mysets = set()
    pc.select(root)
    for mesh in pc.ls(sl=1, type='mesh', dag=True):
        for myset in mesh.firstParent2().outputs(type='objectSet'):
            if 'geo_set' in myset.name().lower():
                mysets.add(myset)
    return mysets

def findAllConnectedGeosets(mylist=None, restrictToNamespace=True):
    @_memo
    def _rootParent(node):
        if hasattr(node, 'firstParent2'):
            parent = node.firstParent2()
        else:
            return None
        if not parent:
            return node
        elif restrictToNamespace and parent.namespace() != node.namespace():
            return node
        else:
            return _rootParent(parent)

    selection = pc.ls(sl=1)
    if mylist is None:
        mylist = selection

    geosets = set()
    rootNodes = set()
    for node in mylist:
        node = pc.PyNode(node)
        parent = _rootParent(node)
        if parent is not None and parent not in rootNodes:
            rootNodes.add(parent)
            geosets.update(findSetFromRootNode(parent))
    pc.select(selection)
    return list(geosets)

def getFromScreen(x, y, x_rect=None, y_rect=None):
    sel = api.MSelectionList()
    api.MGlobal.getActiveSelectionList(sel)
    #get current selection

    #select from screen
    if x_rect!=None and y_rect!=None:
        api.MGlobal.selectFromScreen(x, y, x_rect, y_rect, api.MGlobal.kReplaceList)
    else:
        api.MGlobal.selectFromScreen(x, y, api.MGlobal.kReplaceList)
    objects = api.MSelectionList()
    api.MGlobal.getActiveSelectionList(objects)

    #restore selection
    api.MGlobal.setActiveSelectionList(sel, api.MGlobal.kReplaceList)
 
    #return the objects as strings
    fromScreen = []
    objects.getSelectionStrings(fromScreen)
    return fromScreen

def listSelectedControls():
    selection = pc.ls(sl=1, type='nurbsCurve', dag=True)
    return [node.firstParent() for node in selection]


def getFuture(node, visited=None):
    if visited is None:
        visited = set()
    outputs = [output for output in node.outputs(type=('constraint',
        'mesh', 'transform')) if output not in visited]
    visited.update(outputs)
    for thing in outputs:
        getFuture(thing, visited)
    return visited


def findDrivenMeshes(node, done=None):
    meshes = set()
    joints = set()
    if done is None:
        done = set()

    for obj in node.listRelatives(ad=True):
        if isinstance(obj, pc.nt.Mesh):
            meshes.add(obj.firstParent())
        elif isinstance(obj, pc.nt.Joint):
            joints.add(obj)

    for obj in getFuture(node):
        if isinstance(obj, pc.nt.Mesh):
            meshes.add(obj.firstParent())
        elif isinstance(obj, pc.nt.Joint):
            joints.add(obj)

    newdone = done.copy()
    newdone.update( joints )

    for joint in joints:
        if joint in done:
            continue
        meshes.update(findDrivenMeshes(joint, newdone))

    return meshes

def getSetFromMesh(mesh):
    return mesh.outputs(type='objectSet')


def findGeoSets():
    controls = listSelectedControls()

    geosets = set()
    for node in controls:
        meshes = findDrivenMeshes(node)
        print meshes
        for mesh in meshes:
            geosets.update(getSetFromMesh(mesh))
    return geosets

#if __name__ == '__main__':
#    import time
#    start = time.time()
#    objects = getFromScreen(0, 0, 4096, 4096)
#    sets = findAllConnectedGeosets(objects)
#    print time.time()-start
#    for i in sets: print i
