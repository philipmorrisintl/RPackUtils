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

import pytest
import os

from rpackutils.provider import Provider
from rpackutils.packinfo import PackInfo
from rpackutils.packinfo import PackStatus as Status
from rpackutils.tree import DepTree

from . import get_local_provider


def test_build_tree():
    p = get_local_provider() 
    dt = DepTree()
    dt.provider = p
    dt.build()
    assert(len(dt._g.nodes()) > 10)
    assert(len(dt._g.edges()) > 10)
    print(dt._g.edges())
    from networkx.algorithms.dag import descendants
    from networkx.readwrite.gml import write_gml
    from networkx.readwrite.gml import literal_stringizer 
    write_gml(dt._g, os.path.join(os.getcwd(), 'test.gml'),
              stringizer=literal_stringizer)
    #  print(descendants(dt._g, 'ff'))
