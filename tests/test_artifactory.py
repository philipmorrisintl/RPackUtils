import os
import pytest
from rpackutils.artifactory import ArtifactoryHelper

REPOS_OK = 'R-3.0.2-local'
REPOS_NON_OK = 'R-3.0.3-local'

def test_repos_exists():
    ah = ArtifactoryHelper(REPOS_OK)
    assert(ah.exists())
    ah = ArtifactoryHelper(REPOS_NON_OK)
    assert(not ah.exists())

def test_list_files():
    ah = ArtifactoryHelper(REPOS_OK)
    files = ah.files
    assert(len(files) > 0)

def test_download_file():
    ah = ArtifactoryHelper(REPOS_OK)
    files = ah.files
    ah.download(files[0], './download.tmp')
    found = os.path.exists('./download.tmp')
    assert(found)
    if found:
        os.remove('./download.tmp')

def test_deploy_artifact():
    data_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),'data')
    files = [ os.path.join(data_path, f) for f in os.listdir(
        data_path) if os.path.isfile(os.path.join(data_path, f)) ]
    ArtifactoryHelper.deploy(REPOS_OK, data_path)
    ah = ArtifactoryHelper(REPOS_OK)
    fs = ah.files
    assert(os.path.basename(files[0]) in fs)

@pytest.mark.skipif("True")
def test_deploy_all():
    data_path = '/pmrdpc/bioconductor/3.0'
    ArtifactoryHelper.deploy('Bioc-3.0', data_path)

