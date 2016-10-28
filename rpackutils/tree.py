##############################################################################
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
##############################################################################
# -*- coding: utf-8 > -*-
__author__ = "Sylvain Gubian"
__copyright__ = "Copyright 2016, PMP SA"
__license__ = "GPL2.0"
__email__ = "Sylvain.Gubian@pmi.com"

import os
import networkx as nx
from packtool.packinfo import PackInfo

class DepTreeBuilder(object):

    def __init__(self):
        self._g = nx.Graph()
        self._excludes = DEFAULT_PACKS.deep_copy()
        self.suggest = False

    def build_from_install(self, path=None):
        if not path:
            path = os.getcwd()
        folders = os.listdir(path)
        # Removing the packages to exclude
        folders = [x for x in folders if not x in self._excludes]
        # Getting the full path
        folders = [os.path.join(path, x) for x in folders]
        # Filtering, keeping only folders
        folders = [x for x in folders if os.path.isdir(x)]
        # Gettingt Package information
        for folder in folders:
            res = PackInfo.desc2dict(path=folder)




