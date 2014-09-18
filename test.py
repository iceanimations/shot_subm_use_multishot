
def test_backend():
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


def test_frontend():
    pass

if __name__ == '__main__':
    test_backend()
    test_frontend()
