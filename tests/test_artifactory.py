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
import tempfile
import shutil

from rpackutils.packinfo import PackInfo
from rpackutils.packinfo import PackStatus
from rpackutils.providers.artifactory import Artifactory
from rpackutils.utils import Utils
from rpackutils.config import Config

# configfilepath = os.path.join(
#     os.path.dirname(os.path.abspath(__file__)),
#     'resources/rpackutils_pmi.conf')

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
    def __init__(self, path):
        self.name, self.version = PackInfo._parse_package_name_version(path)
        self.status = None
        self.fullstatus = None
        self.repos = None
        self.depends = None
        self.imports = None
        self.suggests = None
        self.license = None


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


def test_create():
    create()


def test_get_api_url():
    arti = create()
    assert(arti._get_api_url('R-3.1.2') ==
           'https://artifactory.local/artifactory/api/storage/R-3.1.2')


@patch('rpackutils.providers.artifactory.Artifactory._do_request')
def test_ls(mock_do_request):
    arti = create()
    mockresjson = {
        "path": "/",
        "lastModified": "2017-03-08T16:21:11.504+01:00",
        "created": "2017-03-08T16:21:11.504+01:00",
        "lastUpdated": "2017-03-08T16:21:11.504+01:00",
        "uri": "https://artifactory.local/artifactory/api/storage/R-3.1.2",
        "repo": "R-3.1.2",
        "children": [{
            "folder": False,
            "uri": "/accelerometry_2.2.4.tar.gz"
        }, {
            "folder": False,
            "uri": "/ABCExtremes_1.0.tar.gz"
        }]
    }
    mock_do_request.return_value = MockResponse(200, json.dumps(mockresjson))
    files = arti.ls_repo('R-3.1.2')
    assert('accelerometry_2.2.4.tar.gz' in files)
    # mockresjson will be returned for both defined repositories
    files = arti.ls()
    assert("R-3.1.2/accelerometry_2.2.4.tar.gz" in files)
    assert("R-3.1.2/ABCExtremes_1.0.tar.gz" in files)
    assert("R-local/accelerometry_2.2.4.tar.gz" in files)
    assert("R-local/ABCExtremes_1.0.tar.gz" in files)


@patch('rpackutils.providers.artifactory.Artifactory._do_request')
def test_find(mock_do_request):
    arti = create()
    mockresjson = {
        "path": "/",
        "lastModified": "2017-03-08T16:21:11.504+01:00",
        "created": "2017-03-08T16:21:11.504+01:00",
        "lastUpdated": "2017-03-08T16:21:11.504+01:00",
        "uri": "https://rd-artifactory.app.pmi/artifactory/api/storage/R-3.1.2",
        "repo": "R-3.1.2",
        "children": [{
            "folder": False,
            "uri": "/accelerometry_2.2.4.tar.gz"
        }, {
            "folder": False,
            "uri": "/ABCExtremes_1.0.tar.gz"
        }]
    }
    mock_do_request.return_value = MockResponse(200, json.dumps(mockresjson))
    files = arti.find_repo('R-3.1.2', 'ABCExtremes_*')
    assert("ABCExtremes_1.0.tar.gz" in files)
    # mockresjson will be returned for both defined repositories
    files = arti.find("accelerometry_*.tar.gz")
    assert("R-3.1.2/accelerometry_2.2.4.tar.gz" in files)
    assert("R-local/accelerometry_2.2.4.tar.gz" in files)


@patch('rpackutils.providers.artifactory.Artifactory.find_repo')
@patch('rpackutils.providers.artifactory.Artifactory.download_single_fullname')
@patch('rpackutils.packinfo.PackInfo.__init__')
def test_download_single(mock_pi, mock_download_single_fullname,
                         mock_find_repo):
    arti = create()
    dest = tempfile.mkdtemp()
    mock_find_repo.return_value = ['Rpack_0.99.0.tar.gz']
    mock_download_single_fullname.return_value = PackStatus.DOWNLOADED
    mock_pi.return_value = PackInfoMock('Rpack_0.99.0.tar.gz')
    retVal = arti.download_single('R-local', 'Rpack', dest)
    assert(retVal == PackStatus.DOWNLOADED)
    shutil.rmtree(dest)


# @patch('rpackutils.providers.Artifactory.find_repo')
# @patch('rpackutils.providers.Artifactory.download_single')
# def test_download_multiple(mock_download_single, mock_find_repo):
def test_download_multiple():
    pass
    # arti = create()
    # dest = tempfile.mkdtemp()
    # mock_find_repo.return_value = ['Rpackabc_0.99.0.tar.gz',
    #                                'Rpacktru_1.2.3.tar.gz',
    #                                'Rpacksta_0.9.34.tar.gz']
    # mock_download_single.return_value = PackStatus.DOWNLOADED
    # retVals = arti.download_multiple(
    #     ['R-local', 'R-3.1.2', 'R-3.2.2'],
    #     ['Rpackabc', 'Rpacktru', 'Rpacksta'],
    #     dest,
    #     procs=3)
    # assert(retVals == [PackStatus.DOWNLOADED,
    #                    PackStatus.DOWNLOADED,
    #                    PackStatus.DOWNLOADED])
    # shutil.rmtree(dest)


