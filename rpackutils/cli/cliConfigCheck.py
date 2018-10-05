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
from ..reposconfig import ReposConfig

# logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def rpacks_config_check():
    parser = argparse.ArgumentParser(
        description=('Check the configuration file '
                     'and report issues if any'))
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
    starttime = time.time()
    logger.info('Checking the configuration file...')
    # read the configuration file
    config = Config(configFile)
    # create the repositories defined there
    reposConfig = ReposConfig(config)
    # get all repository instances
    reposConfig.repository_instances
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))
