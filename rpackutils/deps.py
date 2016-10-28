import os
import errno
import requests
import sys
import argparse
import subprocess
import tempfile

from .graph import Graph
from .graph import Node
from .repos import RRepository
from .repos import RRepositoryException
from .artifactory import ArtifactoryHelper

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
    def __init__(self):
        self._repos = {}
        self._processed = []
        self._nofound = []
        self._trace = True
        self._fun = None
        self._funargs = {}

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
            self._repos[k] = RRepository(k)

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

    @staticmethod
    def tree(packages, repos=['R-3.1.2', 'Bioc-3.0', 'R-local'], useref=False):
        g = Graph()
        notfound = []
        rrepos = {}
        for repo in repos:
            rrepos[repo] = RRepository(repo)
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

    @staticmethod
    def installpack(n, args):
        rlibpath = args['rlibpath']
        rhome = args['rhome']
        print('====> Instaling package: {0}'.format(n.idt))
        DepsManager._installpack(n, rhome, rlibpath)


    @staticmethod
    def _installpack(n, rhome, rlibpath):
        if rlibpath is not None:
            path = rlibpath
        else:
            path = os.path.join(rhome, 'lib64', 'R', 'library')
        installed = os.listdir(path)
        if n.idt in installed:
            print('Package: {0} already installed'.format(n.idt))
            n.status = PackStatus.INSTALLED
            return
        repo = RRepository(n.reponame)
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
            description='Installing packages based on a list of packages')
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

    args = parser.parse_args()
    repos = [x.strip() for x in args.repos.split(',')]
    rlibpath = args.rlibpath
    rhome = args.rhome
    packages = [x.strip() for x in args.packages.split(',')]
    # Check some parameters
    checkrhome(rhome)
    checkrlibpath(rlibpath)
    welcome(rhome, repos)

    dm = DepsManager()
    dm.repositories = repos
    dm.fun = DepsManager.installpack
    dm.funargs = {'rlibpath': rlibpath, 'rhome': rhome}
    for pack in packages:
        n = PackNode(pack)
        dm.processnode(n)
    if dm.notfound:
        tracenotfound(dm.notfound)



def rpacks_clone():
    parser = argparse.ArgumentParser(
            description='Installing R packages list based on a existing installation')
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

    args = parser.parse_args()
    repos = [x.strip() for x in args.repos.split(',')]
    rlibpath = args.rlibpath
    rhome = args.rhome
    rlibpathref = args.rlibpathref
    # Check some parameters
    checkrhome(rhome)
    checkrlibpath(rlibpath)
    checkrlibpathref(rlibpathref)
    welcome(rhome, repos)
    packages = os.listdir(rlibpathref)
    packages = [x for x in packages]

    dm = DepsManager()
    dm.repositories = repos
    dm.fun = DepsManager.installpack
    dm.funargs = {'rlibpath': rlibpath, 'rhome': rhome}
    for pack in packages:
        n = PackNode(pack)
        dm.processnode(n)
    if dm.notfound:
        tracenotfound(dm.notfound)

    print('Building dependency tree...')
    g, notfound = DepsManager.tree(packages, repos, useref=True)
    tracenotfound(notfound)
    DepsManager.applyfun2graph(g, fun=DepsManager.installpack,
            rhome=rhome, rlibpath=rlibpath)
    showadditionalactions()

def rpacks_query():
    parser = argparse.ArgumentParser(
            description='Query repositories about a package or a list of packages')
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
    args = parser.parse_args()
    repos = [x.strip() for x in args.repos.split(',')]
    packages = [x.strip() for x in args.packages.split(',')]
    if not repos:
        print('Repository is not provided')
        sys.exit(-1)
    if not packages:
        print('No package name provided')
    rrepos = {}
    for repo in repos:
        rrepos[repo] = RRepository(repo)
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