@patch('rpackutils.utils.Utils.subprocesscall')
def test_upload_single(mock_subprocesscall):
    arti = create()
    artifact = "/some/path/to/a/package_version.tar.gz"
    mock_subprocesscall.return_value = (0, None, None)
    retVal = arti.upload_single(artifact, "fakerepo")
    assert(retVal == PackStatus.DEPLOYED)


@patch('rpackutils.utils.Utils.subprocesscall')
def test_upload_multiple(mock_subprocesscall):
    arti = create()
    artifacts = ["/path1/package1",
                 "/path2/package2",
                 "/path3/package3"]
    # success
    mock_subprocesscall.return_value = (0, None, None)
    retVals = arti.upload_multiple(artifacts, "sources-local", procs=3)
    assert(retVals == [PackStatus.DEPLOYED,
                       PackStatus.DEPLOYED,
                       PackStatus.DEPLOYED])
    # fail
    mock_subprocesscall.return_value = (1, None, None)
    retVals = arti.upload_multiple(artifacts, "sources-local", procs=3)
    assert(retVals == [PackStatus.DEPLOY_FAILED,
                       PackStatus.DEPLOY_FAILED,
                       PackStatus.DEPLOY_FAILED])


def test_packinfo_repo_multiple_versions():
    pass
    # config = Config(configfilepath)
    # arti = Artifactory(baseurl=config.get("artifactory-pmi", "baseurl"),
    #                    repos=['R-3.1.2', 'R-local'],
    #                    auth=(config.get("artifactory-pmi", "user"),
    #                          config.get("artifactory-pmi", "password")),
    #                    verify=config.get("artifactory-pmi", "verify"))
    # pi = arti.packinfo('RConferoDB', 'R-local')
    # assert(pi.name == 'RConferoDB')
    # assert(pi.version == '0.2.3')
    # assert(pi.license == 'INTERNAL')
    # assert('RCurl' in pi.depends)
    # assert('rjson' in pi.depends)
    # assert('limma' in pi.depends)
    # assert('samr' in pi.depends)
    # assert('Ridmap' in pi.depends)
    # assert('RGraph2js' in pi.depends)


def test_packinfo_repo_in_packagename():
    pass
    # config = Config(configfilepath)
    # arti = Artifactory(baseurl=config.get("artifactory-pmi", "baseurl"),
    #                    repos=['R-3.1.2', 'R-local'],
    #                    auth=(config.get("artifactory-pmi", "user"),
    #                          config.get("artifactory-pmi", "password")),
    #                    verify=config.get("artifactory-pmi", "verify"))
    # pi = arti.packinfo('R-local/RConferoDB')
    # assert(pi.name == 'RConferoDB')
    # assert(pi.version == '0.2.3')
    # assert(pi.license == 'INTERNAL')
    # assert('RCurl' in pi.depends)
    # assert('rjson' in pi.depends)
    # assert('limma' in pi.depends)
    # assert('samr' in pi.depends)
    # assert('Ridmap' in pi.depends)
    # assert('RGraph2js' in pi.depends)


def test_packinfo_packagename_only():
    pass
    # config = Config(configfilepath)
    # arti = Artifactory(baseurl=config.get("artifactory-pmi", "baseurl"),
    #                    repos=['R-3.1.2', 'R-local'],
    #                    auth=(config.get("artifactory-pmi", "user"),
    #                          config.get("artifactory-pmi", "password")),
    #                    verify=config.get("artifactory-pmi", "verify"))
    # pi = arti.packinfo('RConferoDB')
    # assert(pi.name == 'RConferoDB')
    # assert(pi.version == '0.2.3')
    # assert(pi.license == 'INTERNAL')
    # assert('RCurl' in pi.depends)
    # assert('rjson' in pi.depends)
    # assert('limma' in pi.depends)
    # assert('samr' in pi.depends)
    # assert('Ridmap' in pi.depends)
    # assert('RGraph2js' in pi.depends)


def test_packinfo_single_version():
    pass
    # config = Config(configfilepath)
    # arti = Artifactory(baseurl=config.get("artifactory-pmi", "baseurl"),
    #                    repos=['R-3.1.2', 'R-local'],
    #                    auth=(config.get("artifactory-pmi", "user"),
    #                          config.get("artifactory-pmi", "password")),
    #                    verify=config.get("artifactory-pmi", "verify"))
    # # packagename, repo
    # pi = arti.packinfo('RConferoDB_0.2.3.tar.gz', 'R-local')
    # assert(pi.name == 'RConferoDB')
    # assert(pi.version == '0.2.3')
    # assert(pi.license == 'INTERNAL')
    # assert('RCurl' in pi.depends)
    # assert('rjson' in pi.depends)
    # assert('limma' in pi.depends)
    # assert('samr' in pi.depends)
    # assert('Ridmap' in pi.depends)
    # assert('RGraph2js' in pi.depends)
    # # repo/packagename
    # pi = arti.packinfo('R-local/RConferoDB_0.2.3.tar.gz')
    # assert(pi.name == 'RConferoDB')
    # assert(pi.version == '0.2.3')
    # assert(pi.license == 'INTERNAL')
    # assert('RCurl' in pi.depends)
    # assert('rjson' in pi.depends)
    # assert('limma' in pi.depends)
    # assert('samr' in pi.depends)
    # assert('Ridmap' in pi.depends)
    # assert('RGraph2js' in pi.depends)
