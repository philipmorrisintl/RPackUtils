###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import argparse
import logging
import time

from ..json_serializer import JSONSerializer
from ..providers.cran import CRAN

# logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def rpacks_mran():
    parser = argparse.ArgumentParser(
        description='Query the MRAN repository for available snapshots')
    parser.add_argument(
        '--Rversion',
        dest='rversion',
        action='store',
        default=None,
        help=('The version of R, as \"x.y.z\" '
              '(ignored when --restore is used)'),
    ) and None
    parser.add_argument(
        '--procs',
        dest='procs',
        action='store',
        default='50',
        type=int,
        help=('Number of parallel processes used to parse '
              'snapshots properties, default=50'),
    ) and None
    parser.add_argument(
        '--dump',
        dest='dumpfilepath',
        action='store',
        default=None,
        help='a file where to dump the results',
    ) and None
    parser.add_argument(
        '--restore',
        dest='restorefromfilepath',
        action='store',
        default=None,
        help='a file where to read the results from',
    ) and None
    args = parser.parse_args()
    if args.dumpfilepath is not None and args.restorefromfilepath is not None:
        logger.error("Please choose either dump or restore, "
                     "they are exclusive!")
        exit(-1)
    snapshots = None
    starttime = time.time()
    if args.restorefromfilepath is None:
        logger.info("I will use {0} parallel processes to parse "
                    "the R version from snapshots dates."
                    .format(args.procs))
        logger.info("Fetching available MRAN snapshots from the Internet...")
        cran = CRAN()
        snapshots = cran.ls_snapshots(args.procs, args.rversion)
    else:
        if args.rversion is not None:
            logger.warn('Ignoring the --Rversion parameter '
                        'since --restore is used.')
        if args.procs is not None:
            logger.warn('Ignoring the --procs parameter '
                        'since --restore is used.')
        logger.info("Reading available MRAN snapshots "
                    "from {0}...".format(args.restorefromfilepath))
        snapshots = JSONSerializer.deserializefromfile(
            args.restorefromfilepath)
    logger.info("============================================================")
    for version in snapshots.keys():
        logger.info("R version {0}, {1} snapshots\n"
                    "----------------------------------------"
                    "\n{2}\n"
                    .format(version,
                            len(snapshots[version]),
                            " ".join(snapshots[version])))
    logger.info("============================================================")
    if args.dumpfilepath is not None:
        JSONSerializer.serialize2file(snapshots, args.dumpfilepath)
        logger.info("Results dumped to {0}.".format(args.dumpfilepath))
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))
