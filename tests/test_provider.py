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

import pytest
from random import choice

from rpackutils.provider import Provider
from rpackutils.packinfo import PackInfo
from rpackutils.packinfo import PackStatus as Status
from . import download_package_example
from . import remove_package_example
from . import pack_example_fp
from . import pack_example_name

def test_provider_list():
    l = Provider.providers()
    assert(len(l) > 0)

def test_wrong_provider():
    with pytest.raises(ValueError):
        p = Provider('Test')

def test_local_provider_init():
    p = Provider('Local')
    assert(p.baseurl)

def local_provider_push():
    choices = [True, False]
    decision = choice(choices)
    if decision:
        remove_package_example(uninstall=decision)
    download_package_example()
    pack = PackInfo(pack_example_name)
    p = Provider('Local')
    decision = choice(choices)
    p.push(pack, source=pack_example_fp, overwrite=decision)
    p.packinfo(pack)
    assert(pack.status == Status.DEPLOYED)
    assert(pack.author)
    assert(pack.version)
    decision = choice(choices)

def test_local_provider_push():
    for i in range(5):
        local_provider_push()
    remove_package_example(uninstall=True)

def test_local_provider_download():
    pack = PackInfo('test')
    p = Provider('Local')
    with pytest.raises(RuntimeError):
        p.download(pack)

def test_local_provider_ls():
    p = provider('Local')
    pack_names = p.ls()
    assert(len(pack_names) > 0)

