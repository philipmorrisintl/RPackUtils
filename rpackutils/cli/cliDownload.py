###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import argparse
import logging
import os
import time

from ..config import Config
from ..depsmanager import DepsManager
from ..depsmanager import PackNode
from ..reposconfig import ReposConfig

# logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def rpacks_download():
    parser = argparse.ArgumentParser(
        description=('Install packages to a target R environment '
                     'in dry-run mode'))
    parser.add_argument(
        '--repo',
        dest='reponame',
        action='store',
        default=None,
        help=('The repository name where to get packages '
              '(it must be defined in the configuration file)'),
    ) and None
    parser.add_argument(
        '--Renv',
        dest='renvname',
        action='store',
        default=None,
        help=('Name of the target R environment '
              'where to do the installation '
              '(the name must be defined in the configuration file)'),
    ) and None
    parser.add_argument(
        '--packages',
        dest='packages',
        action='store',
        default=None,
        required=True,
        help='Comma separated package names to install',
    ) and None
    parser.add_argument(
        '--dest',
        dest='dest',
        action='store',
        default=None,
        required=True,
        help=('Path where to store downloaded packages and '
              'the installation script. It must exist.'),
    ) and None
    parser.add_argument(
        '--overwrite',
        dest='overwrite',
        action='store_true',
        default=False,
        required=False,
        help=('Overwrite already installed packages. '
              'By default, nothing gets overwritten.'),
    ) and None
    parser.add_argument(
        '--overwrite-specified',
        dest='overwritespecified',
        action='store_true',
        default=False,
        required=False,
        help=('Overwrite only specified packages (in --packages) '
              'that are already installed. '
              'By default, nothing gets overwritten.'),
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
    overwrite = args.overwrite
    overwritespecified = args.overwritespecified
    configFile = args.config
    starttime = time.time()
    # read the configuration file
    config = Config(configFile)
    # create the repositories defined there
    reposConfig = ReposConfig(config)
    dest = args.dest
    overwritepackages = None
    # check destination folder exists
    if not os.path.exists(dest):
        logger.error('The path \"{}\" does not exist, '
                     'please specify an existing location!'
                     .format(dest))
        exit(-1)
    renvname = args.renvname
    # check the R environemnt
    if renvname not in reposConfig.renvironment_instances:
        logger.error('Could not find any R environment '
                     'with name \"{}\" in the configuration file!'
                     .format(renvname))
        exit(-1)
    renv = reposConfig.renvironment_instance(renvname)
    reponame = args.reponame
    repo = reposConfig.instance(reponame)
    if not repo:
        logger.error('Could not find any repository '
                     'with name \"{}\" in the configuration file!'
                     .format(reponame))
        exit(-1)
    packages = [x.strip() for x in args.packages.split(',')]
    if overwritespecified:
        if overwrite:
            logger.error('Please use only one of '
                         '--overwrite or --overwritespecified, not both.')
            exit(-1)
        overwritepackages = packages
        logger.info('The following packages will be overwritten: '
                    '{}'.format(packages))
    logger.info('Using the target R environment: {} at {}'
                .format(renv.name, renv.baseurl))
    logger.info('Using the package repository: {} at {} with folders: {}'
                .format(repo.name, repo.baseurl, ",".join(repo.repos)))
    dm = DepsManager(
        repo,
        renv.install_dryrun,
        {'dest': dest, 'overwrite': overwrite,
         'overwritepackages': overwritepackages}
    )
    for package in packages:
        n = PackNode(package)
        dm.processnode(n)
    logger.info("============================================================")
    if dm.errors:
        logger.error('Some error(s) occured.')
        if dm.notfound:
            logger.error('Some packages were not found: {}'
                         .format(str(dm.notfound)))
        if dm.downloadfailed:
            logger.error('Some packages could not be downloaded: {}'
                         .format(str(dm.downloadfailed)))
    logger.info('Packages: {} processed | {} errors '
                '({} not found, {} download failed)'
                .format(len(dm.processed),
                        len(dm.errors),
                        len(dm.notfound),
                        len(dm.downloadfailed)))
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))
