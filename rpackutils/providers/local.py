##############################################################################
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
##############################################################################
# -*- coding: utf-8 -*-
__author__ = "Sylvain Gubian"
__copyright__ = "Copyright 2016, PMP SA"
__license__ = "GPL2.0"
__email__ = "Sylvain.Gubian@pmi.com"

import os
import tempfile
import subprocess
import shutil
import datetime
import logging

from ..provider import AbstractProvider
from ..packinfo import PackStatus
from ..packinfo import update_from_desc

logger = logging.getLogger(__name__)

class LocalProvider(AbstractProvider):

    def __init__(self, baseurl, repos):
       AbstractProvider.__init__(self)
       self.name = 'Local'
       self.baseurl = baseurl
       self.repos = repos
       if not os.path.exists(self.baseurl):
           raise(IOError,
                 '{0} does not exists, not R install path defined'.format(
                 self.baseurl))
       if not os.path.exists(self.repos):
           raise(IOError,
                 '{0} does not exists, not R library folder defined'.format(
                 self.repos))

    def ls(self):
        """ Returns the list of available packages from the provider
        In this case, list of installed packages
        """
        folders = os.listdir(self.repos)
        # Keeping valid packages (folder which contain DESCRIPTION file)
        folders = [x for x in folders if os.path.exists(os.path.join(
            self.repos, x, 'DESCRIPTION'))]
        return folders

    def download(self, pack, dest=None):
        raise NotImplementedError(
                'Downloading package with Local provider is not implemented')

    def push(self, pack, source, overwrite=False):
        if not os.path.exists(source):
            raise(IOError, 'Package source not found for installation')
        p = os.path.join(self.repos, pack.name)
        if os.path.exists(p):
            # Package already exists but we reinstall
            if overwrite:
                try:
                    shutil.rmtree(p, ignore_errors=False)
                except Exception, e:
                    logger.info('Failed to uninstall previous version')
                    pack.status = PackStatus.DEPLOY_FAILED
                    pack.fullstatus = e
                    raise(RuntimeError, 'Installation of {} failed')
            else:
                pack.status = PackStatus.DEPLOYED
                pack.fullstatus = "Already installed package"
                ts = os.path.getmtime(p)
                pack.install_date = str(datetime.datetime.fromtimestamp(ts))
                return

        # If package already installed
        cmd = os.path.join(self.baseurl, 'bin', 'R')
        p = subprocess.Popen(
                [cmd, 'CMD', 'INSTALL', source],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False)
        (out, err) = p.communicate()
        res = p.wait()
        if res !=0:
            pack.status = PackStatus.DEPLOY_FAILED
            pack.fullstatus = err
            raise(RuntimeError, 'Installation of package {} failed'.format(
                pack.fullname
                ))
        else:
            pack.status = PackStatus.DEPLOYED
            pack.fullstatus = out
            pack.install_date = str(datetime.datetime.now())
            logger.info('Installation of package {} DONE.'.format(
                pack.fullname))

    def packinfo(self, pack):
        p = os.path.join(self.repos, pack.name)
        if not os.path.exists(p):
            logger.error('Package {} not FOUND'.format(pack.name))
            pack.status = PackStatus.NOT_FOUND
            pack.fullstatus = 'Package folder not found'
            return
        descpath = os.path.join(p, 'DESCRIPTION')
        if not os.path.exists(descpath):
            logger.error('No DESCRIPTION file for package: {}'.format(
                pack.name
                ))
            pack.status = PackStatus.INVALID
            pack.fullstatus = 'No DESCRIPTION file found'
        try:
            update_from_desc(pack, descpath)
            pack.status = PackStatus.DEPLOYED
        except Exception, e:
            logger.error('Failed to get package information')
            pack.status = PackStatus.INVALID
            pack.fullstatus = 'Error: {}'.format(e)
