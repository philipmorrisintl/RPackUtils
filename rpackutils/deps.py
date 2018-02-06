###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import errno
import requests
import sys
import argparse
import subprocess
import tempfile
import multiprocessing
import time

from .graph import Graph
from .graph import Node
from .repos import RRepository
from .repos import RRepositoryException
from .artifactory import ArtifactoryHelper

ARTIFACTORY_CONFIG_HELP = "File specifying the Artifactroy configuration.\n" \
    "Sample content:\n" \
    "\n" \
    "[global]\n" \
    "artifactory.url = \"https://artifactoryhost/artifactory\"" \
    "artifactory.user = \"artiuser\"" \
    "artifactory.pwd = \"***\"" \
    "artifactory.cert = \"Certificate_Chain.pem\""

base_packages = [
            'R',
            'utils',
            'mgcv',
            'foreign',
            'survival',
            'tcltk',
            'translations',
            'cluster',
            'MASS',
            'grDevices',
            'nlme',
            'grid',
            'base',
            'compiler',
            'KernSmooth',
            'class',
            'spatial',
            'boot',
            'tools',
            'lattice',
            'nnet',
            'graphics',
            'methods',
            'codetools',
            'stats4',
            'rpart',
            'datasets',
            'stats',
            'splines',
            'parallel',
            'Matrix',
        ]

def enum(**enums):
    return type('Enum', (), enums)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


PackStatus = enum(
        UNKNOWN=-1,
        PARSED=0,
        DOWNLOADED=1,
        DOWNLOAD_FAILED=2,
        INSTALLED=3,
        INSTALLATION_FAILED=4)


class PackNode(Node):
    def __init__(self, idt):
        super(PackNode, self).__init__(idt)
        self._version = None
        self._status = None
        self._packurl = None
        self.reponame = None

    @property
    def packurl(self):
        return self._packurl

    @packurl.setter
    def packurl(self, v):
        self._packurl = v

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, v):
        self._version = v

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, v):
        self._status = v

    @property
    def reponame(self):
        return self._reponame

    @reponame.setter
    def reponame(self, v):
        self._reponame = v

    def __str__(self):
        return ('{0} - {1} - {2} - {3}'.format(
            self.idt, self.version, self.status, self.reponame))

