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
from rpackutils.artifactory import ArtifactoryHelper

REPOS_OK = 'R-3.0.2-local'
REPOS_NOT_OK = 'R-3.0.3-local'

artifactoryConfig = os.path.join(
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

@patch('rpackutils.artifactory.ArtifactoryHelper._do_request')
def test_repos_exists(mock_do_request):
    mock_do_request.return_value = MockResponse(200, "Ok")
    ah = ArtifactoryHelper(REPOS_OK, artifactoryConfig)
    assert(ah.exists())
    mock_do_request.return_value = MockResponse(404, "Not found")
    ah = ArtifactoryHelper(REPOS_NOT_OK, artifactoryConfig)
    assert(not ah.exists())

@patch('rpackutils.artifactory.ArtifactoryHelper._do_request')
def test_list_files(mock_do_request):
    mock_do_request.return_value = MockResponse(200, '{ \"children\": [{ \"uri\" : \"/child1\", \"folder\" : true },{ \"uri\" : \"/child2\", \"folder\" : false } ] }')
    ah = ArtifactoryHelper(REPOS_OK, artifactoryConfig)
    files = ah.files
    assert(len(files) > 0)

@patch('rpackutils.artifactory.ArtifactoryHelper._do_request')
def test_download_file(mock_do_request):
    mock_do_request.return_value = MockResponse(200, '{ \"children\": [{ \"uri\" : \"/child1\", \"folder\" : true },{ \"uri\" : \"/child2\", \"folder\" : false } ] }')
    ah = ArtifactoryHelper(REPOS_OK, artifactoryConfig)
    files = ah.files
    # TODO
    # mock_do_request.return_value = MockResponse(200, '12345', '12345\n12345')
    # ah.download(files[0], './download.tmp')
    # found = os.path.exists('./download.tmp')
    # assert(found)
    # if found:
    #     os.remove('./download.tmp')

#FIXME: Mock multiprocessing, _pickle.PicklingError: Can't pickle <class 'unittest.mock.MagicMock'>
# @patch('rpackutils.artifactory.ArtifactoryHelper.deployArtifact')
# @patch('rpackutils.artifactory.ArtifactoryHelper._do_request')
# def test_deploy_artifact(mock_deployArtifact, mock_do_request):
#     data_path = os.path.join(
#         os.path.abspath(os.path.dirname(__file__)), 'data')
#     files = [ os.path.join(data_path, f) for f in os.listdir(
#         data_path) if os.path.isfile(os.path.join(data_path, f)) ]
#     ah = ArtifactoryHelper(REPOS_OK, artifactoryConfig)
#     mock_deployArtifact.return_value = "ok"
#     ah.deploy(REPOS_OK, data_path)
#     mock_do_request.return_value = MockResponse(200, '{ \"children\": [{ \"uri\" : \"/child1\", \"folder\" : true },{ \"uri\" : \"' + file[0] + '\", \"folder\" : false } ] }')
#     fs = ah.files
#     assert(os.path.basename(files[0]) in fs)
