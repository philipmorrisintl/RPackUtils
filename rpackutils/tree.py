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
from .packinfo import PackInfo

class DepTree(object):

    def __init__(self):
        self._g = nx.Graph()
        self.excludes = DEFAULT_PACKS.deep_copy()
        self.provider = None

    def build(self, roots=None):
        if self.provider is None:
            self.provider = Provider('Local')
            logger.warning('No provider specified, using Local as default')
        if roots is None:
            roots = p.ls()
        for pack in roots:
            # Get package information, call recursive tree build
            self._add_node(pack)

    def _add_node(self, pack_name):
        pack = PackInfo(pack_name)
        self.provider.packinfo(pack)
        if pack.status < 0:
            self._add_to_graph(pack)
            return
        if pack.has_childs():
            for child in pack.childs:
                self._add_node(child)
        else:
            self._add_to_graph(pack)

    def _add_to_graph(self, pack):
        # Adding pack object to the Graph
        pass

    def traverse(self, func, *args, **kargs):
        pass





