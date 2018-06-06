###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import glob
import errno
import sys
import argparse
import tempfile
import time
import logging
from networkx.algorithms.dag import descendants
from networkx.readwrite.gml import write_gml
from networkx.readwrite.gml import literal_stringizer

from .config import Config
from .reposconfig import ReposConfig
from .packinfo import PackInfo
from .packinfo import PackStatus
from .provider import AbstractREnvironment
from .providers.artifactory import Artifactory
from .providers.bioconductor import Bioconductor
from .providers.cran import CRAN
from .providers.localrepository import LocalRepository
from .providers.renvironment import REnvironment
from .json_serializer import JSONSerializer
from .tree import DepTree
from .depsmanager import PackNode
from .depsmanager import DepsManager

# logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def rpacks_query():
    parser = argparse.ArgumentParser(
        description='Search accross repositories for ' \
        'a package or a list of packages')
    parser.add_argument(
        '--repos',
        dest='repos',
        action='store',
        default='all',
        required=False,
        help='Comma separated repository names, ' \
        'by default: all defined in the configuration file',
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
            logger.info('Searching for {} in {}...' \
                        .format(package, repo.name))
            candidates = []
            if(isinstance(repo, AbstractREnvironment)):
                candidates = repo.find('{0}'.format(package))
            else:
                candidates = repo.find('{0}_*.tar.gz'.format(package))
            logger.info('-')
            logger.info('Repository instance \"{0}\"' \
                        .format(repo.name))
            logger.info('{0} matche(s) found'.format(len(candidates)))
            for candidate in candidates:
                logger.info('-')
                packinfo = repo.packinfo(candidate)
                logger.info(
                    'Package: {0} ' \
                    'Version: {1} ' \
                    'License: {2} ' \
                    .format(packinfo.name,
                            packinfo.version,
                            packinfo.license))
                logger.info('Repository path: {0}' \
                            .format(candidate))
                logger.info('Depends: {}' \
                            .format(",".join(packinfo.dependslist)))
                logger.info('Imports: {}' \
                            .format(",".join(packinfo.importslist)))
                logger.info('Suggests: {}' \
                            .format(",".join(packinfo.suggestslist)))
                # logger.info('Dependencies: {0}' \
                #             .format(",".join(packinfo.dependencies())))
        logger.info('-------------------------------------')

def rpacks_bioc():
    parser = argparse.ArgumentParser(
        description='Query the Bioconductor repository ' \
        'for available releases')
    args = parser.parse_args()
    starttime = time.time()
    bioc = Bioconductor()
    releases = bioc.ls_releases()
    for release in releases:
        logger.info(release)
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))

def rpacks_mran():
    parser = argparse.ArgumentParser(
        description='Query the MRAN repository for available snapshots')
    parser.add_argument(
        '--Rversion',
        dest='rversion',
        action='store',
        default=None,
        help='The version of R, as \"x.y.z\" ' \
        '(ignored when --restore is used)',
    ) and None
    parser.add_argument(
        '--procs',
        dest='procs',
        action='store',
        default='50',
        type=int,
        help='Number of parallel processes used to parse ' \
        'snapshots properties, default=50',
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
        logger.error("Please choose either dump or restore, " \
                     "they are exclusive!")
        exit(-1)
    snapshots = None
    starttime = time.time()
    if args.restorefromfilepath is None:
        logger.info("I will use {0} parallel processes to parse " \
                    "the R version from snapshots dates." \
              .format(args.procs))
        logger.info("Fetching available MRAN snapshots from the Internet...")
        cran = CRAN()
        snapshots = cran.ls_snapshots(args.procs, args.rversion)
    else:
        if args.rversion is not None:
            logger.warn('Ignoring the --Rversion parameter ' \
                        'since --restore is used.')
        if args.procs is not None:
            logger.warn('Ignoring the --procs parameter ' \
                        'since --restore is used.')
        logger.info("Reading available MRAN snapshots " \
                    "from {0}...".format(args.restorefromfilepath))
        snapshots = JSONSerializer.deserializefromfile(args.restorefromfilepath)
    logger.info("============================================================")
    for version in snapshots.keys():
        logger.info("R version {0}, {1} snapshots\n"\
                    "----------------------------------------" \
                    "\n{2}\n" \
                    .format(version,
                            len(snapshots[version]),
                            " ".join(snapshots[version])))
    logger.info("============================================================")
    if args.dumpfilepath is not None:
        JSONSerializer.serialize2file(snapshots, args.dumpfilepath)
        logger.info("Results dumped to {0}.".format(args.dumpfilepath))
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))

