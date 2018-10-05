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
import json
import pytest
from unittest import mock
from unittest.mock import patch

from networkx.algorithms.dag import descendants
from networkx.readwrite.gml import write_gml
from networkx.readwrite.gml import literal_stringizer
    
from rpackutils.providers.cran import CRAN
from rpackutils.providers.bioconductor import Bioconductor
from rpackutils.packinfo import PackInfo
from rpackutils.packinfo import PackStatus
from rpackutils.tree import DepTree
from rpackutils.providers.localrepository import LocalRepository
from rpackutils.providers.renvironment import REnvironment
from rpackutils.providers.artifactory import Artifactory
from rpackutils.utils import Utils
from rpackutils.config import Config

LOCALREPO_BASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'resources/R')

# LOCALREPO_LIBS = os.path.join(
#     os.path.dirname(os.path.abspath(__file__)),
#     'resources/R/library')

LOCALREPO_LIBS = 'library'

REPOFULLPATH = Utils.concatpaths(LOCALREPO_BASE, LOCALREPO_LIBS)

GML = os.path.join(tempfile.gettempdir(),
                   'RPackUtils_deps_graph.gml')

configfilepath = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'resources/rpackutils.conf')

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


# Bioconductor
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


@pytest.fixture(scope="module")
def cleanup(request):
    def teardown():
        for root, dirs, files in os.walk(REPOFULLPATH, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        try:
            os.remove(GML)
        except OSError:
            pass
    request.addfinalizer(teardown)


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


@patch('rpackutils.providers.Artifactory._do_request')
def create(mock_do_request):
    mock_do_request.return_value = MockResponse(200, "Ok")
    config = Config(configfilepath)
    arti = Artifactory(baseurl=config.get("artifactory", "baseurl"),
                       repos=['R-3.1.2', 'R-local'],
                       auth=(config.get("artifactory", "user"),
                             config.get("artifactory", "password")),
                       verify=config.get("artifactory", "verify"))
    # arti = Artifactory(baseurl=config.get("artifactory-pmi", "baseurl"),
    #                    repos=['R-3.1.2', 'R-local'],
    #                    auth=(config.get("artifactory-pmi", "user"),
    #                          config.get("artifactory-pmi", "password")),
    #                    verify=config.get("artifactory-pmi", "verify"))
    return arti

######################################################################
######################################################################


@pytest.mark.slow
@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_build_dependencies_graph_from_local_packages_repository(cleanup):
    # step 1: download packages from MRAN, a particular snapshot of CRAN
    packagenames = ["ggplot2", "data.table", "plyr", "knitr", "shiny", "xts",
                    "lattice", "digest", "gtable", "reshape2", "scales",
                    "proto", "MASS", "Rcpp", "stringr", "RColorBrewer",
                    "dichromat", "munsell", "labeling", "colorspace",
                    "evaluate", "formatR", "highr", "markdown", "mime",
                    "httpuv", "caTools", "RJSONIO", "xtable", "htmltools",
                    "bitops", "zoo", "SparseM", "survival", "Formula",
                    "latticeExtra", "cluster", "maps", "sp", "foreign",
                    "mvtnorm", "TH.data", "sandwich", "nlme", "Matrix", "bit",
                    "codetools", "iterators", "timeDate", "quadprog", "Hmisc",
                    "BH", "quantreg", "mapproj", "hexbin", "maptools",
                    "multcomp", "testthat", "mgcv", "chron", "reshape",
                    "fastmatch", "bit64", "abind", "foreach", "doMC",
                    "itertools", "testit", "rgl", "XML", "RCurl", "Cairo",
                    "timeSeries", "tseries", "fts", "tis", "KernSmooth", "R6",
                    "acepack", "stringi", "praise", "cli", "glue",
                    "htmlwidgets", "crayon", "yaml", "quantmod", "magrittr",
                    "MatrixModels", "jsonlite"]
    cran.download_multiple('2018-02-27',
                           packagenames,
                           dest=REPOFULLPATH,
                           procs=10)
    # step 2: create a local repository for these downloaded packages
    localRepo = LocalRepository(
        LOCALREPO_BASE,
        [LOCALREPO_LIBS]
    )
    assert(localRepo.baseurl == LOCALREPO_BASE)
    assert(localRepo.repos == [LOCALREPO_LIBS])
    # step 3: create a dependencies graph
    print('Building dependencies graph...')
    lsargs = {'packagenamesonly': True}
    dt = DepTree(localRepo,
                 lsargs)
    dt.build()
    assert(len(dt._g.nodes()) > 0)
    assert(len(dt._g.edges()) > 0)
    print('Generating graph...')
    write_gml(dt._g,
              GML,
              stringizer=literal_stringizer)
    assert(os.path.exists(GML))


@pytest.mark.slow
@pytest.mark.skipif(
    not cran_is_available(),
    reason="MRAN is not available (https://mran.revolutionanalytics.com)"
)
def test_build_dependencies_graph_from_cran(cleanup):
    version2dates = cran.ls_snapshots(rversion='3.2.5')
    print('Building dependencies graph...')
    # select the first snapshot date in the list for R-3.2.5
    lsargs = {'snapshot_date': version2dates['3.2.5'][0]}
    packinfoargs = lsargs
    dt = DepTree(cran,
                 lsargs,
                 packinfoargs)
    dt.build(packagenames=['chromoR'])
    assert(len(dt._g.nodes()) > 0)
    assert(len(dt._g.edges()) > 0)
    print('Generating graph...')
    write_gml(dt._g,
              GML,
              stringizer=literal_stringizer)
    assert(os.path.exists(GML))


def test_build_dependencies_graph_from_renvironment(cleanup):
    RHOME = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources/R-fake-env')
    LIBRARYPATH = 'packages'
    renv = REnvironment(
        RHOME,
        LIBRARYPATH
    )
    assert(renv.baseurl == RHOME)
    assert(renv.repos == [LIBRARYPATH])
    print('Building dependencies graph...')
    lsargs = {'packagenamesonly': True}
    dt = DepTree(renv,
                 lsargs)
    dt.build()
    assert(len(dt._g.nodes()) > 0)
    assert(len(dt._g.edges()) > 0)
    print('Generating graph...')
    write_gml(dt._g,
              GML,
              stringizer=literal_stringizer)
    assert(os.path.exists(GML))


@pytest.mark.skipif(
    not bioc_is_available(),
    reason="BioConductor is not available (https://www.bioconductor.org)"
)
def test_build_dependencies_graph_from_bioc(cleanup):
    print('Building dependencies graph...')
    lsargs = {'bioc_release': '3.3',
              'view': 'software'}
    packinfoargs = lsargs
    dt = DepTree(bioc,
                 lsargs,
                 packinfoargs)
    dt.build(packagenames=['RGraph2js'])
    assert(len(dt._g.nodes()) > 0)
    assert(len(dt._g.edges()) > 0)
    print('Generating graph...')
    write_gml(dt._g,
              GML,
              stringizer=literal_stringizer)
    assert(os.path.exists(GML))


def test_build_dependencies_graph_from_artifactory(cleanup):
    pass
    # artifactory = create()
    # print('Building dependencies graph...')
    # lsargs = {'repo': 'R-3.1.2'}
    # packinfoargs = lsargs
    # dt = DepTree(artifactory,
    #              lsargs,
    #              packinfoargs=None)
    # dt.build(packagenames=['whisker'])
    # assert(len(dt._g.nodes()) == 1)
    # assert(len(dt._g.edges())== 0)
    # print('Generating graph...')
    # write_gml(dt._g,
    #           GML,
    #           stringizer=literal_stringizer)
    # assert(os.path.exists(GML))
