###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import errno
import tempfile
import subprocess
import shutil
import glob
import datetime
import logging
import re

from ..provider import AbstractREnvironment
from ..packinfo import PackStatus
from ..packinfo import PackInfo
from ..rbasepackages import RBasePackages
from ..utils import Utils
from ..depsmanager import PackNode
from ..license import License
# from ..command import Command

# INSTALL_TIMEOUT_SEC = 240
logger = logging.getLogger(__name__)


class REnvironment(AbstractREnvironment):

    def __init__(self, rhome, librarypath, licensecheck=False):
        """
        Define a R environment.
        :param rhome: example /home/john/R-3.1.2
        :param librarypath: example 'lib64/R/library'
        """
        super().__init__('renvironment', rhome, librarypath)
        if not os.path.exists(rhome):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    rhome)
        self._repofullpath = Utils.concatpaths(rhome, librarypath)
        if not os.path.exists(self._repofullpath):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    self._repofullpath)
        self._Rbinarypath = os.path.join(rhome, 'bin', 'R')
        if not os.path.exists(self._Rbinarypath):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    self._Rbinarypath)
        self._licensecheck = licensecheck

    @property
    def as_dict(self):
        return self.__dict__

    def ls(self, packagenamesonly=True, withBasePackages=False):
        """
        List available packages (tarballs) with their path relative
        to the baseurl+librarypath.
        """
        folders = os.listdir(self._repofullpath)
        folders = [re.sub('^/', '', x) for x in folders
                   if os.path.exists(os.path.join(
                           self._repofullpath, x, 'DESCRIPTION'))]
        if not withBasePackages:
            return [x for x in folders if x not in RBasePackages.getnames()]
        else:
            return folders

    def find(self, pattern):
        """
        Return a list of repository paths matching a filename pattern.
        The returned paths are relative to the baseurl+librarypath.
        The pattern may contain simple shell-style wildcards a la
        fnmatch. However, unlike fnmatch, filenames starting with a
        dot are special cases that are not matched by '*' and '?'
        patterns.
        """
        files = glob.glob(os.path.join(self._repofullpath, pattern))
        relfiles = [f.replace(self._repofullpath, '') for f in files]
        relfiles2 = [re.sub("^/", "", f) for f in relfiles]
        return relfiles2

    def install_dryrun(self, packnode, dest, overwrite=False,
                       overwritepackages=None):
        if not isinstance(packnode, PackNode):
            msg = 'a PackNode instance is expected!'
            logger.error(msg)
            raise TypeError(msg)
        return self.upload_single_dryrun(
            filepath=packnode.packagepath,
            dest=dest,
            repo=None,
            overwrite=overwrite,
            overwritepackages=overwritepackages,
            packagenamesonly=None)

    def install(self, packnode, overwrite=False,
                overwritepackages=None):
        if not isinstance(packnode, PackNode):
            msg = 'a PackNode instance is expected!'
            logger.error(msg)
            raise TypeError(msg)
        return self.upload_single(
            filepath=packnode.packagepath,
            repo=None,
            overwrite=overwrite,
            overwritepackages=overwritepackages,
            packagenamesonly=None)

    def _installpackage(self, packagepath):
        # Perform a license check
        packInfo = PackInfo(packagepath)
        if(packInfo.status == PackStatus.INVALID):
            message = 'Cannot install {}: {}' \
                      .format(packagepath, packInfo.fullstatus)
            return (-1, message, message)
        # TODO: this is ugly, let's find a better solution
        # the process never terminates
        if(packInfo.name == 'nloptr'):
            message = 'Cannot install {}: ' \
                      'the package is known to be a problem!' \
                      .format(packInfo.name)
            return (-1, message, message)
        if(not packInfo.installation_is_allowed):
            message = "The license \"{}\" is {} " \
                      "and the installation is not allowed!" \
                      .format(
                          packInfo.license,
                          packInfo.licenseclass)
            return (-1, message, message)
        if(packInfo.installation_warning):
            message = "*WARNING* The license \"{}\" is {}" \
                      .format(
                          packInfo.license,
                          packInfo.licenseclass)
            logger.warn(message)
        cmd = os.path.join(self._Rbinarypath)
        cmdargs = [cmd, 'CMD', 'INSTALL', packagepath]
        logger.info('Running: {}'.format(" ".join(cmdargs)))
        p = subprocess.Popen(
            cmdargs,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False)
        # communicate will wait for the process to terminate
        # and set the returncode value
        logger.info('Waiting for PID {} to complete...'
                    .format(p.pid))
        (stdout, stderr) = p.communicate()
        returncode = p.returncode
        # decode stdout and stderr
        if(stdout):
            stdout = stdout.decode()
        if(stderr):
            stderr = stderr.decode()
        # apply a timeout for the installation
        # command = Command(cmdargs)
        # (returncode, stdout, stderr) = command.run(
        #     INSTALL_TIMEOUT_SEC)
        return (returncode, stdout, stderr)

    def _installpackage_dryrun(self, packagepath, dest):
        # Perform a license check
        packInfo = PackInfo(packagepath)
        if(packInfo.status == PackStatus.INVALID):
            message = 'Cannot install {}: {}' \
                      .format(packagepath, packInfo.fullstatus)
            return (-1, message, message)
        # TODO: this is ugly, let's find a better solution
        # the process never terminates
        if(packInfo.name == 'nloptr'):
            message = 'Cannot install {}: ' \
                      'the package is known to be a problem!' \
                      .format(packInfo.name)
            return (-1, message, message)
        if self._licensecheck:
            license = License(packInfo.license)
            if license.blacklisted:
                message = "The license \"{}\" is BLACKLISTED" \
                          .format(packInfo.license)
                return (-1, message, message)
            if license.restricted:
                logger.warn("The license \"{}\" is RESTRICTED"
                            .format(packInfo.license))
        # copy the package to the dest folder
        shutil.copy(packagepath, dest)
        cmd = os.path.join(self._Rbinarypath)
        destpackagepath = os.path.join(dest, os.path.basename(packagepath))
        cmdargs = [cmd, 'CMD', 'INSTALL', destpackagepath]
        command = " ".join(cmdargs)
        # Write installation commands to the install.sh script
        scriptfilepath = os.path.join(dest, 'install.sh')
        with open(scriptfilepath, 'a') as f:
            f.write(command + "\n")
            returncode = 0
            stdout = 'Command written to output script file'
            stderr = None
        return (returncode, stdout, stderr)

    def upload_single(self, filepath, repo=None, overwrite=False,
                      overwritepackages=None, packagenamesonly=None):
        """
        This will install a new R package to the R environment.

        repo is not a used argument.

        return:
        PackStatus.DEPLOY upon success and installation of the package
        PackStatus.DEPLOY_FAILED if any error occured
        """
        if repo:
            logger.warn('Ignoring the repo argument')
        if not os.path.exists(filepath):
            logger.error('Cannot access {0}'.format(filepath))
            return PackStatus.DEPLOY_FAILED
        if overwritepackages is None:
            overwritepackages = []
        packagefullname = os.path.basename(filepath)
        packagename = PackInfo._parse_package_name_version(filepath)[0]
        p = os.path.join(self._repofullpath, packagename)
        if os.path.exists(p):
            if overwrite or packagename in overwritepackages:
                logger.info('The package is already installed')
                try:
                    logger.info('Uninstalling the previous version')
                    shutil.rmtree(p, ignore_errors=False)
                except Exception as e:
                    logger.error('Failed to uninstall previous version: {0}'
                                 .format(e))
                    return PackStatus.DEPLOY_FAILED
            else:
                logger.info('The package is already installed and '
                            'overwritting is disabled')
                # ts = os.path.getmtime(p)
                # pack.install_date = str(datetime.datetime.fromtimestamp(ts))
                return PackStatus.DEPLOYED
        logger.info('Installing package')
        (res, out, err) = self._installpackage(filepath)
        if res != 0:
            logger.error('Installation of package {} failed!\n'
                         '\n[STDOUT BEGINS]\n{}\n[STDOUT ENDS]\n'
                         '\n[STDERR BEGINS]\n{}\n[STDERR ENDS]'
                         .format(packagefullname,
                                 out,
                                 err))
            return PackStatus.DEPLOY_FAILED
        else:
            # pack.fullstatus = out
            # pack.install_date = str(datetime.datetime.now())
            logger.info('Installation of package {} DONE.'
                        .format(packagefullname))
            # verbose:
            # logger.info('Installation of package {} DONE.\n' \
            #             '\n[STDOUT BEGINS]\n{}\n[STDOUT ENDS]'
            #             .format(packagefullname,
            #                     out.decode()))
            return PackStatus.DEPLOYED

    def upload_single_dryrun(self, filepath, dest, repo=None, overwrite=False,
                             overwritepackages=None, packagenamesonly=None):
        """
        This will simulate the installion a new R package to the R environment.

        repo is not a used argument.

        return:
        PackStatus.DEPLOY upon success and installation of the package
        PackStatus.DEPLOY_FAILED if any error occured
        """
        if repo:
            logger.warn('Ignoring the repo argument')
        if not os.path.exists(filepath):
            logger.error('Cannot access {0}'.format(filepath))
            return PackStatus.DEPLOY_FAILED
        if overwritepackages is None:
            overwritepackages = []
        packagefullname = os.path.basename(filepath)
        packagename = PackInfo._parse_package_name_version(filepath)[0]
        p = os.path.join(self._repofullpath, packagename)
        if os.path.exists(p):
            if overwrite or packagename in overwritepackages:
                logger.info('The package is already installed')
                try:
                    logger.info('Uninstalling the previous version')
                    shutil.rmtree(p, ignore_errors=False)
                except Exception as e:
                    logger.error('Failed to uninstall previous version: {0}'
                                 .format(e))
                    return PackStatus.DEPLOY_FAILED
            else:
                logger.info('The package is already installed and '
                            'overwritting is disabled')
                # ts = os.path.getmtime(p)
                # pack.install_date = str(datetime.datetime.fromtimestamp(ts))
                return PackStatus.DEPLOYED
        logger.info('Installing package')
        (res, out, err) = self._installpackage_dryrun(filepath, dest)
        if res != 0:
            logger.error('Installation of package {} failed!\n'
                         '\n[STDOUT BEGINS]\n{}\n[STDOUT ENDS]\n'
                         '\n[STDERR BEGINS]\n{}\n[STDERR ENDS]'
                         .format(packagefullname,
                                 out,
                                 err))
            return PackStatus.DEPLOY_FAILED
        else:
            # pack.fullstatus = out
            # pack.install_date = str(datetime.datetime.now())
            logger.info('Installation of package {} DONE.'
                        .format(packagefullname))
            # verbose:
            # logger.info('Installation of package {} DONE.\n' \
            #             '\n[STDOUT BEGINS]\n{}\n[STDOUT ENDS]'
            #             .format(packagefullname,
            #                     out.decode()))
            return PackStatus.DEPLOYED

    def upload_multiple(self, filepaths, repo=None, overwrite=False,
                        overwritepackages=None):
        pass
