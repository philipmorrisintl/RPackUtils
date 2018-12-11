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
import shutil

from ..config import Config
from ..providers.artifactory import Artifactory
from ..providers.bioconductor import Bioconductor
from ..providers.localrepository import LocalRepository
from ..providers.cran import CRAN
from ..reposconfig import ReposConfig
from ..utils import Utils

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
              'possible values: \"cran\", \"bioc\" '
              'or the name of a Local repository')
    ) and None
    parser.add_argument(
        '--inputrepoparam',
        dest='inputrepoparam',
        action='store',
        default='',
        required=False,
        help='The release of Bioconductor or the snapshot date of CRAN'
    ) and None
    parser.add_argument(
        '--biocview',
        dest='biocview',
        action='store',
        default='all',
        required=False,
        help=('When mirroring Bioconductor only: specify the view: '
              '\"software\", \"experimentData\", \"annotationData\" '
              'or by default: \"all\"')
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
        '--dest',
        dest='dest',
        action='store',
        default=None,
        required=False,
        help=('Path where to store downloaded packages. '
              'It must exist. A temp folder will be used otherwise.'),
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
    if args.inputrepo in ['cran', 'bioc'] and not args.inputrepoparam:
        logger.error('Version or snapshot date not provided')
        sys.exit(-1)
    if not args.outputrepo:
        logger.error('Output Repository not provided')
        sys.exit(-1)
    procs = args.procs
    outputrepo = args.outputrepo
    dest = args.dest
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
        logger.error('The output repository \"{}\" '
                     'is not an Artifactory one.'
                     .format(repository.name))
        exit(-1)
    # check destination folder exists
    if dest is not None:
        if not os.path.exists(dest):
            logger.error('The path \"{}\" does not exist, '
                         'please specify an existing location!'
                         .format(dest))
            exit(-1)
    else:
        # create a temp folder
        dest = tempfile.mkdtemp()
    logger.info("Using the temporary folder " + dest)
    logger.info('I will use {0} parallel processes for '
                'parsing, downloads and uploads.'
                .format(procs))
    mirror = None
    # lsargs = None
    # packinfoargs = None
    filepaths = []
    if args.inputrepo == "cran":
        mirror = CRAN()
        snapshot_date = args.inputrepoparam
        # get the list of packages
        packagenames = mirror.ls(snapshot_date, packagenamesonly=True)
        # download them all
        statusDownloads = mirror.download_multiple(snapshot_date,
                                                   packagenames,
                                                   dest, procs)
        filepaths = glob.glob(os.path.join(dest, '*.tar.gz'))
    if args.inputrepo == 'bioc':
        mirror = Bioconductor()
        bioc_release = args.inputrepoparam
        if(args.biocview == 'all' or args.biocview == 'software'):
            softwarepackages = mirror.ls(
                bioc_release, 'software', procs)
            statusDownloads_software = mirror.download_multiple(
                softwarepackages,
                bioc_release, 'software',
                dest, procs)
        if(args.biocview == 'all' or args.biocview == 'experimentData'):
            experimentaldatapackages = mirror.ls(
                bioc_release, 'experimentData', procs)
            statusDownloads_experimentData = mirror.download_multiple(
                experimentaldatapackages,
                bioc_release, 'experimentData',
                dest, procs)
        if(args.biocview == 'all' or args.biocview == 'annotationData'):
            annotationdatapackages = mirror.ls(
                bioc_release, 'annotationData', procs)
            statusDownloads_annotationData = mirror.download_multiple(
                annotationdatapackages,
                bioc_release, 'annotationData',
                dest, procs)
        filepaths = glob.glob(os.path.join(dest, '*.tar.gz'))
    if args.inputrepo not in ['cran', 'bioc']:
        inputrepository = reposConfig.instance(args.inputrepo)
        if inputrepository is None:
            logger.error('Exiting due to previous error.')
            exit(-1)
        if not isinstance(inputrepository, LocalRepository):
            logger.error('The input repository \"{}\" '
                         'is not a LocalRepository one.'
                         .format(repository.name))
            exit(-1)
        ifiles = inputrepository.ls()
        ibaseurl = inputrepository.baseurl
        filepaths = [Utils.concatpaths(ibaseurl, f) for f in ifiles]
    if filepaths:
        # upload them to the output repository (Artifactory)
        logger.info('Preparing to upload {} packages '
                    'to the output repository '
                    '{} ...'.format(len(filepaths), repository.name))
        repository.upload_multiple(filepaths, args.outputrepofolder, procs)
    else:
        logger.error('No package found in the '
                     '{} repository.'.format(args.inputrepo))
    shutil.rmtree(dest)
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))
