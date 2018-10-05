###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################


class Node(object):
    def __init__(self, key):
        self._idt = key
        self._connections = {}

    def connect(self, node, direction=1):
        self._connections[node.idt] = (node, direction)

    def __str__(self):
        return '{0} -> {1}'.format(
                self.idt, ','.join(self._connections.keys()))

    @property
    def connections(self):
        return self._connections.keys()

    @property
    def idt(self):
        return self._idt

    def direction(self, idt):
        if idt not in self._connections:
            return None
        else:
            return self.connections[idt][1]

    def node(self, idt):
        if idt not in self._connections:
            return None
        else:
            return self._connections[idt][0]


class Graph(object):
    def __init__(self):
        self._nodes = {}
        self._nbnodes = 0

    def addnode(self, node):
        self._nbnodes += 1
        self._nodes[node.idt] = node

    def node(self, idt):
        if idt in self._nodes:
            return self._nodes[idt]

    def __contains__(self, idt):
        return idt in self._nodes

    def connect(self, idtA, idtB, direction=1):
        assert(idtA in self._nodes)
        assert(idtB in self._nodes)
        self._nodes[idtA].connect(self._nodes[idtB], direction)

    @property
    def nodesidts(self):
        return self._nodes.keys()

    def __iter__(self):
        return iter(self._nodes.values())