class DepsManager(object):
    def __init__(self, artifactoryConfig=None):
        self._repos = {}
        self._processed = []
        self._nofound = []
        self._trace = True
        self._fun = None
        self._funargs = {}
        self._artifactoryConfig = artifactoryConfig

    @property
    def fun(self):
        return self._fun

    @fun.setter
    def fun(self, v):
        self._fun = v

    @property
    def notfound(self):
        return self._nofound

    @property
    def trace(self):
        return self._trace

    @trace.setter
    def trace(self, v):
        self._trace = v

    @property
    def funargs(self):
        return self._funargs

    @funargs.setter
    def funargs(self, v):
        self._funargs = v

    @property
    def repositories(self):
        return self._repos.keys()

    @repositories.setter
    def repositories(self, v):
        for r in v:
            k = r.strip()
            self._repos[k] = RRepository(k, self._artifactoryConfig)

    def repopack(self, p):
        for repo in self._repos:
            if p in self._repos[repo].packages:
                return repo
        return None

    def processnode(self, node):
        if node.idt in base_packages and self._trace:
            print('Package: {0} already installed'.format(node.idt))
            return
        if node.idt in self._nofound:
            if self._trace:
                print('Package: {0} was not found'.format(node.idt))
                return

        if not node.idt in self._processed:
            repo = self.repopack(node.idt)
            if repo is None:
                if self._trace:
                    print('Package: {0} was not found'.format(node.idt))
                self._nofound.append(node.idt)
                return
            _, version, deps = self._repos[repo].description(node.idt)
            node.version = version
            node.packurl = self._repos[repo].packurl(node.idt)
            node.reponame = repo
            deps = [x for x in deps if x not in base_packages]
            
            for dep in deps:
                depnode = PackNode(dep)
                self.processnode(depnode)
                
            print('Processing node: {0}...'.format(node.idt))
            self._fun(node, self._funargs)
            self._processed.append(node.idt)

    @staticmethod
    def applyfun2graph(g, fun=None, *a, **k):
        for idt in g.nodesidts:
            #print('Processing: {0}...'.format(idt))
            n = g.node(idt)
            DepsManager.applyfun2node(n, fun=fun, *a, **k)

    @staticmethod
    def applyfun2node(n, fun=None, *a, **k):
        for childidt in n.connections:
            child = n.node(childidt)
            DepsManager.applyfun2node(child, fun=fun, *a, **k)
        fun(n, *a, **k)

    def tree(self, packages, repos=['R-3.1.2', 'Bioc-3.0', 'R-local'], useref=False):
        g = Graph()
        notfound = []
        rrepos = {}
        for repo in repos:
            rrepos[repo] = RRepository(repo, self._artifactoryConfig)
        for pack in packages:
            print('----------------------------------------------------------')
            print('Processing package: {0}'.format(pack))
            found = False
            if pack in base_packages:
                #print('Ignoring base package: {0}'.format(pack))
                continue
            for repo in repos:
                rrepo = rrepos[repo]
                if pack in rrepo.packages:
                    packname, version, deps = rrepos[repo].description(pack)
                    print('Package: {0}, version: {1} found in repos: {2}'.format(
                        pack, version, repo))
                    packurl = rrepos[repo].packurl(pack)
                    reponame = repo
                    found = True
            if found:
                node = PackNode(packname)
                node.version = version
                node.status = PackStatus.PARSED
                node.packurl = packurl
                node.reponame = reponame
                if not packname in base_packages:
                    g.addnode(node)
                for dep in deps:
                    if not dep in base_packages:
                        if not dep in g.nodesidts:
                            depnode = PackNode(dep)
                            for repo in repos:
                                rrepo = rrepos[repo]
                                if dep in rrepo.packages:
                                    depname, version, _ = rrepos[repo].description(dep)
                                    print('Dep: {0}, version: {1} found in repos: {2}'.format(
                                        dep, version, repo))
                                    packurl = rrepos[repo].packurl(dep)
                            depnode.version = version
                            depnode.packurl = packurl
                            depnode.reponame = reponame
                            depnode.status = PackStatus.PARSED
                            g.addnode(depnode)
                            if not useref:
                                packages.append(dep)
                        g.connect(node.idt, dep, 1)
            else:
                notfound.append(pack)
        return g, notfound

    def download(self, n, args):
        # print('====> Downloading package: {0}'.format(n.idt))
        if args['with_r_cmd']:
            if args['rlibpath'] is not None:
                lib_path_cmd = '--library {0}'.format(args['rlibpath'])
            else:
                lib_path_cmd = ''
            if args['prefix'] is None:
                prefix = ''
            else:
                prefix = args['prefix']
            cmd_filepath = os.path.join(args['dest'], 'install.sh')
            if os.path.exists(cmd_filepath):
                f = open(cmd_filepath, 'a+')
            else:
                f = open(cmd_filepath, 'x')
            cmd = '{0} CMD INSTALL {1} {2}'.format(
                os.path.join(args['rhome'], 'bin', 'R'),
                lib_path_cmd,
                os.path.join(prefix, '{0}_{1}.tar.gz'.format(
                    n.idt, n.version))
            )
            f.write(cmd)
            f.write('\n')
            f.close()
        repo = RRepository(n.reponame)
        filepath = repo.download(n.idt, os.path.join(args['dest'],
                '{0}_{1}.tar.gz'.format(n.idt, n.version)))
        if os.path.exists(filepath):
            n.status = PackStatus.DOWNLOADED
        else:
            n.status = PackStatus.DOWNLOAD_FAILED
            print('Failed to download package: {0}'.format(
                n.idt))
            sys.exit(-1)
        

    def installpack(self, n, args):
        rlibpath = args['rlibpath']
        rhome = args['rhome']
        print('====> Instaling package: {0}'.format(n.idt))
        self._installpack(n, rhome, rlibpath)

    def _installpack(self, n, rhome, rlibpath):
        if rlibpath is not None:
            path = rlibpath
        else:
            path = os.path.join(rhome, 'lib64', 'R', 'library')
        installed = os.listdir(path)
        if n.idt in installed:
            print('Package: {0} already installed'.format(n.idt))
            n.status = PackStatus.INSTALLED
            return
        repo = RRepository(n.reponame, self._artifactoryConfig)
        filepath = repo.download(n.idt)
        if os.path.exists(filepath):
            n.status = PackStatus.DOWNLOADED
        else:
            n.status = PackStatus.DOWNLOAD_FAILED
            print('Failed to download package: {0}'.format(
                n.idt))
            sys.exit(-1)

        cmd = "{0}/bin/R CMD INSTALL {1}".format(
                rhome,
                filepath,
                )
        res = subprocess.call(cmd, shell=True)
        if res != 0:
            n.status = PackStatus.INSTALLATION_FAILED
            print('Installation FAILED for: {0}'.format(n.idt))
        else:
            n.status = PackStatus.INSTALLED
        os.remove(filepath)


