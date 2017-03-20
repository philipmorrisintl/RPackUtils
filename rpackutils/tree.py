##############################################################################
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
##############################################################################
# -*- coding: utf-8 -*-
__author__ = "Sylvain Gubian"
__copyright__ = "Copyright 2016, PMP SA"
__license__ = "GPL2.0"
__email__ = "Sylvain.Gubian@pmi.com"

import os
import copy
import networkx as nx
from .packinfo import PackInfo
from .packinfo import BASE_PACKAGES


class DepTree(object):

    def __init__(self):
        self._g = nx.Graph()
        self.excludes = copy.deepcopy(BASE_PACKAGES)
        self.provider = None

    def build(self, roots=None):
        if self.provider is None:
            self.provider = Provider('Local')
            logger.warning('No provider specified, using Local as default')
        if roots is None:
            roots = self.provider.ls()
        for pack in roots:
            # Get package information, call recursive tree build
            self._add_node(pack)

    def _add_node(self, pack_name):
        if pack_name in self.excludes:
            return
        if pack_name in self._g.nodes():
            return
        pack = PackInfo(pack_name)
        self.provider.packinfo(pack)
        self._add_to_graph(pack)
        if pack.has_depends:
            for dep_name in pack.depends:
                if dep_name in self.excludes:
                    continue
                self._add_node(dep_name)
                self._connect(pack.name, dep_name, "depends")
        if pack.has_imports:
            for imp_name in pack.imports:
                if imp_name in self.excludes:
                    continue
                self._add_node(imp_name)
                self._connect(pack.name, imp_name, "imports")

    def _add_to_graph(self, pack):
        # Adding pack object to the Graph
        self._g.add_node(pack.name, pack.as_dict)

    def _connect(self, a, b, r):
        self._g.add_edge(a, b, relation=r)






