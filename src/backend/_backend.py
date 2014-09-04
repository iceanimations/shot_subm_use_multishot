import pymel.core as pc

def playblast(data):
    pc.playblast(st=data['start'], et=data['end'], f=data['path'], fo=True,
                 quality=100, w=1280, h=720, compression='MS-CRAM', percent=100,
                 format='avi', sequenceTime=0, clearCache=True, viewer=False,
                 showOrnaments=True, fp=4)