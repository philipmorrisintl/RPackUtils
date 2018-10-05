###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import pytest
import os
import glob
import tarfile
import tempfile
import shutil

from rpackutils.providers.cran import CRAN
from rpackutils.packinfo import PackInfo
from rpackutils.packinfo import PackStatus
from rpackutils.providers.localrepository import LocalRepository
from rpackutils.utils import Utils

LOCALREPO_BASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'resources/R')

REPOS = ['library']

LOCALREPO_LIBS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'resources/R/library')

PACKAGEPATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'resources/FooBar_0.99.1.tar.gz')

Utils.rmtree_under(LOCALREPO_LIBS)
#####################################################################
# SOMW TESTS WILL BE SKIPPED IF NO INTERNET CONNECTION IS AVAILABLE #
#####################################################################

# CRAN
cran = None
try:
    cran = CRAN()
except Exception as e:
    pass


def cran_is_available():
    if cran is not None:
        return cran.check_connection_mran_snapshot(numtries=1)
    else:
        return False


cran = CRAN()
packages = ["ggplot2",
            "data.table",
            "plyr"]
download_status = cran.download_multiple('2018-02-27',
                                         packages,
                                         dest=LOCALREPO_LIBS,
                                         procs=5)
localRepo = LocalRepository(
    LOCALREPO_BASE,
    REPOS
)

# def cleanup():
#     Utils.rmtree_under(LOCALREPO_LIBS)


def test_create():
    assert(localRepo.baseurl == LOCALREPO_BASE)
    assert(localRepo.repos == REPOS)
    # invalid baseurl
    try:
        LocalRepository(
            '/invalid/local/repobase',
            REPOS
        )
        pytest.fail('Constructing a LocalRepository with '
                    'an invalid baseurl must raise an Exception!')
    except Exception:
        pass
    # invalid repos
    try:
        LocalRepository(
            LOCALREPO_BASE,
            ['invalid1', 'invalid2', 'invalid3']
        )
        pytest.fail('Constructing a LocalRepository with '
                    'an invalid repos list must raise an Exception!')
    except Exception:
        pass


@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_find():
    assert(len(localRepo.find("*.tar.gz")) == 3)
    assert(len(localRepo.find("*.zip")) == 0)


@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_ls():
    packagenames = localRepo.ls(packagenamesonly=True)
    assert(len(packagenames) == 3)
    assert('ggplot2' in packagenames)
    assert('data.table' in packagenames)
    assert('plyr' in packagenames)
    filenames = localRepo.ls(packagenamesonly=False)
    assert(len(filenames) == 3)
    assert('library/ggplot2_2.2.1.tar.gz' in filenames)
    assert('library/data.table_1.10.4-3.tar.gz' in filenames)
    assert('library/plyr_1.8.4.tar.gz' in filenames)


@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_download_single():
    # test download success
    destfolder = tempfile.mkdtemp()
    downloadStatus = localRepo.download_single('ggplot2', destfolder)
    assert(downloadStatus == PackStatus.DOWNLOADED)
    assert(os.path.exists(
        os.path.join(destfolder,
                     'ggplot2_2.2.1.tar.gz')
        ))
    shutil.rmtree(destfolder)
    # test download failure, package not found
    downloadStatus = localRepo.download_single(
        'notexistingpackage', destfolder)
    assert(downloadStatus == PackStatus.NOT_FOUND)
    # test download failure, dest folder does not exist
    downloadStatus = localRepo.download_single(
        'plyr', '/some/wreid/none/existing/path')
    assert(downloadStatus == PackStatus.DOWNLOAD_FAILED)


def test_upload_single():
    uploadStatus = localRepo.upload_single(PACKAGEPATH, 'library')
    assert(uploadStatus == PackStatus.DEPLOYED)
    # test upload, overwrite existing
    uploadStatus = localRepo.upload_single(
        PACKAGEPATH, 'library', overwrite=True)
    assert(uploadStatus == PackStatus.DEPLOYED)
    # test upload do not overwrite existing
    uploadStatus = localRepo.upload_single(
        PACKAGEPATH, 'library', overwrite=False)
    assert(uploadStatus == PackStatus.DEPLOYED)
    # test uploa with invalid repo
    uploadStatus = localRepo.upload_single(PACKAGEPATH, 'noneexistingrepo')
    assert(uploadStatus == PackStatus.DEPLOY_FAILED)
    # repo = None
    uploadStatus = localRepo.upload_single(PACKAGEPATH, None)
    assert(uploadStatus == PackStatus.INVALID)
    # none existing packagepath
    uploadStatus = localRepo.upload_single(
        '/some/invalid/package/path/foo.tar.gz', 'library')
    assert(uploadStatus == PackStatus.DEPLOY_FAILED)


@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_packinfo():
    ggplot2 = localRepo.packinfo('ggplot2')
    print('ggplot2: {0}'.format(ggplot2.as_dict))
    assert(ggplot2.name == 'ggplot2')
    assert(ggplot2.version == '2.2.1')
    assert(ggplot2.license == 'GPL-2 | file LICENSE')
    plyr = localRepo.packinfo('plyr')
    print('plyr: {0}'.format(plyr.as_dict))
    assert(plyr.name == 'plyr')
    assert(plyr.version == '1.8.4')
    assert(plyr.license == 'MIT + file LICENSE')
    assert(plyr.imports == ['Rcpp'])
    assert(plyr.depends == ['R'])
    assert(plyr.suggests == ['abind', 'testthat', 'tcltk',
                             'foreach', 'doParallel',
                             'itertools', 'iterators',
                             'covr'])