def rpacks_deps_graph():
    parser = argparse.ArgumentParser(
        description='Generate a dependencies graph')
    parser.add_argument(
        '--repo',
        dest='repo',
        action='store',
        default=None,
        required=True,
        help='The repository to work with. Identified by ' \
        'its name in the configuration file. Use \"cran\" or ' \
        '\"bioc\" to use CRAN or Bioconductor respectively',
    ) and None
    parser.add_argument(
        '--repoparam',
        dest='repoparam',
        action='store',
        default=None,
        required=False,
        help='Additional repository parameter. ' \
        'For Artifactory: \"repo name\"; all defined repositories ' \
        'will be used otherwise. ' \
        'Bioconductor: \"release numer, view\" ' \
        'where \"view\" can be 1 of \"software\", ' \
        '\"experimentData\", \"annotationData\". ' \
        'CRAN: \"snapshot date\".'
    ) and None
    parser.add_argument(
        '--packages',
        dest='packages',
        action='store',
        default=None,
        required=False,
        help='Comma separated list of root packages' \
        ' to create the graph, by default all will be included',
    ) and None
    parser.add_argument(
        '--traverse',
        dest='traverse',
        action='store',
        default='imports,depends',
        required=False,
        help='By default \"imports,depends\", to traverse both ' \
        'imports and depends to build the dependency graph. ' \
        '\"suggests\" is ignored by default.',
    ) and None
    parser.add_argument(
        '--config',
        dest='config',
        action='store',
        default=None,
        required=False,
        help='RPackUtils configuration file, required unless ' \
        'you use CRAN or Bioconductor as repository',
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
            logger.warn('Ignoring the --conf argument ' \
                        'since CRAN will be used.')
    elif repo == 'bioc':
        repository = Bioconductor()
        if args.config is not None:
            logger.warn('Ignoring the --conf argument ' \
                        'since Bioconductor will be used.')
    else:
        if args.config is None:
            logger.error(
                'Please specify the configuration ' \
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
            logger.info('No repository specified for Artifactory, ' \
                        'using all defined in teh configuration file.')
            lsargs = {'repo': None}
            packinfoargs = lsargs
        else:
            lsargs = {'repo': repoparam}
            packinfoargs = lsargs
    # for Bioconductor we need the release number and teh view name
    if isinstance(repository, Bioconductor):
        if repoparam is None:
            logger.error(
                'Please specify the Bioconductor ' \
                'release and view to use with --repoparam')
            exit(-1)
        else:
            repoparams = [x.strip() for x in repoparam.split(',')]
            if not len(repoparams) == 2:
                logger.error(
                    'Please specify the Bioconductor ' \
                    'release and view to use with --repoparam=\"release,view\"')
                exit(-1)
            lsargs = {'bioc_release': repoparams[0],
                      'view': repoparams[1]}
            packinfoargs = lsargs
    # for CRAN we need the snapshot date
    if isinstance(repository, CRAN):
        if repoparam is None:
            logger.error(
                'Please specify the CRAN ' \
                'spanshot date to use with --repoparam')
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
    logger.info('The result graph has {} nodes and {} edges' \
                .format(len(dt._g.nodes()), len(dt._g.edges())))
    logger.info('Writting output GML file to \"{}\" ...' \
                .format(out))
    write_gml(dt._g,
              out,
              stringizer=literal_stringizer)
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))

