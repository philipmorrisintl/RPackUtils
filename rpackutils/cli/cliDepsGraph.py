###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import argparse
import logging
import time

from networkx.readwrite.gml import literal_stringizer
from networkx.readwrite.gml import write_gml

from ..config import Config
from ..providers.artifactory import Artifactory
from ..providers.bioconductor import Bioconductor
from ..providers.cran import CRAN
from ..providers.localrepository import LocalRepository
from ..providers.renvironment import REnvironment
from ..reposconfig import ReposConfig
from ..tree import DepTree

# logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def rpacks_deps_graph():
    parser = argparse.ArgumentParser(
        description='Generate a dependencies graph')
    parser.add_argument(
        '--repo',
        dest='repo',
        action='store',
        default=None,
        required=True,
        help=('The repository to work with. Identified by '
              'its name in the configuration file. Use \"cran\" or '
              '\"bioc\" to use CRAN or Bioconductor respectively'),
    ) and None
    parser.add_argument(
        '--repoparam',
        dest='repoparam',
        action='store',
        default=None,
        required=False,
        help=('Additional repository parameter. '
              'For Artifactory: \"repo name\"; all defined repositories '
              'will be used otherwise. '
              'Bioconductor: \"release numer, view\" '
              'where \"view\" can be 1 of \"software\", '
              '\"experimentData\", \"annotationData\". '
              'CRAN: \"snapshot date\".')
    ) and None
    parser.add_argument(
        '--packages',
        dest='packages',
        action='store',
        default=None,
        required=False,
        help=('Comma separated list of root packages'
              ' to create the graph, by default all will be included'),
    ) and None
    parser.add_argument(
        '--traverse',
        dest='traverse',
        action='store',
        default='imports,depends',
        required=False,
        help=('By default \"imports,depends\", to traverse both '
              'imports and depends to build the dependency graph. '
              '\"suggests\" is ignored by default.'),
    ) and None
    parser.add_argument(
        '--config',
        dest='config',
        action='store',
        default=None,
        required=False,
        help=('RPackUtils configuration file, required unless '
              'you use CRAN or Bioconductor as repository'),
    ) and None
    parser.add_argument(
        '--out',
        dest='out',
        action='store',
        default=None,
        required=True,
        help='Output file where to write the GML',
    ) and None
    lsargs = None
    packinfoargs = None
    args = parser.parse_args()
    packages = None
    if args.packages is not None:
        packages = [x.strip() for x in args.packages.split(',')]
    repo = args.repo
    repoparam = args.repoparam
    traverse = args.traverse
    out = args.out
    starttime = time.time()
    if repo == 'cran':
        repository = CRAN()
        if args.config is not None:
            logger.warn('Ignoring the --conf argument '
                        'since CRAN will be used.')
    elif repo == 'bioc':
        repository = Bioconductor()
        if args.config is not None:
            logger.warn('Ignoring the --conf argument '
                        'since Bioconductor will be used.')
    else:
        if args.config is None:
            logger.error(
                'Please specify the configuration '
                'file to use with --config')
            exit(-1)
        configFile = args.config
        # read the configuration file
        config = Config(configFile)
        # create the repositories defined there
        reposConfig = ReposConfig(config)
        repository = reposConfig.instance(repo)
    if repository is None:
        logger.error('Exiting due to previous error.')
        exit(-1)
    # for Artifactory we need the repo name
    if isinstance(repository, Artifactory):
        if repoparam is None:
            # logger.error(
            #     'Please specify the Artifactory ' \
            #     'repo/folder to use with --repoparam')
            # exit(-1)
            logger.info('No repository specified for Artifactory, '
                        'using all defined in the configuration file.')
            lsargs = {'repo': None}
            packinfoargs = lsargs
        else:
            lsargs = {'repo': repoparam}
            packinfoargs = lsargs
    # for Bioconductor we need the release number and the view name
    if isinstance(repository, Bioconductor):
        if repoparam is None:
            logger.error(
                'Please specify the Bioconductor '
                'release and view to use with --repoparam')
            exit(-1)
        else:
            repoparams = [x.strip() for x in repoparam.split(',')]
            if not len(repoparams) == 2:
                logger.error(
                    'Please specify the Bioconductor '
                    'release and view to use with '
                    '--repoparam=\"release,view\"')
                exit(-1)
            lsargs = {'bioc_release': repoparams[0],
                      'view': repoparams[1]}
            packinfoargs = lsargs
    # for CRAN we need the snapshot date
    if isinstance(repository, CRAN):
        if repoparam is None:
            logger.error(
                'Please specify the CRAN '
                'snapshot date to use with --repoparam')
            exit(-1)
        else:
            lsargs = {'snapshot_date': repoparam}
            packinfoargs = lsargs
    # for REnvironment or LocalRepository it's fine
    if isinstance(repository, REnvironment) \
       or isinstance(repository, LocalRepository):
        if repoparam is not None:
            logger.warn('Ignoring the --repoparam argument')
    # traverse options (imports, depends, suggests)
    traverse_imports = ('imports' in traverse)
    traverse_depends = ('depends' in traverse)
    traverse_suggests = ('suggests' in traverse)
    # construct the dependencies tree
    dt = DepTree(repository,
                 lsargs,
                 packinfoargs,
                 traverse_imports,
                 traverse_depends,
                 traverse_suggests)
    logger.info('Building the dependencies graph ...')
    dt.build(packagenames=packages)
    if len(dt._g.nodes()) < 2:
        logger.info('The result graph is empty!')
        logger.info('No output file generated')
        exit(1)
    logger.info('The result graph has {} nodes and {} edges'
                .format(len(dt._g.nodes()), len(dt._g.edges())))
    logger.info('Writting output GML file to \"{}\" ...'
                .format(out))
    write_gml(dt._g,
              out,
              stringizer=literal_stringizer)
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))
