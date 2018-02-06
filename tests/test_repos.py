###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
from unittest import mock
from unittest.mock import patch
from rpackutils.repos import RRepository

REPOS_TEST = 'R-3.1.2'
REPOS_TEST2 = 'R-local'

artifactoryConfig = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 
    'resources/rpackutils.conf')

DESCRIPTION = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 
    'resources/DESCRIPTION')

def test_parse_pack_name():
    name, version = RRepository.parse_pack_name('CompQuadForm_1.4.1.tar.gz')
    assert(name == 'CompQuadForm')
    assert(version == '1.4.1')

@patch('rpackutils.artifactory.ArtifactoryHelper.exists')
@patch('rpackutils.artifactory.ArtifactoryHelper.files')
def test_latest_version(mock_exists, mock_files):
    mock_exists.return_value = True
    mock_files.return_value = ["package1-0.99.0.tar.gz",
                               "package2-1.0.0.tar.gz",
                               "package3-0.99.1.tar.gz"]
    rr = RRepository(REPOS_TEST2, artifactoryConfig)
    packs = rr.packages
    for p in packs:
        print('{0} - Version: {1}'.format(p,
            rr.package_version(p)))

@patch('rpackutils.artifactory.ArtifactoryHelper.exists')
@patch('rpackutils.artifactory.ArtifactoryHelper.files')
def test_pack_list(mock_exists, mock_files):
    mock_exists.return_value = True
    packages_list = ["package1",
                     "package2",
                     "package3"]
    packs = {"package1": {'version': '0.99.0'},
             "package2": {'version': "1.0.0"},
             "package3": {'version': "0.99.1"}}
    mock_files.return_value = packages_list
    rr = RRepository(REPOS_TEST, artifactoryConfig)
    # mock the pack attribute
    rr._packs = packs
    assert(len(rr.packages) > 0)
    name = packages_list[0].split('_')[0]
    assert(rr.package_version(name) == '0.99.0')

@patch('rpackutils.artifactory.ArtifactoryHelper.exists')
@patch('rpackutils.artifactory.ArtifactoryHelper.files')
def test_description(mock_exists, mock_files):
    # read a R DESCRIPTION file
    f = open(DESCRIPTION, 'r', encoding='utf-8', errors='ignore')
    content = f.readlines()
    f.close()
    # fake the repo but not the reading of the file
    mock_exists.return_value = True
    packages_list = ["package1",
                     "package2",
                     "package3"]
    mock_files.return_value = packages_list
    rr = RRepository(REPOS_TEST, artifactoryConfig)
    packname, version, deps = rr.parse_descfile(content)
    assert(packname == "FooBar")
    assert(version == "1.1.4")
    assert(len(deps) == 1)
