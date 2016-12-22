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
from random import choice
from rpackutils.packinfo import parse_description
from rpackutils.packinfo import update_from_desc
from rpackutils.packinfo import PackInfo

def test_parse_desc():
    assert(os.environ['R_LIBS'])
    path = os.environ['R_LIBS']
    packages = os.listdir(path)
    for i in range(20):
        pack_name = choice(packages)
        fp = os.path.join(path, pack_name, 'DESCRIPTION')
        d = parse_description(fp)
        assert(d['version'])
        assert(d['package'])

def test_update_from_desc():
    assert(os.environ['R_LIBS'])
    path = os.environ['R_LIBS']
    packages = os.listdir(path)
    pack_name = choice(packages)
    pack = PackInfo(pack_name)
    fp = os.path.join(path, pack_name, 'DESCRIPTION')
    update_from_desc(pack, fp)
    assert(pack.version)
    assert(pack.fullname)


