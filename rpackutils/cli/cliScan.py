###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import argparse
import csv
import logging
import time

from ..config import Config
from ..reposconfig import ReposConfig

# logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def rpacks_scan():
    parser = argparse.ArgumentParser(
        description='Scan a repository or an R environment')
    parser.add_argument(
        '--repos',
        dest='repos',
        action='store',
        default=None,
        required=True,
        help=('Comma separated repository names, '
              'use \"all\": to specify all defined in the configuration file'),
    ) and None
    parser.add_argument(
        '--config',
        dest='config',
        action='store',
        default=None,
        required=True,
        help='RPackUtils configuration file',
    ) and None
    parser.add_argument(
        '--out',
        dest='out',
        action='store',
        default=None,
        required=True,
        help='Output file where to write the CSV',
    ) and None
    args = parser.parse_args()
    repos = [x.strip() for x in args.repos.split(',')]
    out = args.out
    starttime = time.time()
    configFile = args.config
    # read the configuration file
    config = Config(configFile)
    # create the repositories defined there
    reposConfig = ReposConfig(config)
    repositories = []
    if repos == ['all']:
        repositories = reposConfig.repository_instances
    else:
        repositories = reposConfig.repository_instances_by_name(repos)
    # scan all available R packages accross specified repositories
    _scan_packages(repositories, out)
    logger.info('Writting output CSV file to \"{}\" ...'
                .format(out))
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))


def _scan_packages(repositories, out):
    # TODO: we could launch multi processes
    with open(out, 'w', newline='') as csvfile:
        fieldnames = ['Name', 'Version', 'License', 'License class',
                      'Depends', 'Imports', 'Suggests',
                      'Installation allowed', 'Installation warning']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        logger.info('-------------------------------------')
        logger.info('{0} repositories(s) specified'.format(len(repositories)))
        for repo in repositories:
            candidates = repo.ls(packagenamesonly=True)
            logger.info('Repository instance \"{0}\"'
                        .format(repo.name))
            logger.info('{0} package(s) found'.format(len(candidates)))
            for idx, candidate in enumerate(candidates):
                logger.info('-')
                packinfo = repo.packinfo(candidate)
                logger.info('{} / {} Done'.format(idx+1, len(candidates)))
                writer.writerow({
                    'Name': packinfo.name,
                    'Version': packinfo.version,
                    'License': packinfo.license,
                    'License class': packinfo.licenseclass,
                    'Depends': ",".join(packinfo.dependslist),
                    'Imports': ",".join(packinfo.importslist),
                    'Suggests': ",".join(packinfo.suggestslist),
                    'Installation allowed': packinfo.installation_is_allowed,
                    'Installation warning': packinfo.installation_warning
                })
                logger.info('-')
        logger.info('-------------------------------------')
