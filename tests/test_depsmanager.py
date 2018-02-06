###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import pytest

from rpackutils.graph import Graph
from rpackutils.graph import Node
from rpackutils.deps import DepsManager

# A set of package to test
pack_set = {
        'DCPM': ['apcluster', 'gplots', 'pander', 'whisker' ,'Rgraphviz'],
        'affy': ['R', 'BiocGenerics', 'Biobase'],
        'Rgraphviz': ['R', 'methods', 'utils', 'graph', 'grid']
        }

# def test_parse_descfile():
    # for pack in pack_set:
        # print('Testing package: {0}'.format(
            # pack))
        # path = os.path.join(librarypath, pack, 'DESCRIPTION')
        # assert(os.path.exists(path))
        # f = open(path, 'r')
        # content = f.readlines()
        # f.close()
        # name,_,deps = DepsManager.parse_descfile(content)
        # print('\t{0}'.format(','.join(deps)))
        # assert([x in pack_set[pack] for x in deps])

# @pytest.fixture
# def create_deps_graph():
#     packs = os.listdir(librarypath)
#     dm = DepsManager()
#     g = dm.tree(packs, useref=True,)
#     assert(g)
#     for idt in g.nodesidts:
#         print('Version: {0} - {1}'.format(
#             g.node(idt).version, g.node(idt)))
#     return g

# @pytest.fixture
# def create_deps_graph_no_ref():
#     packs = os.listdir(librarypath)
#     dm = DepsManager()
#     g, _ = dm.tree(packs, useref=False)
#     assert(g)
#     for idt in g.nodesidts:
#         print('Version: {0} - {1}'.format(
#             g.node(idt).version, g.node(idt)))
#     return g

# def tracecalls(node):
#     print('{0} : {1}'.format(
#         node.idt, node.version))


# def test_apply_fun():
    # g = create_deps_graph()
    # DepsManager.applyfun2graph(g, fun=tracecalls)

# def test_download():
    # g = create_deps_graph()
    # DepsManager.applyfun2graph(g, fun=DepsManager.download)

# def test_script4install():
    # g = create_deps_graph()
    # DepsManager.applyfun2graph(g, DepsManager.script4install)

# def test_script4install_noref():
    # g = create_deps_graph_no_ref()
    # DepsManager.applyfun2graph(g, DepsManager.script4install)

