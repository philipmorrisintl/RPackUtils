###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import argparse
import logging
import time

from ..config import Config
from ..depsmanager import DepsManager
from ..depsmanager import PackNode
from ..reposconfig import ReposConfig

# logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def rpacks_clone():
    parser = argparse.ArgumentParser(
        description=('Install R packages based on '
                     'an existing environments (clone)'))
    parser.add_argument(
        '--repo',
        dest='reponame',
        action='store',
        default=None,
        help=('The repository name where to get packages '
              '(it must be defined in the configuration file)'),
    ) and None
    parser.add_argument(
        '--Renvin',
        dest='renvnameinput',
        action='store',
        default=None,
        help=('Name of the input R environment '
              '(the name must be defined in the configuration file)'),
    ) and None
    parser.add_argument(
        '--Renvout',
        dest='renvnameoutput',
        action='store',
        default=None,
        help=('Name of the target R environment '
              'where to do the installation '
              '(the name must be defined in the configuration file)'),
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
        '--config',
        dest='config',
        action='store',
        default=None,
        required=True,
        help='RPackUtils configuration file',
    ) and None
    args = parser.parse_args()
    configFile = args.config
    overwrite = args.overwrite
    starttime = time.time()
    # read the configuration file
    config = Config(configFile)
    # create the repositories defined there
    reposConfig = ReposConfig(config)
    # validate
    # renvnameinput
    renvnameinput = args.renvnameinput
    if renvnameinput not in reposConfig.renvironment_instances:
        logger.error('Could not find any R environment '
                     'with name \"{}\" in the configuration file!'
                     .format(renvnameinput))
        exit(-1)
    renvinput = reposConfig.renvironment_instance(renvnameinput)
    # renvnameoutput
    renvnameoutput = args.renvnameoutput
    if renvnameoutput not in reposConfig.renvironment_instances:
        logger.error('Could not find any R environment '
                     'with name \"{}\" in the configuration file!'
                     .format(renvnameoutput))
        exit(-1)
    renvoutput = reposConfig.renvironment_instance(renvnameoutput)
    # validate repo
    reponame = args.reponame
    repo = reposConfig.instance(reponame)
    if not repo:
        logger.error('Could not find any repository '
                     'with name \"{}\" in the configuration file!'
                     .format(reponame))
        exit(-1)
    logger.info('Using the source/input R environment: {} at {}'
                .format(renvinput.name, renvinput.baseurl))
    logger.info('Using the destination/output R environment: {} at {}'
                .format(renvoutput.name, renvoutput.baseurl))
    logger.info('Using the package repository: {} at {} with folders: {}'
                .format(repo.name, repo.baseurl, ",".join(repo.repos)))
    # get the list of installed packages in the input R environment
    packagenames = renvinput.ls(packagenamesonly=True, withBasePackages=False)
    logger.info('Number of none-base packages installed on {}: {}'
                .format(renvinput.name, len(packagenames)))
    if(len(packagenames) == 0):
        logger.info('Nothing to do! Could not find any none-base package '
                    'installed on the input R environment.')
        exit(-1)
    dm = DepsManager(
        repo,
        renvoutput.install,
        {'overwrite': overwrite}
    )
    for packagename in packagenames:
        n = PackNode(packagename)
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