def checkrhome(rhome):
    if not os.path.exists(rhome):
        print('No R installation found at: {0}'.format(
            rhome))
        sys.exit(-1)
    if not os.path.exists(os.path.join(rhome, 'bin', 'R')):
        print('Invalid R-home: {0}'.format(
            rhome))
        sys.exit(-1)

def checkrlibpath(path):
    if path is not None:
        print('Installing packages in library: {0}'.format(path))
        if not os.path.exists(path):
            print((
                'Specified location for packages',
                'destination: {0} does not exist').format(path))

def checkrlibpathref(path):
    if path is not None:
        print('Using reference library path: {0}'.format(path))
        if not os.path.exists(path):
            print((
                'Specified location for packages',
                'reference: {0} does not exist').format(path))

def welcome(rhome, repos):
    print('Using R: {0}'.format(rhome))
    print('Using Repositories: {0}'.format(repos))

def tracenotfound(notfound):
    if notfound:
        print('They are package that are not found:')
        #print('\n'.join('{}: {}'.format(*k) for k in enumerate(notfound)))
        print(str(notfound))

def showadditionalactions():
    print('Add HPC certificate to RCurl installation')

def rpacks_install():
    parser = argparse.ArgumentParser(
            description='Install packages based on a list of packages')
    parser.add_argument(
            '--repositories',
            dest='repos',
            action='store',
            default='R-3.1.2,Bioc-3.0,R-local,R-Data-0.1',
            help='Comma separated list of repositories. Default are: R-3.1.2, Bioc-3.0, R-local,R-Data-0.1',
            ) and None
    parser.add_argument(
            '--R-lib-path',
            dest='rlibpath',
            action='store',
            default=None,
            help='Path to the R library path where to install packages',
            ) and None
    parser.add_argument(
            '--R-home',
            dest='rhome',
            action='store',
            default=None,
            help='Path to the R installation to use for installing',
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
            '--config',
            dest='artifactoryConfig',
            action='store',
            default=None,
            required=True,
            help=ARTIFACTORY_CONFIG_HELP,
            ) and None
    
    args = parser.parse_args()
    repos = [x.strip() for x in args.repos.split(',')]
    rlibpath = args.rlibpath
    rhome = args.rhome
    packages = [x.strip() for x in args.packages.split(',')]
    artifactoryConfig = None
    if args.artifactoryConfig is not None:
        artifactoryConfig = args.artifactoryConfig
    # Check some parameters
    checkrhome(rhome)
    checkrlibpath(rlibpath)
    welcome(rhome, repos)

    dm = DepsManager(artifactoryConfig)
    dm.repositories = repos
    dm.fun = dm.installpack
    dm.funargs = {'rlibpath': rlibpath, 'rhome': rhome}
    for pack in packages:
        n = PackNode(pack)
        dm.processnode(n)
    if dm.notfound:
        tracenotfound(dm.notfound)

def rpacks_clone():
    parser = argparse.ArgumentParser(
            description='Install R packages based on an existing environments (clone)')
    parser.add_argument(
            '--repositories',
            dest='repos',
            action='store',
            default='R-3.1.2,Bioc-3.0,R-local,R-Data-0.1',
            help='Comma separated list of repositories. Default are: R-3.1.2, Bioc-3.0, R-local,R-Data-0.1',
            ) and None
    parser.add_argument(
            '--R-lib-path',
            dest='rlibpath',
            action='store',
            default=None,
            help='Path to the R library path where to install packages',
            ) and None
    parser.add_argument(
            '--R-home',
            dest='rhome',
            action='store',
            default=None,
            help='Path to the installation to use',
            ) and None
    parser.add_argument(
            '--R-lib-refpath',
            dest='rlibpathref',
            action='store',
            default=None,
            help='Path to the R library path used as reference',
            ) and None
    parser.add_argument(
            '--config',
            dest='artifactoryConfig',
            action='store',
            default=None,
            required=True,
            help=ARTIFACTORY_CONFIG_HELP,
            ) and None

    args = parser.parse_args()
    repos = [x.strip() for x in args.repos.split(',')]
    rlibpath = args.rlibpath
    rhome = args.rhome
    rlibpathref = args.rlibpathref
    artifactoryConfig = None
    if args.artifactoryConfig is not None:
        artifactoryConfig = args.artifactoryConfig
    # Check some parameters
    checkrhome(rhome)
    checkrlibpath(rlibpath)
    checkrlibpathref(rlibpathref)
    welcome(rhome, repos)
    packages = os.listdir(rlibpathref)
    packages = [x for x in packages]

    dm = DepsManager(artifactoryConfig)
    dm.repositories = repos
    dm.fun = dm.installpack
    dm.funargs = {'rlibpath': rlibpath, 'rhome': rhome}
    for pack in packages:
        n = PackNode(pack)
        dm.processnode(n)
    if dm.notfound:
        tracenotfound(dm.notfound)

    print('Building dependency tree...')
    g, notfound = dm.tree(packages, repos, useref=True)
    tracenotfound(notfound)
    DepsManager.applyfun2graph(g, fun=dm.installpack,
            rhome=rhome, rlibpath=rlibpath)
    showadditionalactions()

