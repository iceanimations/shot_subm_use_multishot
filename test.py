def test_backend():
    print "importing stuff ..."
    import sys
    sys.path.insert(0, r'd:\talha.ahmed\workspace\repos')

    import shot_subm.src.backend.shotactions as sa
    reload(sa)

    import shot_subm.src.backend.shotplaylist as spl
    reload(spl)

    import shot_subm.src.backend.playblast as pbl
    reload(pbl)

    from collections import OrderedDict
    import pymel.core as pc


    print "loading file ..."
    pc.mel.eval('file -f -options "v=0;" -loadReferenceDepth "none"  -typ "mayaAscii" -o "D:/talha.ahmed/Documents/Downloads/S02EP22_SEQ03_Sh01-Sh09(7).ma";addRecentFile("D:/talha.ahmed/Documents/Downloads/S02EP22_SEQ03_Sh01-Sh09(7).ma", "mayaAscii");')
    pl = spl.Playlist()

    print "adding items on each camera ..."
    for cam in pc.ls(type='camera'):
        if not cam.orthographic.get():
            item = pl.addNewItem(cam.firstParent())

    print "Adding actions to each item ..."
    for item in pl.getItems():
        pb = pbl.PlayblastExport(path='d:\\')
        #pb.path = 'd:\\'
        item.actions.add(pb)
        #import json
        #print json.dumps(item._PlaylistItem__data)
        item.saveToScene()

    print "Clearing object cache ..."
    spl.plu._PlaylistUtils__iteminstances = OrderedDict()
    spl.plu._PlaylistUtils__playlistinstances = OrderedDict()

    pl = spl.Playlist()
    counter = 0
    for item in pl.getItems():
        if counter < 3:
            item.selected = True
        counter+=1
        #print item.actions['PlayblastExport'].path
    pl.performActions()

def test_frontend():
    pass

if __name__ == '__main__':
    test_backend()
    test_frontend()
