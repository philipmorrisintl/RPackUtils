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
import shutil
import tempfile
import multiprocessing
import time
import logging

from .config import Config
# from .reposconfig import ReposConfig
from .packinfo import PackInfo
from .packinfo import PackStatus
from .graph import Graph
from .graph import Node
from .rbasepackages import RBasePackages
from .provider import AbstractPackageRepository
from .provider import AbstractREnvironment
from .providers.artifactory import Artifactory
from .providers.localrepository import LocalRepository

logger = logging.getLogger(__name__)


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
        return ('{} - {} - {} - {}'.format(
            self.idt, self.version, self.status, self.reponame))


class DepsManager(object):
    def __init__(self, repo, fun=None, funargs=None):
        self._repo = repo
        self._processed = []
        self._notfound = []
        self._downloadfailed = []
        self._fun = fun
        self._funargs = funargs
        assert(self._repoIsSupported(),
               'Only Artifactory or LocalRepository '
               'instances are supported!')

    def _repoIsSupported(self):
        return(
            isinstance(self._repo, AbstractPackageRepository)
            and (
                isinstance(self._repo, Artifactory)
                or
                isinstance(self._repo, LocalRepository)
            )
        )

    @property
    def fun(self):
        return self._fun

    # @fun.setter
    # def fun(self, v):
    #     self._fun = v

    @property
    def processed(self):
        return self._processed

    @property
    def errors(self):
        return self._notfound + self._downloadfailed

    @property
    def notfound(self):
        return self._notfound

    @property
    def downloadfailed(self):
        return self._downloadfailed

    @property
    def funargs(self):
        return self._funargs

    # @funargs.setter
    # def funargs(self, v):
    #     self._funargs = v

    def _removePackInfoTempDir(self, packinfo):
        if hasattr(packinfo, 'tempdir') \
           and packinfo.tempdir \
           and os.path.exists(packinfo.tempdir):
            shutil.rmtree(packinfo.tempdir)

    def processnode(self, node):
        if node.idt in RBasePackages.getnames():
            logger.info(
                'Package: {} is already installed '
                '(part of the base packages)'
                .format(node.idt))
            return
        if node.idt in self._notfound:
            logger.error('Package \"{}\" was not found!'
                         .format(node.idt))
            return
        if node.idt not in self._processed:
            # the most recent version will be taken
            # from the repository "repo"
            #
            # we keep the temp files
            packinfo = self._repo.packinfo(packagename=node.idt,
                                           keeptempfiles=True)
            if(packinfo is None):
                logger.error('Package \"{}\" was not found!'
                             .format(node.idt))
                self._notfound.append(node.idt)
                self._removePackInfoTempDir(packinfo)
                return
            if(packinfo.status == PackStatus.NOT_FOUND):
                logger.error('Package \"{}\" was not found!'
                             .format(node.idt))
                self._notfound.append(node.idt)
                self._removePackInfoTempDir(packinfo)
                return
            if(packinfo.status == PackStatus.DOWNLOAD_FAILED):
                logger.error('Failed to download package \"{}\"!'
                             .format(node.idt))
                self._downloadfailed.append(node.idt)
                self._removePackInfoTempDir(packinfo)
                return
            node.version = packinfo.version
            node.packagepath = packinfo.packagepath
            deps = packinfo.dependencies(withBasePackages=False)
            for dep in deps:
                depnode = PackNode(dep)
                self.processnode(depnode)
            logger.info('Processing node: {}...'.format(node.idt))
            if(self._funargs is not None):
                self._fun(node, **self._funargs)
            else:
                self._fun(node)
            # we remove the temp files
            self._removePackInfoTempDir(packinfo)
            self._processed.append(node.idt)
