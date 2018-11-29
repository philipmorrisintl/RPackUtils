###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import argparse
import glob
import logging
import os
import sys
import tempfile
import time

from ..config import Config
from ..providers.artifactory import Artifactory
from ..providers.bioconductor import Bioconductor
from ..providers.cran import CRAN
from ..reposconfig import ReposConfig

# logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def rpacks_mirror():
    parser = argparse.ArgumentParser(
        description=('Download R packages from a specified repository '
                     '(CRAN or Bioconductor) and upload them to Artifactory'
                     ' (mirror)'))
    parser.add_argument(
        '--input-repository',
        dest='inputrepo',
        action='store',
        default='',
        help=('The type of public R repository to mirror, '
              'possible values: \"cran\" or \"bioc\"')
    ) and None
    parser.add_argument(
        '--inputrepoparam',
        dest='inputrepoparam',
        action='store',
        default='',
        required=True,
        help='The release of Bioconductor or the snapshot date of CRAN'
    ) and None
    parser.add_argument(
        '--output-repository',
        dest='outputrepo',
        action='store',
        default=None,
        required=True,
        help='The destination Artifactory instance name',
    ) and None
    parser.add_argument(
        '--output-repository-folder',
        dest='outputrepofolder',
        action='store',
        default=None,
        required=True,
        help='The destination Artifactory repository folder name',
    ) and None
    parser.add_argument(
        '--procs',
        dest='procs',
        action='store',
        default='10',
        type=int,
        help='Number of parallel downloads and uploads, default=10',
    ) and None
    parser.add_argument(
        '--config',
        dest='config',
        action='store',
        default=None,
        required=True,
        help='RPackUtils configuration file',
    ) and None
    args = parser.parse_args()
    if args.inputrepo not in ['cran','bioc']:
        logger.error('The specified Input Repository is invalid. ' \
                     'It must be \"cran\" or \"bioc\".')
        sys.exit(-1)
    if not args.inputrepoparam:
        logger.error('Version or snapshot date not provided')
        sys.exit(-1)
    if not args.outputrepo:
        logger.error('Output Repository not provided')
        sys.exit(-1)
    procs = args.procs
    outputrepo = args.outputrepo
    starttime = time.time()
    # read the configuration file
    config = Config(args.config)
    # create the repositories defined there
    reposConfig = ReposConfig(config)
    repository = reposConfig.instance(outputrepo)
    if repository is None:
        logger.error('Exiting due to previous error.')
        exit(-1)
    if not isinstance(repository, Artifactory):
        logger.error('The output repository \"{}\" ' \
                     'is not an Artifactory one.' \
                     .format(repository.name))
        exit(-1)
    # create a temp folder
    dest = tempfile.mkdtemp()
    logger.info("Using the temporary folder " + dest)
    logger.info('I will use {0} parallel processes for ' \
                'parsing, downloads and uploads.' \
                .format(procs))
    mirror = None
    lsargs = None
    packinfoargs = None
    if args.inputrepo == "cran":
        mirror = CRAN()
        snapshot_date = args.inputrepoparam
        # get the list of packages
        packagenames = mirror.ls(snapshot_date, packagenamesonly=True)
        # download them all
        statusDownloads = mirror.download_multiple(snapshot_date,
                                                   packagenames,
                                                   dest, procs)
    if args.inputrepo == 'bioc':
        mirror = Bioconductor()
        bioc_release = args.inputrepoparam
        # get the list of data and packages
        softwarepackages = mirror.ls(
            bioc_release, 'software', procs)
        experimentaldatapackages = mirror.ls(
            bioc_release, 'experimentData', procs)
        annotationdatapackages = mirror.ls(
            bioc_release, 'annotationData', procs)
        # download
        statusDownloads_software = mirror.download_multiple(
            softwarepackages,
            bioc_release, 'software',
            dest, procs)
        statusDownloads_experimentData = mirror.download_multiple(
            experimentaldatapackages,
            bioc_release, 'experimentData',
            dest, procs)
        statusDownloads_annotationData = mirror.download_multiple(
            annotationdatapackages,
            bioc_release, 'annotationData',
            dest, procs)
    # upload them to the output repository (Artifactory)
    filepaths = glob.glob(os.path.join(dest, '*.tar.gz'))
    logger.info('Preparing to upload to the output repository ' \
                '{} ...'.format(repository.name))
    repository.upload_multiple(filepaths, outputrepofolder, procs)
    shutil.rmtree(dest)
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))
