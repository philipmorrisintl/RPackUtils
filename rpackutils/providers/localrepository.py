###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
from distutils.version import LooseVersion
import errno
import tempfile
import subprocess
import shutil
import datetime
import logging
import glob
import re

from ..provider import AbstractPackageRepository
from ..packinfo import PackInfo
from ..packinfo import PackStatus
from ..utils import Utils

logger = logging.getLogger(__name__)


class LocalRepository(AbstractPackageRepository):

    def __init__(self, baseurl, repos):
        """
        Create a local R packages repository.
        :param baseurl: example /home/john/packages
        :param repos: example [R-3.1.2_packages]
        """
        super().__init__('local', baseurl, repos)
        if not os.path.exists(baseurl):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    baseurl)
        for repo in repos:
            repopath = Utils.concatpaths(baseurl, repo)
            if not os.path.exists(repopath):
                raise FileNotFoundError(errno.ENOENT,
                                        os.strerror(errno.ENOENT),
                                        repopath)

    @property
    def as_dict(self):
        return self.__dict__

    def ls(self, packagenamesonly=False):
        """
        List available packages (tarballs) with their path relative
        to the baseurl.
        """
        tarballs = self.find("*.tar.gz")
        if packagenamesonly:
            names = [os.path.basename(tb)
                     .replace('.tar.gz', '').split('_')[0]
                     for tb in tarballs]
            return names
        return tarballs

    def find(self, pattern):
        """
        Return a list of repository paths matching a filename pattern.
        The returned paths are relative to the baseurl of the repository.
        The pattern may contain simple shell-style wildcards a la
        fnmatch. However, unlike fnmatch, filenames starting with a
        dot are special cases that are not matched by '*' and '?'
        patterns.
        """
        files = []
        for repo in self.repos:
            repopath = Utils.concatpaths(self.baseurl, repo)
            matches = glob.glob(os.path.join(repopath, pattern))
            files.extend(matches)
        relfiles = [f.replace(self.baseurl, '') for f in files]
        relfiles2 = [re.sub("^/", "", f) for f in relfiles]
        return relfiles2

    def find_repo(self, repo, pattern):
        """
        Return a list of files matching the specified pattern
        for a given repository nam.
        The pattern may contain simple shell-style wildcards a la
        fnmatch. However, unlike fnmatch, filenames starting with a
        dot are special cases that are not matched by '*' and '?'
        patterns.
        """
        files = []
        repopath = Utils.concatpaths(self.baseurl, repo)
        matches = glob.glob(os.path.join(repopath, pattern))
        files.extend(matches)
        relfiles = [f.replace(self.baseurl, '') for f in files]
        relfiles2 = [re.sub("^/", "", f) for f in relfiles]
        return relfiles2

    def download_single(self, packagename, dest):
        """
        Download a R package given its name.
        If multiple versions exist, the most recent one will
        be taken into account.

        returns:
        PackStatus.DOWNLOADED upon success
        PackStatus.DOWNLOAD_FAILED if any download error occured
        PackStatus.NOT_FOUND if the package could not be found
        """
        tarballs = []
        tarballs = self.find("{0}_*.tar.gz".format(packagename))
        if len(tarballs) == 0:
            logger.error('Package {0} not found!'.format(packagename))
            return PackStatus.NOT_FOUND
        elif len(tarballs) > 1:
            # choose the most recent version of the package
            packinfos_tarballs = []
            for tarball in tarballs:
                packinfo = PackInfo(Utils.concatpaths(self.baseurl, tarball))
                packinfos_tarballs.append(
                    {'packinfo': packinfo, 'tarball': tarball}
                )
            mostrecenttarball = None
            for pi in packinfos_tarballs:
                if mostrecenttarball is None:
                    mostrecenttarball = pi['tarball']
                else:
                    if(LooseVersion(pi['packinfo'].version)
                       > LooseVersion(packinfo.version)):
                        mostrecenttarball = pi['tarball']
        else:
            mostrecenttarball = tarballs[0]
        packagepath = os.path.join(self.baseurl,
                                   *mostrecenttarball.split(os.sep))
        try:
            destfile = os.path.join(dest, os.path.basename(mostrecenttarball))
            shutil.copyfile(packagepath, destfile)
        except Exception as e:
            logger.error("Unable to copy file: {0}".format(e))
            return PackStatus.DOWNLOAD_FAILED
        return PackStatus.DOWNLOADED

    def download_multiple(self, packagenames, dest):
        pass

    def upload_single(self, filepath, repo, overwrite=False,
                      overwritepackages=None):
        """
        Upload a R package to the target repository.

        returns:
        PackStatus.DEPLOYED upon success
        PackStatus.DEPLOY_FAILED if any upload error occured
        PackStatus.DEPLOY_FAILED if the input file is inaccessible
        PackStatus.DEPLOY_FAILED if the specified repo does not exist
        PackStatus.INVALID if the specified repo is invalid
        """
        if repo is None:
            logger.error('Specifying a repo name is mandatory')
            return PackStatus.INVALID
        if repo not in self.repos:
            logger.error('Repository folder {0} is invalid!'.format(repo))
            return PackStatus.DEPLOY_FAILED
        if not os.path.exists(filepath):
            logger.error('Cannot access {0}'.format(filepath))
            return PackStatus.DEPLOY_FAILED
        p = os.path.join(
            Utils.concatpaths(self.baseurl, repo),
            os.path.basename(filepath))
        if os.path.exists(p):
            if overwrite:
                try:
                    shutil.copyfile(filepath, p)
                    return PackStatus.DEPLOYED
                except Exception as e:
                    logger.error(
                        'Failed to push the package '
                        'to the repository: {0}'.format(e))
                    return PackStatus.DEPLOY_FAILED
            else:
                logger.info(
                    'The package already exists in the '
                    'repository and overwrite is disabled')
                return PackStatus.DEPLOYED
        else:
            try:
                shutil.copyfile(filepath, p)
                return PackStatus.DEPLOYED
            except Exception as e:
                logger.error(
                    'Failed to push the package '
                    'to the repository: {0}'.format(e))
                return PackStatus.DEPLOY_FAILED

    def upload_multiple(self, filepaths, repo, overwrite=False,
                        overwritepackages=None):
        pass

    def packinfo(self, packagename, keeptempfiles=False):
        tarballs = []
        repo = None
        if('/' in packagename):
            pathelements = [e for e in packagename.split('/') if e]
            repo = '/'.join(pathelements[0:len(pathelements)-1])
            packagename = pathelements[len(pathelements)-1]
        if(".tar.gz" in packagename):
            if repo:
                tarballs = self.find_repo(repo, "{}".format(packagename))
            else:
                tarballs = self.find("{}".format(packagename))
        else:
            tarballs = self.find("{}_*.tar.gz".format(packagename))
        if len(tarballs) == 0:
            logger.error('Package {} not FOUND'.format(packagename))
            packinfo = PackInfo(packagename)
            packinfo.status = PackStatus.NOT_FOUND
            packinfo.fullstatus = 'Package not found'
        elif len(tarballs) > 1:
            # choose the most recent version of the package
            packinfos = []
            for tarball in tarballs:
                packinfo = PackInfo(Utils.concatpaths(self.baseurl, tarball))
                packinfo.packagepath = tarball
                packinfos.append(packinfo)
            packinfo = None
            for pi in packinfos:
                if packinfo is None:
                    packinfo = pi
                else:
                    try:
                        if(LooseVersion(pi.version)
                           > LooseVersion(packinfo.version)):
                            packinfo = pi
                    except Exception as e:
                        logger.error('Error comparing version \"{}\" '
                                     'with version \"{}\"!'
                                     .format(
                                         pi.version,
                                         packinfo.version))
                        logger.warn('Keeping {} as the most recent version'
                                    .format(packinfo.version))
                        pass
        else:
            packagepath = Utils.concatpaths(self.baseurl, tarballs[0])
            packinfo = PackInfo(packagepath)
            packinfo.packagepath = packagepath
        return packinfo
