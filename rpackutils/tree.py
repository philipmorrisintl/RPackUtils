###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import copy
import networkx as nx
from .packinfo import PackInfo
from .rbasepackages import RBasePackages


class DepTree(object):
    # FUTURE: we could use multiple providers instead of a single one
    # in order ot search across several repositories
    def __init__(self, provider, lsargs=None, packinfoargs=None,
                 imports=True, depends=True, suggests=False):
        """
        Traverse Imports and Depends to build the dependency graph
        and ignores Suggests.
        
        :param provider: object of type AbstractProvider
        :param lsargs: dict of additional function parameters
                       for the provider's ls()
        :param packinfoargs: additional function parameters
                             for the provider's packinfo() function
        :param imports: traverse imports
        :param depends: traverse depends
        :param suggests: traverse suggests
        """
        self._g = nx.Graph()
        self.excludes = copy.deepcopy(RBasePackages.getnames())
        # TODO check the provider is an object in the
        # AbstractProvider hierarchy
        self.provider = provider
        self.lsargs = lsargs
        self.packinfoargs = packinfoargs
        self.imports = imports
        self.depends = depends
        self.suggests = suggests

    def build(self, packagenames=None):
        """
        Specify 1 or multiple package names, to build the
        dependencies tree.
        Specifying none will include all available packages in the
        dependencies tree.
        """
        if packagenames is None:
            if self.lsargs is not None:
                packagenames = self.provider.ls(**self.lsargs)
            else:
                packagenames = self.provider.ls()
        for packagename in packagenames:
            # Get package information, call recursive tree build
            self._add_node(packagename)

    def _add_node(self, packagename):
        if packagename in self.excludes:
            return
        if packagename in self._g.nodes():
            return
        if self.packinfoargs is not None:
            packinfo = self.provider.packinfo(
                packagename,
                **self.packinfoargs
            )
        else:
            packinfo = self.provider.packinfo(
                packagename
            )
        if packinfo is not None:
            self._add_to_graph(packinfo)
            if self.depends and packinfo.has_depends:
                for dep_name in packinfo.depends:
                    if dep_name in self.excludes:
                        continue
                    self._add_node(dep_name)
                    self._connect(packinfo.name, dep_name, "depends")
            if self.imports and packinfo.has_imports:
                for imp_name in packinfo.imports:
                    if imp_name in self.excludes:
                        continue
                    self._add_node(imp_name)
                    self._connect(packinfo.name, imp_name, "imports")
            if self.suggests and packinfo.has_suggests:
                for sug_name in packinfo.suggests:
                    if sug_name in self.excludes:
                        continue
                    self._add_node(sug_name)
                    self._connect(packinfo.name, sug_name, "suggests")

    def _add_to_graph(self, packinfo):
        self._g.add_node(packinfo.name, **packinfo.as_dict)

    def _connect(self, a, b, r):
        self._g.add_edge(a, b, relation=r)
