import sys
sitedir = r'd:\talha.ahmed\workspace\repos'
if sitedir not in sys.path:
    sys.path.insert(0, sitedir)

import shot_subm
reload(shot_subm)
shot_subm.Submitter().show()
