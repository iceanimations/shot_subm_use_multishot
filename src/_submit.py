'''
Created on Sep 1, 2014

@author: qurban.ali
'''
import site
site.addsitedir(r'R:\Pipe_Repo\Users\Qurban\utilities')
from uiContainer import uic
import os
import os.path as osp

root_path = osp.dirname(osp.dirname(__file__))
ui_path = osp.join(root_path, 'ui')

Form, Base = uic.loadUiType()
class Submitter(Form, Base):
    pass