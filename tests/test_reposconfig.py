###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import pytest
import json
from unittest import mock
from unittest.mock import patch
from rpackutils.config import Config
from rpackutils.reposconfig import ReposConfig
from rpackutils.provider import AbstractPackageRepository


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


def test_typeerror():
    config = "wrong type"
    try:
        ReposConfig(config)
        pytest.fail('Constructing a ReposConfig with '
                    'a parameter which is not an instance of '
                    'Config must raise an exception!')
    except Exception as e:
        pass


@patch('os.path.exists')
@patch('rpackutils.providers.artifactory.Artifactory._do_request')
@patch('rpackutils.providers.bioconductor.Bioconductor.check_connection')
@patch('rpackutils.providers.cran.CRAN.check_connection')
def test_reposconfig_creation(mock_cran, mock_bioc, mock_arti, mock_exists):
    # read the configuration file
    configfilepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources/rpackutils.conf')
    config = Config(configfilepath)
    # construct a reposconfig
    mock_exists.return_value = True
    mock_arti.return_value = MockResponse(200, "Ok")
    mock_bioc.return_value = True
    mock_cran.return_value = True
    reposconfig = ReposConfig(config)
    # verify the number of instances created
    assert(len(reposconfig.artifactory_instances) == 2)
    assert(len(reposconfig.renvironment_instances) == 3)
    assert(len(reposconfig.local_instances) == 1)
    # verify the instances names
    assert(reposconfig.artifactory_instance('artifactory') is not None)
    assert(reposconfig.artifactory_instance('artifactorydev') is not None)
    assert(reposconfig.renvironment_instance('R-3.1.2') is not None)
    assert(reposconfig.renvironment_instance('R-3.2.2') is not None)
    assert(reposconfig.renvironment_instance('R-3.2.5') is not None)
    assert(reposconfig.local_instance('local') is not None)
    # verify artifactory instance
    artifactory = reposconfig.artifactory_instance('artifactory')
    assert(artifactory.baseurl == 'https://artifactory.local/artifactory')
    assert(artifactory.auth[0] == 'artifactoryUser')
    assert(artifactory.auth[1] == 's3C437P4ssw@Rd')
    assert(artifactory.verify == '/toto/Certificate_Chain.pem')
    assert(len(artifactory.repos) == 4)
    assert('R-3.1.2' in artifactory.repos)
    assert('Bioc-3.0' in artifactory.repos)
    assert('R-local' in artifactory.repos)
    assert('R-Data-0.1' in artifactory.repos)
    # verify artifactorydev instance
    artifactorydev = reposconfig.artifactory_instance('artifactorydev')
    assert(artifactorydev.baseurl
           == 'https://artifactorydev.local/artifactory')
    assert(artifactorydev.auth[0] == 'artifactoryUserDev')
    assert(artifactorydev.auth[1] == 's3C437P4ssw@RdDev')
    assert(artifactorydev.verify == '/toto/Certificate_Chain_Dev.pem')
    assert(len(artifactorydev.repos) == 4)
    assert('R-3.1.2' in artifactorydev.repos)
    assert('Bioc-3.0' in artifactorydev.repos)
    assert('R-local' in artifactorydev.repos)
    assert('R-Data-0.1' in artifactorydev.repos)
    # verify R-3.1.2
    r312 = reposconfig.renvironment_instance('R-3.1.2')
    assert(r312.baseurl == '/home/john/opt/R-3.1.2')
    assert(len(r312.repos) == 1)
    assert('lib64/R/library' in r312.repos)
    # verify R.3.2.5
    r325 = reposconfig.renvironment_instance('R-3.2.5')
    assert(r325.baseurl == '/home/john/opt/R-3.2.5')
    assert(len(r325.repos) == 1)
    assert('lib64/R/library' in r325.repos)
    # verify local
    local = reposconfig.local_instance('local')
    assert(local.baseurl == '/home/john/RPackUtils/repository')
    assert(len(local.repos) == 2)
    assert('local1' in local.repos)
    assert('local2' in local.repos)


@patch('os.path.exists')
@patch('rpackutils.providers.artifactory.Artifactory._do_request')
@patch('rpackutils.providers.bioconductor.Bioconductor.check_connection')
@patch('rpackutils.providers.cran.CRAN.check_connection')
def test_reposconfig_instance(mock_cran, mock_bioc, mock_arti, mock_exists):
    # read the configuration file
    configfilepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources/rpackutils.conf')
    config = Config(configfilepath)
    # construct a reposconfig
    mock_exists.return_value = True
    mock_arti.return_value = MockResponse(200, "Ok")
    mock_bioc.return_value = True
    mock_cran.return_value = True
    reposconfig = ReposConfig(config)
    # check get repositories by name
    # existing repos
    assert(reposconfig.instance('artifactory') is not None)
    assert(reposconfig.instance('artifactory').name == 'artifactory')
    assert(reposconfig.instance('artifactorydev') is not None)
    assert(reposconfig.instance('artifactorydev').name == 'artifactorydev')
    assert(reposconfig.instance('R-3.1.2') is not None)
    assert(reposconfig.instance('R-3.1.2').name == 'R-3.1.2')
    assert(reposconfig.instance('R-3.2.5') is not None)
    assert(reposconfig.instance('R-3.2.5').name == 'R-3.2.5')
    assert(reposconfig.instance('local') is not None)
    assert(reposconfig.instance('local').name == 'local')
    # none existing repo
    assert(reposconfig.instance('thisreponamedoesnotexist') is None)


@patch('os.path.exists')
@patch('rpackutils.providers.artifactory.Artifactory._do_request')
@patch('rpackutils.providers.bioconductor.Bioconductor.check_connection')
@patch('rpackutils.providers.cran.CRAN.check_connection')
def test_reposconfig_instances_by_name(mock_cran, mock_bioc, mock_arti,
                                       mock_exists):
    # read the configuration file
    configfilepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources/rpackutils.conf')
    config = Config(configfilepath)
    # construct a reposconfig
    mock_exists.return_value = True
    mock_arti.return_value = MockResponse(200, "Ok")
    mock_bioc.return_value = True
    mock_cran.return_value = True
    reposconfig = ReposConfig(config)
    # check the whole list of repositories
    repos = reposconfig.repository_instances_by_name(
        ['artifactorydev', 'R-3.2.5'])
    assert(len(repos) == 2)
    assert('artifactorydev' in [repos[0].name, repos[1].name])
    assert('R-3.2.5' in [repos[0].name, repos[1].name])
