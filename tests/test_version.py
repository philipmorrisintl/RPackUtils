###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import pytest
from distutils.version import LooseVersion


def test_version():
    assert(LooseVersion('0.99.2-45') > LooseVersion('0.99.2-12'))
    assert(LooseVersion('0.99.2-45') > LooseVersion('0.99.2'))
    assert(LooseVersion('1.0.2') > LooseVersion('0.99.2-1'))
    assert(LooseVersion('2.0') > LooseVersion('1.0.1'))
    # This will fail
    # RPACU-24 FIX version mismatch in the LooseVersion comparison
    # assert(LooseVersion('0.9.42') > LooseVersion('0.9-41'))
