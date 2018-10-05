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
from unittest import mock
from unittest.mock import patch

from rpackutils.packinfo import PackInfo
from rpackutils.packinfo import PackStatus
from rpackutils.providers.renvironment import REnvironment
from rpackutils.utils import Utils

RHOME = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'resources/R-fake-env')

LIBRARYPATH = 'packages'

RHOME_INVALID = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'resources/R')

RPACKAGE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'resources/FooBar_0.99.1.tar.gz')


def test_create():
    renv = REnvironment(RHOME, LIBRARYPATH)
    assert(renv.baseurl == RHOME)
    assert(renv.repos == [LIBRARYPATH])
    # invalid baseurl
    try:
        renv = REnvironment(
            '/invalid/local/repobase',
            LIBRARYPATH
        )
        pytest.fail('Constructing a REnvironment with '
                    'an invalid baseurl/rhome must raise an Exception!')
    except Exception:
        pass
    # invalid repos
    try:
        renv = REnvironment(
            RHOME,
            'invalid1'
        )
        pytest.fail('Constructing a REnvironment with '
                    'an invalid library path must raise an Exception!')
    except Exception:
        pass
    # no R file in the bin folder
    try:
        renv = REnvironment(
            RHOME_INVALID,
            'library'
        )
        pytest.fail(
            'Constructing a REnvironment which '
            'does not contain any R binary file must raise an Exception!')
    except Exception:
        pass


def test_find():
    renv = REnvironment(RHOME, LIBRARYPATH)
    # findall
    findall = renv.find('*')
    assert(len(findall) == 6)
    assert('energy' in findall)
    assert('entropy' in findall)
    assert('evaluate' in findall)
    assert('fake1' in findall)
    assert('faraway' in findall)
    assert('fastcluster' in findall)
    # find something that does not exist
    assert(len(renv.find('*.tar.gz')) == 0)


def test_ls():
    renv = REnvironment(RHOME, LIBRARYPATH)
    packagenames = renv.ls()
    assert(len(packagenames) == 5)
    assert('energy' in packagenames)
    assert('entropy' in packagenames)
    assert('evaluate' in packagenames)
    assert('faraway' in packagenames)
    assert('fastcluster' in packagenames)


def test_download_single():
    renv = REnvironment(RHOME, LIBRARYPATH)
    destfolder = tempfile.mkdtemp()
    try:
        renv.download_single('energy', destfolder)
        pytest.fail('The download method must raise an exception!')
    except Exception:
        pass


@patch('rpackutils.providers.renvironment.REnvironment._installpackage')
def test_upload_single(mock_installpackage):
    renv = REnvironment(RHOME, LIBRARYPATH)
    # none existing package
    status = renv.upload_single(
        '/none/existent/path/to/some/none/existent/package.tar.gz')
    assert(status == PackStatus.DEPLOY_FAILED)
    # existing package
    mock_installpackage.return_value = (0, "Ok", None)
    status = renv.upload_single(RPACKAGE)
    assert(status == PackStatus.DEPLOYED)
    # set the unused argument
    status = renv.upload_single(RPACKAGE, repo='fakerepo')
    assert(status == PackStatus.DEPLOYED)
    # overwrite
    status = renv.upload_single(RPACKAGE, overwrite=True)
    assert(status == PackStatus.DEPLOYED)
    # failed installation
    mock_installpackage.return_value = (1, "not Ok", "Could not install")
    status = renv.upload_single(RPACKAGE)
    assert(status == PackStatus.DEPLOY_FAILED)


def test_packinfo():
    renv = REnvironment(RHOME, LIBRARYPATH)
    # existing package
    energy = renv.packinfo('energy')
    print('energy: {0}'.format(energy.as_dict))
    assert(energy.name == 'energy')
    assert(energy.version == '1.6.2')
    assert(energy.license == 'GPL (>= 2)')
    assert(energy.imports == ['boot'])
    # none existing package
    foobar = renv.packinfo('foobar')
    assert(foobar.status == PackStatus.NOT_FOUND)
    # invalid package
    try:
        renv.packinfo('fake1')
        pytest.fail('Passing a folder without any DESCRIPTION file '
                    'must raise an exception!')
    except Exception:
        pass
