###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import json
import pytest
from unittest import mock
from unittest.mock import patch

from rpackutils.depsmanager import PackNode
from rpackutils.depsmanager import DepsManager
from rpackutils.packinfo import PackStatus
from rpackutils.providers.artifactory import Artifactory
from rpackutils.config import Config

configfilepath = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'resources/rpackutils.conf')


class MockResponse(object):
    def __init__(self, status_code, text, body=None):
        self.status_code = status_code
        self.text = text
        self.body = body
        self.ok = (status_code == 200)

    def json(self):
        return json.loads(self.text)

    def iter_content(self, chunk_size=1, decode_unicode=False):
        return None


class PackInfoMock(object):
    def __init__(self, name, status):
        self.name = name
        self.version = '0.0.1'
        self.status = status
        self.fullstatus = None
        self.repos = None
        self.depends = None
        self.imports = None
        self.suggests = None
        self.license = None
        self.packagepath = None

    def dependencies(self, withBasePackages):
        return []


@patch('rpackutils.providers.artifactory.Artifactory._do_request')
def create(mock_do_request):
    mock_do_request.return_value = MockResponse(200, "Ok")
    config = Config(configfilepath)
    arti = Artifactory(baseurl=config.get("artifactory", "baseurl"),
                       repos=['R-3.1.2', 'R-local'],
                       auth=(config.get("artifactory", "user"),
                             config.get("artifactory", "password")),
                       verify=config.get("artifactory", "verify"))
    return arti


def fakeprocess(packagename, param1, param2):
    assert(packagename)
    assert(param1 == 'param1value')
    assert(param2 == 'param2value')


@patch('rpackutils.providers.artifactory.Artifactory.packinfo')
def test_processnode_notfound(mock_packinfo):
    arti = create()
    package = 'fakePackage1'
    mock_packinfo.return_value = PackInfoMock(
        package,
        PackStatus.NOT_FOUND
    )
    dm = DepsManager(
        arti,
        fakeprocess,
        {'param1': 'param1value', 'param2': 'param2value'}
    )
    packNode = PackNode(package)
    dm.processnode(packNode)
    assert(dm.errors)
    assert(dm.notfound)
    assert(dm.notfound[0] == package)
    assert(not dm.downloadfailed)
    assert(not dm.processed)


@patch('rpackutils.providers.artifactory.Artifactory.packinfo')
def test_processnode_downloadfailed(mock_packinfo):
    arti = create()
    package = 'fakePackage1'
    mock_packinfo.return_value = PackInfoMock(
        package,
        PackStatus.DOWNLOAD_FAILED
    )
    dm = DepsManager(
        arti,
        fakeprocess,
        {'param1': 'param1value', 'param2': 'param2value'}
    )
    packNode = PackNode(package)
    dm.processnode(packNode)
    assert(dm.errors)
    assert(not dm.notfound)
    assert(dm.downloadfailed)
    assert(dm.downloadfailed[0] == package)
    assert(not dm.processed)


@patch('rpackutils.providers.artifactory.Artifactory.packinfo')
def test_processnode_none(mock_packinfo):
    arti = create()
    package = 'fakePackage1'
    mock_packinfo.return_value = None
    dm = DepsManager(
        arti,
        fakeprocess,
        {'param1': 'param1value', 'param2': 'param2value'}
    )
    packNode = PackNode(package)
    dm.processnode(packNode)
    assert(dm.errors)
    assert(dm.notfound)
    assert(dm.notfound[0] == package)
    assert(not dm.downloadfailed)
    assert(not dm.processed)


@patch('rpackutils.providers.artifactory.Artifactory.packinfo')
def test_processnode_ok(mock_packinfo):
    arti = create()
    package = 'fakePackage1'
    mock_packinfo.return_value = PackInfoMock(package, PackStatus.DOWNLOADED)
    dm = DepsManager(
        arti,
        fakeprocess,
        {'param1': 'param1value', 'param2': 'param2value'}
    )
    packNode = PackNode(package)
    dm.processnode(packNode)
    assert(not dm.errors)
    assert(not dm.notfound)
    assert(not dm.downloadfailed)
    assert(dm.processed[0] == package)
