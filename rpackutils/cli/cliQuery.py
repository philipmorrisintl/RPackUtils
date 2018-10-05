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
from ..provider import AbstractREnvironment
from ..reposconfig import ReposConfig

# logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def rpacks_query():
    parser = argparse.ArgumentParser(
        description=('Search accross repositories for '
                     'a package or a list of packages'))
    parser.add_argument(
        '--repos',
        dest='repos',
        action='store',
        default='all',
        required=False,
        help=('Comma separated repository names, '
              'by default: all defined in the configuration file'),
    ) and None
    parser.add_argument(
        '--packages',
        dest='packages',
        action='store',
        default=None,
        required=True,
        help='Comma separated package names to search',
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
    packages = [x.strip() for x in args.packages.split(',')]
    repos = [x.strip() for x in args.repos.split(',')]
    configFile = args.config
    if not packages:
        logger.error('No package name provided')
        exit(-1)
    starttime = time.time()
    # read the configuration file
    config = Config(configFile)
    # create the repositories defined there
    reposConfig = ReposConfig(config)
    repositories = []
    if repos == ['all']:
        repositories = reposConfig.repository_instances
    else:
        repositories = reposConfig.repository_instances_by_name(repos)
    # search accross all defined repositories
    _query_packages(repositories, packages)
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))


def _query_packages(repositories, packages):
    for package in packages:
        logger.info('-------------------------------------')
        for repo in repositories:
            logger.info('Searching for {} in {}...'
                        .format(package, repo.name))
            candidates = []
            if(isinstance(repo, AbstractREnvironment)):
                candidates = repo.find('{0}'.format(package))
            else:
                candidates = repo.find('{0}_*.tar.gz'.format(package))
            logger.info('-')
            logger.info('Repository instance \"{0}\"'
                        .format(repo.name))
            logger.info('{0} matche(s) found'.format(len(candidates)))
            for candidate in candidates:
                logger.info('-')
                packinfo = repo.packinfo(candidate)
                logger.info(
                    'Package: {0} '
                    'Version: {1} '
                    'License: {2} '
                    .format(packinfo.name,
                            packinfo.version,
                            packinfo.license))
                logger.info('Repository path: {0}'
                            .format(candidate))
                logger.info('Depends: {}'
                            .format(",".join(packinfo.dependslist)))
                logger.info('Imports: {}'
                            .format(",".join(packinfo.importslist)))
                logger.info('Suggests: {}'
                            .format(",".join(packinfo.suggestslist)))
                # logger.info('Dependencies: {0}' \
                #             .format(",".join(packinfo.dependencies())))
        logger.info('-------------------------------------')