def rpacks_mirror():
    parser = argparse.ArgumentParser(
        description='Download R packages from a specified repository ' \
        '(CRAN or Bioconductor) and upload them to Artifactory (mirror)')
    parser.add_argument(
        '--input-repository',
        dest='inputrepo',
        action='store',
        default='',
        help='The type of public R repository to mirror, ' \
        'possible values: \"cran\" or \"bioc\"',
    ) and None
    parser.add_argument(
        '--inputrepoparam',
        dest='inputrepoparam',
        action='store',
        default='',
        required=True,
        help='The release of Bioconductor or the snapshot date of CRAN',
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

def rpacks_install():
    parser = argparse.ArgumentParser(
        description='Install packages to a target R environment')
    parser.add_argument(
        '--repo',
        dest='reponame',
        action='store',
        default=None,
        help='The repository name where to get packages ' \
        '(it must be defined in the configuration file)',
    ) and None
    parser.add_argument(
        '--Renv',
        dest='renvname',
        action='store',
        default=None,
        help='Name of the target R environment ' \
        'where to do the installation ' \
        '(the name must be defined in the configuration file)',
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
        '--overwrite',
        dest='overwrite',
        action='store_true',
        default=False,
        required=False,
        help=('Overwrite already installed packages. ' \
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
    configFile = args.config
    starttime = time.time()
    # read the configuration file
    config = Config(configFile)
    # create the repositories defined there
    reposConfig = ReposConfig(config)
    renvname = args.renvname
    # check the R environemnt
    if not renvname in reposConfig.renvironment_instances:
        logger.error('Could not find any R environment ' \
                     'with name \"{}\" in the configuration file!' \
                     .format(renvname))
        exit(-1)
    renv = reposConfig.renvironment_instance(renvname)
    reponame = args.reponame
    repo = reposConfig.instance(reponame)
    if not repo:
        logger.error('Could not find any repository ' \
                     'with name \"{}\" in the configuration file!' \
                     .format(reponame))
        exit(-1)
    packages = [x.strip() for x in args.packages.split(',')]
    logger.info('Using the target R environment: {} at {}' \
                .format(renv.name, renv.baseurl))
    logger.info('Using the package repository: {} at {} with folders: {}' \
                .format(repo.name, repo.baseurl, ",".join(repo.repos)))
    dm = DepsManager(
        repo,
        renv.install,
        {'overwrite': overwrite}
    )
    for package in packages:
        n = PackNode(package)
        dm.processnode(n)
    logger.info("============================================================")
    if dm.errors:
        logger.error('Some error(s) occured.')
        if dm.notfound:
            logger.error('Some packages were not found: {}' \
                         .format(str(dm.notfound)))
        if dm.downloadfailed:
            logger.error('Some packages could not be downloaded: {}' \
                         .format(str(dm.downloadfailed)))
    logger.info('Packages: {} processed | {} errors ' \
                '({} not found, {} download failed)' \
                .format(len(dm.processed),
                        len(dm.errors),
                        len(dm.notfound),
                        len(dm.downloadfailed)
                )
    )
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))

def rpacks_clone():
    parser = argparse.ArgumentParser(
        description='Install R packages based on an existing environments (clone)')
    parser.add_argument(
        '--repo',
        dest='reponame',
        action='store',
        default=None,
        help='The repository name where to get packages ' \
        '(it must be defined in the configuration file)',
    ) and None
    parser.add_argument(
        '--Renvin',
        dest='renvnameinput',
        action='store',
        default=None,
        help='Name of the input R environment ' \
        '(the name must be defined in the configuration file)',
    ) and None
    parser.add_argument(
        '--Renvout',
        dest='renvnameoutput',
        action='store',
        default=None,
        help='Name of the target R environment ' \
        'where to do the installation ' \
        '(the name must be defined in the configuration file)',
    ) and None
    parser.add_argument(
        '--overwrite',
        dest='overwrite',
        action='store_true',
        default=False,
        required=False,
        help=('Overwrite already installed packages. ' \
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
    if not renvnameinput in reposConfig.renvironment_instances:
        logger.error('Could not find any R environment ' \
                     'with name \"{}\" in the configuration file!' \
                     .format(renvnameinput))
        exit(-1)
    renvinput = reposConfig.renvironment_instance(renvnameinput)
    # renvnameoutput
    renvnameoutput = args.renvnameoutput
    if not renvnameoutput in reposConfig.renvironment_instances:
        logger.error('Could not find any R environment ' \
                     'with name \"{}\" in the configuration file!' \
                     .format(renvnameoutput))
        exit(-1)
    renvoutput = reposConfig.renvironment_instance(renvnameoutput)
    # validate repo
    reponame = args.reponame
    repo = reposConfig.instance(reponame)
    if not repo:
        logger.error('Could not find any repository ' \
                     'with name \"{}\" in the configuration file!' \
                     .format(reponame))
        exit(-1)
    logger.info('Using the source/input R environment: {} at {}' \
                .format(renvinput.name, renvinput.baseurl))
    logger.info('Using the destination/output R environment: {} at {}' \
                .format(renvoutput.name, renvoutput.baseurl))
    logger.info('Using the package repository: {} at {} with folders: {}' \
                .format(repo.name, repo.baseurl, ",".join(repo.repos)))
    # get the list of installed packages in the input R environment
    packagenames = renvinput.ls(packagenamesonly=True, withBasePackages=False)
    logger.info('Number of none-base packages installed on {}: {}' \
                .format(renvinput.name, len(packagenames)))
    if(len(packagenames) == 0):
        logger.info('Nothing to do! Could not find any none-base package ' \
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
            logger.error('Some packages were not found: {}' \
                         .format(str(dm.notfound)))
        if dm.downloadfailed:
            logger.error('Some packages could not be downloaded: {}' \
                         .format(str(dm.downloadfailed)))
    logger.info('Packages: {} processed | {} errors ' \
                '({} not found, {} download failed)' \
                .format(len(dm.processed),
                        len(dm.errors),
                        len(dm.notfound),
                        len(dm.downloadfailed)
                )
    )
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))

def rpacks_download():
    parser = argparse.ArgumentParser(
        description='Install packages to a target R environment in dry-run mode')
    parser.add_argument(
        '--repo',
        dest='reponame',
        action='store',
        default=None,
        help='The repository name where to get packages ' \
        '(it must be defined in the configuration file)',
    ) and None
    parser.add_argument(
        '--Renv',
        dest='renvname',
        action='store',
        default=None,
        help='Name of the target R environment ' \
        'where to do the installation ' \
        '(the name must be defined in the configuration file)',
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
        help=('Path where to store downloaded packages and ' \
              'the installation script. It must exist.'),
    ) and None
    parser.add_argument(
        '--overwrite',
        dest='overwrite',
        action='store_true',
        default=False,
        required=False,
        help=('Overwrite already installed packages. ' \
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
    configFile = args.config
    starttime = time.time()
    # read the configuration file
    config = Config(configFile)
    # create the repositories defined there
    reposConfig = ReposConfig(config)
    dest = args.dest
    # check destination folder exists
    if not os.path.exists(dest):
        logger.error('The path \"{}\" does not exist, ' \
                     'please specify an existing location!'
                     .format(dest))
        exit(-1)
    renvname = args.renvname
    # check the R environemnt
    if not renvname in reposConfig.renvironment_instances:
        logger.error('Could not find any R environment ' \
                     'with name \"{}\" in the configuration file!' \
                     .format(renvname))
        exit(-1)
    renv = reposConfig.renvironment_instance(renvname)
    reponame = args.reponame
    repo = reposConfig.instance(reponame)
    if not repo:
        logger.error('Could not find any repository ' \
                     'with name \"{}\" in the configuration file!' \
                     .format(reponame))
        exit(-1)
    packages = [x.strip() for x in args.packages.split(',')]
    logger.info('Using the target R environment: {} at {}' \
                .format(renv.name, renv.baseurl))
    logger.info('Using the package repository: {} at {} with folders: {}' \
                .format(repo.name, repo.baseurl, ",".join(repo.repos)))
    dm = DepsManager(
        repo,
        renv.install_dryrun,
        {'dest': dest, 'overwrite': overwrite}
    )
    for package in packages:
        n = PackNode(package)
        dm.processnode(n)
    logger.info("============================================================")
    if dm.errors:
        logger.error('Some error(s) occured.')
        if dm.notfound:
            logger.error('Some packages were not found: {}' \
                         .format(str(dm.notfound)))
        if dm.downloadfailed:
            logger.error('Some packages could not be downloaded: {}' \
                         .format(str(dm.downloadfailed)))
    logger.info('Packages: {} processed | {} errors ' \
                '({} not found, {} download failed)' \
                .format(len(dm.processed),
                        len(dm.errors),
                        len(dm.notfound),
                        len(dm.downloadfailed)
                )
    )
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))

def rpacks_config_check():
    parser = argparse.ArgumentParser(
        description='Check the configuration file ' \
        'and report issues if any')
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
    repositories = reposConfig.repository_instances
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))
