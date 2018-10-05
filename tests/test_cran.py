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

from rpackutils.packinfo import PackInfo
from rpackutils.packinfo import PackStatus
from rpackutils.providers.cran import CRAN
from rpackutils.utils import Utils

####################################################################
# ALL TESTS WILL BE SKIPPED IF NO INTERNET CONNECTION IS AVAILABLE #
####################################################################

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

@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_create():
    assert(cran.baseurl == 'https://mran.revolutionanalytics.com')
    assert(cran.repos == [])
    # invalid baseurl
    try:
        CRAN('invalid/baseurl')
        pytest.fail('Using an invalid baseurl must raise an Exception!')
    except Exception:
        pass

@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_mran_snapshots_url():
    assert(cran.mran_snapshots_url == 'https://mran.revolutionanalytics.com/snapshot')

@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_get_mran_packages_url():
    assert(cran.get_mran_packages_url('2018-02-27') == 'https://mran.revolutionanalytics.com/snapshot/2018-02-27/src/contrib/')

@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_get_mran_package_url():
    assert(cran.get_mran_package_url('2018-02-27', 'package_1.2.3.tar.gz') == 'https://mran.revolutionanalytics.com/snapshot/2018-02-27/src/contrib/package_1.2.3.tar.gz')

@pytest.mark.slow
@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_ls_snapshots():
    # full fetch
    cran.ls_snapshots()
    # fetch snapshots for a particular R version
    version2dates_r312 = cran.ls_snapshots(rversion='3.1.2')
    assert(len(version2dates_r312.keys()) == 1)
    assert('3.1.2' in version2dates_r312.keys())
    assert(len(version2dates_r312['3.1.2']) == 129)

@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_ls():
    files = cran.ls('2018-02-27')
    assert(len(files) == 12268)
    assert('ggplotAssist_0.1.3.tar.gz' in files)
    assert('FHtest_1.4.tar.gz' in files)
    assert('heims_0.4.0.tar.gz' in files)

@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_find():
    # locate particular packages
    files = cran.find("ggplotAssist*.tar.gz", '2018-02-27')
    assert(files == ['ggplotAssist_0.1.3.tar.gz'])
    files = cran.find("FHtest*", '2018-02-27')
    assert(files == ['FHtest_1.4.tar.gz'])
    files = cran.find("heims*", '2018-02-27')
    assert(files == ['heims_0.4.0.tar.gz'])

@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_download_single():
    dest = tempfile.mkdtemp()
    # existing package
    retVal = cran.download_single('2018-02-27', 'ggplotAssist', dest)
    assert(retVal == PackStatus.DOWNLOADED)
    # none existing package
    retVal = cran.download_single('2018-02-27',
                                  'foobarzoopackagethatdoesnotexist',
                                  dest)
    assert(retVal == PackStatus.DOWNLOAD_FAILED)
    shutil.rmtree(dest)

@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_download_multiple():
    dest = tempfile.mkdtemp()
    packagenames = ['geecure',
                    'selectiveInference',
                    'HDclassif',
                    'CPBayes',
                    'mozzie']
    retVals = cran.download_multiple('2018-02-27', packagenames, dest, procs=5)
    assert(retVals == [PackStatus.DOWNLOADED,
                       PackStatus.DOWNLOADED,
                       PackStatus.DOWNLOADED,
                       PackStatus.DOWNLOADED,
                       PackStatus.DOWNLOADED])
    for i in range(0, 5):
        assert(
            len(glob.glob(
                os.path.join(
                    dest,
                    "{0}_*.tar.gz".format(packagenames[i])
                )
            )) == 1
        )
    shutil.rmtree(dest)

@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_packinfo():
    pi = cran.packinfo('ggplotAssist', '2018-02-27')
    assert(pi.name == 'ggplotAssist')
    assert(pi.version == '0.1.3')
    assert(pi.license == 'GPL-3')
    assert('R' in pi.depends)
    assert('shiny' in pi.imports)
    assert('miniUI' in pi.imports)
    assert('rstudioapi' in pi.imports)
    assert('shinyWidgets' in pi.imports)
    assert('shinyAce' in pi.imports)
    assert('stringr' in pi.imports)
    assert('tidyverse' in pi.imports)
    assert('ggplot2' in pi.imports)
    assert('dplyr' in pi.imports)
    assert('magrittr' in pi.imports)
    assert('tibble' in pi.imports)
    assert('scales' in pi.imports)
    assert('ggthemes' in pi.imports)
    assert('gcookbook' in pi.imports)
    assert('moonBook' in pi.imports)
    assert('editData' in pi.imports)
    assert('knitr' in pi.suggests)
    assert('rmarkdown' in pi.suggests)
    assert('markdown' in pi.suggests)