def rpacks_query():
    parser = argparse.ArgumentParser(
            description='Search accross repositories for a package or a list of packages')
    parser.add_argument(
            '--repositories',
            dest='repos',
            action='store',
            default='R-3.1.2,Bioc-3.0,R-local,R-Data-0.1',
            help='Comma separated list of repositories. Default are: R-3.1.2, Bioc-3.0, R-local,R-Data-0.1',
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
            '--config',
            dest='artifactoryConfig',
            action='store',
            default=None,
            required=True,
            help=ARTIFACTORY_CONFIG_HELP,
            ) and None
    args = parser.parse_args()
    repos = [x.strip() for x in args.repos.split(',')]
    packages = [x.strip() for x in args.packages.split(',')]
    artifactoryConfig = None
    if args.artifactoryConfig is not None:
        artifactoryConfig = args.artifactoryConfig
    if not repos:
        print('Repository is not provided')
        sys.exit(-1)
    if not packages:
        print('No package name provided')
    rrepos = {}
    for repo in repos:
        rrepos[repo] = RRepository(repo, artifactoryConfig)
    for pack in packages:
        found = False
        for repo in repos:
            rrepo = rrepos[repo]
            if pack in rrepo.packages:
                found = True
                packname, version, deps = rrepos[repo].description(pack)
                print('-------------------------------------')
                print('Package: {0}  Version: {1} in repository: {2}'.format(
                    pack, version, repo))
                print('Depends on: {0}'.format(str(deps)))
        if not found:
                print('-------------------------------------')
                print('Package: {0} not found in repositories: {1}'.format(
                    pack, str(repos)))

def rpacks_download():
    parser = argparse.ArgumentParser(
            description=('Download R packages and resolved dependencies'))
    parser.add_argument(
            '--repositories',
            dest='repos',
            action='store',
            default='R-3.1.2,Bioc-3.0,R-local,R-Data-0.1',
            help='Comma separated list of repositories. Default are: R-3.1.2, Bioc-3.0, R-local,R-Data-0.1',
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
            '--config',
            dest='artifactoryConfig',
            action='store',
            default=None,
            required=True,
            help=ARTIFACTORY_CONFIG_HELP,
            ) and None
    parser.add_argument(
            '--with-R-cmd',
            dest='with_r_cmd',
            action='store_true',
            default=None,
            required=False,
            help='Print to the console the R command to install them',
            ) and None
    parser.add_argument(
            '--R-home',
            dest='rhome',
            action='store',
            default=None,
            help='Path to the installation to use',
            ) and None
    parser.add_argument(
            '--R-lib-path',
            dest='rlibpath',
            action='store',
            default=None,
            required=True,
            help='Path to the R library path where to install packages',
            ) and None
    parser.add_argument(
            '--prefix',
            dest='prefix',
            action='store',
            default=None,
            help='Path to the location where R packages have been downloaded', 
            ) and None
    parser.add_argument(
            '--dest',
            dest='dest',
            action='store',
            default=None,
            help=('Path to the folder where packages are downloaded. If not'
                  'provided, working folder will be used.'), 
            ) and None
    args = parser.parse_args()
    if args.with_r_cmd is not None and args.rhome is None:
        print('You must specify the --R-home when using --with-R-cmd')
        sys.exit(-1)
    repos = [x.strip() for x in args.repos.split(',')]
    packages = [x.strip() for x in args.packages.split(',')]
    artifactoryConfig = None
    dest = args.dest
    if args.dest is None:
        dest = os.getcwd()
    if args.artifactoryConfig is not None:
        artifactoryConfig = args.artifactoryConfig
    if not repos:
        print('Repository is not provided')
        sys.exit(-1)
    dm = DepsManager(artifactoryConfig)
    dm.repositories = repos
    dm.fun = dm.download
    dm.funargs = {'rlibpath': args.rlibpath, 'rhome': args.rhome,
                  'with_r_cmd': args.with_r_cmd, 'prefix': args.prefix,
                  'dest': dest}
    starttime = time.time()
    for pack in packages:
        node = PackNode(pack)
        dm.processnode(node)
    endtime = time.time()
    timeelapsed = int(endtime - starttime)
    print('Time elapsed: {0} seconds.'.format(timeelapsed))
    if dm.notfound:
        tracenotfound(dm.notfound)
