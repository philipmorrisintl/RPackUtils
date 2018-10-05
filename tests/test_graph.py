###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

from rpackutils.graph import Graph
from rpackutils.graph import Node


def create_graph():
    g = Graph()
    for i in range(10):
        n = Node(str(i))
        g.addnode(n)
    g.connect('0', '3', 1)
    g.connect('0', '4', 1)
    g.connect('1', '0', 1)
    g.connect('2', '0', 1)
    g.connect('2', '4', 1)
    g.connect('2', '7', 1)
    g.connect('2', '5', 1)
    g.connect('5', '8', 1)
    g.connect('4', '7', 1)
    g.connect('3', '6', 1)
    g.connect('3', '9', 1)
    return g


def test_create_graph():
    g = create_graph()
    for i in range(10):
        print(g.node(str(i)))
    assert(g)
