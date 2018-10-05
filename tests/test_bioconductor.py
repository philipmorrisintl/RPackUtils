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
from rpackutils.providers.bioconductor import Bioconductor
from rpackutils.utils import Utils

####################################################################
# ALL TESTS WILL BE SKIPPED IF NO INTERNET CONNECTION IS AVAILABLE #
####################################################################

bioc = None
try:
    bioc = Bioconductor()
except Exception as e:
    pass


def bioc_is_available():
    if bioc is not None:
        return bioc.check_connection(numtries=1)
    else:
        return False


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_create():
    assert(bioc.baseurl == 'https://www.bioconductor.org')
    assert(bioc.repos == [])
    # invalid baseurl
    try:
        Bioconductor('invalid/baseurl')
        pytest.fail('Using an invalid baseurl must raise an Exception!')
    except Exception:
        pass


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_bioc_chkres_url():
    assert(bioc.bioc_chkres_url == 'https://www.bioconductor.org/checkResults')


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_bioc_possible_views():
    assert('software' in bioc.bioc_possible_views)
    assert('experimentData' in bioc.bioc_possible_views)
    assert('annotationData' in bioc.bioc_possible_views)


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_get_bioc_software_url():
    assert(
        bioc.get_bioc_software_url('3.0') ==
        'https://www.bioconductor.org/packages/json/3.0/bioc/packages.js'
    )


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_get_bioc_experimentdata_url():
    assert(
        bioc.get_bioc_experimentdata_url('3.0') ==
        'https://www.bioconductor.org/packages/json/3.0/data/experiment/packages.js'
    )


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_get_bioc_annotationdata_url():
    assert(
        bioc.get_bioc_annotationdata_url('3.0') ==
        'https://www.bioconductor.org/packages/json/3.0/data/annotation/packages.js'
    )


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_get_bioc_software_page_url():
    assert(
        bioc.get_bioc_software_page_url('3.3', 'RGraph2js') ==
        'https://www.bioconductor.org/packages/3.3/bioc/html/RGraph2js.html'
    )


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_get_bioc_experimentaldata_page_url():
    assert(
        bioc.get_bioc_experimentaldata_page_url('3.3', 'RGraph2js') ==
        'https://www.bioconductor.org/packages/3.3/data/experiment/html/RGraph2js.html'
    )


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_get_bioc_annotationdata_page_url():
    assert(
        bioc.get_bioc_annotationdata_page_url('3.3', 'RGraph2js') ==
        'https://www.bioconductor.org/packages/3.3/data/annotation/html/RGraph2js.html'
    )


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_get_bioc_download_software_url():
    assert(
        bioc.get_bioc_download_software_url('3.3', 'RGraph2js') ==
        'https://www.bioconductor.org/packages/3.3/bioc/src/contrib/RGraph2js.tar.gz'
    )


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_get_bioc_download_experimentaldata_url():
    assert(
        bioc.get_bioc_download_experimentaldata_url('3.3', 'RGraph2js') ==
        'https://www.bioconductor.org/packages/3.3/data/experiment/src/contrib/RGraph2js.tar.gz'
    )


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_get_bioc_download_annotationdata_url():
    assert(
        bioc.get_bioc_download_annotationdata_url('3.3', 'RGraph2js') ==
        'https://www.bioconductor.org/packages/3.3/data/annotation/src/contrib/RGraph2js.tar.gz'
    )


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_get_full_package_name():
    packagename = 'RGraph2js'
    retVal = bioc._get_full_package_name('3.3', 'software', packagename)
    assert(retVal['status'] == 'ok')
    assert(retVal['name'] == 'RGraph2js')
    assert(retVal['full_package_name'] == 'RGraph2js_1.0.0')


@pytest.mark.slow
@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_ls():
    files = bioc.ls('3.0', 'software')
    assert('Genominator' in files)
    assert('CNAnorm' in files)
    assert('EnrichmentBrowser' in files)
    assert('xcms' in files)
    assert('PSEA' in files)
    files = bioc.ls('3.0', 'experimentData')
    assert('gageData' in files)
    assert('parathyroidSE' in files)
    files = bioc.ls('3.0', 'annotationData')
    assert('rat2302cdf' in files)


@pytest.mark.slow
@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_find():
    files = bioc.find('prot2D*', '3.0', 'software')
    assert(len(files) == 1)
    assert(files[0] == 'prot2D')
    files = bioc.find('gageData*', '3.0', 'experimentData')
    assert(len(files) == 1)
    assert(files[0] == 'gageData')
    files = bioc.find('rat2302cdf*', '3.0', 'annotationData')
    assert(len(files) == 1)
    assert(files[0] == 'rat2302cdf')


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_download_single():
    dest = tempfile.mkdtemp()
    # existing package
    retVal = bioc.download_single('prot2D', '3.0', 'software', dest)
    assert(retVal == PackStatus.DOWNLOADED)
    # none existing package
    retVal = bioc.download_single('noneexistingpackage', '3.0', 'software', dest)
    assert(retVal == PackStatus.DOWNLOAD_FAILED)
    shutil.rmtree(dest)


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_download_multiple():
    dest = tempfile.mkdtemp()
    packagenames = ['Genominator',
                    'CNAnorm',
                    'EnrichmentBrowser',
                    'xcms',
                    'PSEA']
    retVals = bioc.download_multiple(packagenames,
                                     '3.0',
                                     'software',
                                     dest,
                                     procs=5)
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


@pytest.mark.slow
@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_packinfo():
    # software
    pi = bioc.packinfo('prot2D', '3.0', 'software')
    assert(pi.name == 'prot2D')
    assert(pi.version == '1.4.0')
    assert(pi.license == 'GPL (>= 2)')
    assert('R' in pi.depends)
    assert('fdrtool' in pi.depends)
    assert('st' in pi.depends)
    assert('samr' in pi.depends)
    assert('Biobase' in pi.depends)
    assert('limma' in pi.depends)
    assert('Mulcom' in pi.depends)
    assert('impute' in pi.depends)
    assert('MASS' in pi.depends)
    assert('qvalue' in pi.depends)
    assert('made4' in pi.suggests)
    assert('affy' in pi.suggests)
    assert(pi.imports == [])
    # experimentData
    pi = bioc.packinfo('yeastCC', '3.0', 'experimentData')
    assert(pi.version == '1.5.1')
    # annotationData
    pi = bioc.packinfo('ricecdf', '3.0', 'annotationData')
    assert(pi.version == '2.15.0')
