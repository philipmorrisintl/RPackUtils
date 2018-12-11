###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
from distutils.version import LooseVersion
import errno
import sys
import traceback
import requests
import tempfile
import subprocess
import shutil
import datetime
import logging
import glob
import re
from bs4 import BeautifulSoup
import multiprocessing
import time
import fnmatch
import magic

from ..provider import AbstractPackageRepository
from ..packinfo import PackInfo
from ..packinfo import PackStatus
from ..utils import Utils

logger = logging.getLogger(__name__)

class Artifactory(AbstractPackageRepository):
    def __init__(self, baseurl, repos, auth, verify):
        """
        Artifactory repository client.
        
        :param baseurl: example 'https://artifacforyhost/artifactory'
        :param repos: list of repository names
        :param auth: username and password as ('john', 'secret')
        :param verify: path to the SSL certificate, False to bypass the verification
        """
        super().__init__('artifactory', baseurl, repos)
        self.auth = auth
        self.verify = verify
        if not self.check_connection(numtries=3):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    baseurl)

    def check_connection(self, numtries=3):
        """
        Returns True if the connection to baseurl is successful.
        False otherwise.

        A max number of numtries will be done.
        Please note numtries must be >= 1.
        """
        if numtries < 1:
            logger.warn('The \"numtries\" parameter in check_connection() '
                        "must be >= 1. Was \"{0}\" but using 1!"
                        .format(numtries))
            numtries = 1
        retVal = False
        for i in range(0, numtries):
            try:
                logger.info('Checking connection to {0} ...'
                            .format(self.baseurl))
                retVal = ((self._do_request(self.baseurl)).status_code == 200)
            except Exception as e:
                retVal = False
                logger.error('FATAL: Cannot connect to {0}: {1}'
                             .format(self.baseurl, e))
                time.sleep(3)
                continue
            break
        if retVal:
            logger.info('Connection to {0} established.'
                        .format(self.baseurl))
        return retVal

    @property
    def as_dict(self):
        return self.__dict__

    def _get_api_url(self, repo):
        return Utils.concaturls(
            self.baseurl,
            "/api/storage/{0}".format(repo))

    def _do_request(self, url, stream=False):
        r = requests.get(
            url,
            auth=self.auth,
            verify=self.verify,
            stream=stream)
        return r

    def ls(self, repo=None, packagenamesonly=False):
        """
        List available files accross all defined repositories.
        The parameter packagenamesonly will be ignore in
        this implementation.

        The returned filepaths will be prefixed with
        their repository name.
        """
        if repo is not None:
            return self.ls_repo(repo)
        else:
            files = []
            for repo in self.repos:
                matches = self.ls_repo(repo)
                files.extend([Utils.concaturls(repo, match) for match in matches])
            return files

    def ls_repo(self, repo):
        """
        List available files given a repository name.

        The returned filepaths won't be prefixed by their
        repository name.
        """
        r = self._do_request(self._get_api_url(repo))
        if r.status_code == 200:
            content = r.json()
            if 'children' not in content:
                logger.error('Not well formated JSON response')
                return []
            return [x['uri'][1:] for x in content['children'] if not x['folder']]
        if r.status_code == 404:
            logger.error('Repository {} does not exist!'.format(repo))
            return []
        else:
            logger.error('Unexpected http {0} while trying'
                         ' to access the repository {1} '
                         .format(r.status_code, repo))
            return []

    def find(self, pattern):
        """
        Return a list of files matching the specified pattern
        for the defined repositories.
        The pattern may contain simple shell-style wildcards a la
        fnmatch. However, unlike fnmatch, filenames starting with a
        dot are special cases that are not matched by '*' and '?'
        patterns.
        """
        files = []
        for repo in self.repos:
            matches = self.find_repo(repo, pattern)
            files.extend([Utils.concaturls(repo, match) for match in matches])
        return files

    def find_repo(self, repo, pattern):
        """
        Return a list of files matching the specified pattern
        for a given repository name.
        The pattern may contain simple shell-style wildcards a la
        fnmatch. However, unlike fnmatch, filenames starting with a
        dot are special cases that are not matched by '*' and '?'
        patterns.
        """
        matches = []
        files = self.ls_repo(repo)
        for entry in files:
            if fnmatch.fnmatch(entry, pattern):
                matches.append(entry)
        return matches

    def download_single_fullname(self, repo, fullpackagename, dest):
        """
        Download a R package to the specified dest folder
        given a repository name.
        The fullpackagename uniquely identifies a package and is
        like "packagename_version.tar.gz".
        returns:
        PackStatus.DOWNLOADED upon success
        PackStatus.DOWNLOAD_FAILED if any download error occured
        PackStatus.NOT_FOUND if the package could not be found
        """
        logger.info('Downloading R package: {0}'.format(fullpackagename))
        retVal = PackStatus.DOWNLOADED
        url = Utils.concaturls(
            Utils.concaturls(self.baseurl, repo),
            fullpackagename
        )
        if url is None:
            logger.error('Cancelling download of package {0} :'
                         'could not figure out the download url!'
                         .format(fullpackagename))
            return PackStatus.DOWNLOAD_FAILED
        package_tarball = os.path.basename(url)
        targetpath = Utils.concaturls(dest, package_tarball)
        try:
            r = self._do_request(url, stream=True)
            with open(targetpath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            logger.info('Done downloading R package: {0}'
                        .format(fullpackagename))
            retVal = PackStatus.DOWNLOADED
        except Exception:
            error_message = "Error downloading R package: "
            "{0}\n{1}\n{2}\n{3}".format(
                fullpackagename,
                url,
                sys.exc_info()[0],
                traceback.extract_tb(sys.exc_info()[2]))
            logger.error(error_message)
            retVal = PackStatus.DOWNLOAD_FAILED
        if retVal == PackStatus.DOWNLOADED:
            # check tarball size
            if os.path.getsize(targetpath) == 0:
                retVal = PackStatus.DOWNLOAD_FAILED
                error_message = "The downloaded package has a zero size: " \
                                "{0}\nURL: {1}" \
                                .format(targetpath, url)
                logger.error(error_message)
            # check file type
            if(magic.from_file(targetpath) == 'ASCII text'):
                retVal = PackStatus.DOWNLOAD_FAILED
                error_message = "Artifactory returned a status message " \
                                "instead of the package: " \
                                "{0}\nURL: {1}" \
                                .format(targetpath, url)
                logger.error(error_message)
        return retVal

    def download_single(self, repo, packagename, dest):
        """
        Download a R package to the specified dest folder
        given a repository name.
        returns:
        PackStatus.DOWNLOADED upon success
        PackStatus.DOWNLOAD_FAILED if any download error occured
        PackStatus.NOT_FOUND if the package could not be found
        """
        logger.info('Downloading R package: {0}'.format(packagename))
        retVal = PackStatus.DOWNLOADED
        matches = self.find_repo(repo, '{0}_*.tar.gz'.format(packagename))
        if len(matches) == 0:
            logger.error('Package {0} not found in repository {1}!'
                         .format(packagename, repo))
            return PackStatus.NOT_FOUND
        elif len(matches) > 1:
            # fetch the most recent version
            packinfos_tarballs = []
            dest2 = tempfile.mkdtemp()
            for tarball in matches:
                # download tarball prior to create the PackInfo object
                retVal = self.download_single_fullname(repo,
                                                       tarball,
                                                       dest2)
                if retVal == PackStatus.DOWNLOADED:
                    packinfo = PackInfo(Utils.concatpaths(dest2, tarball))
                    packinfos_tarballs.append(
                        {'packinfo': packinfo, 'tarball': tarball}
                    )
                else:
                    packinfo = PackInfo(tarball.split('.')[0])
                    packinfo.status = PackStatus.DOWNLOAD_FAILED
                    packinfo.fullstatus = 'Failed to download package {0}' \
                            .format(tarball)
            if dest and os.path.exists(dest2):
                shutil.rmtree(dest2)
            mostrecenttarball = None
            for pi in packinfos_tarballs:
                if mostrecenttarball is None:
                    mostrecenttarball = pi['tarball']
                else:
                    if LooseVersion(pi['packinfo'].version) > LooseVersion(
                            packinfo.version):
                        mostrecenttarball = pi['tarball']
            retVal = self.download_single_fullname(repo,
                                                   mostrecenttarball,
                                                   dest)
            return retVal
        else:
            retVal = self.download_single_fullname(repo,
                                                   matches[0],
                                                   dest)
            return retVal

    def download_multiple(self, repos, packagenames, dest, procs=20):
        """
        Download R packages given their names and repository location.

        Multiple downloads can be launched in parrallel with
        the procs parameter.
        """
        starttime = time.time()
        totalnumofpacks = len(packagenames)
        totaldownloaded = 0
        logger.info('preparing to download {0} packages'
                    .format(totalnumofpacks))
        # multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=procs)
        # submit all processes at once and retrieve the results
        # as soon as they are finished
        results = [pool.apply_async(self.download_single,
                                    args=(repos[i],
                                          packagenames[i],
                                          dest))
                   for i in range(0, totalnumofpacks)]
        retVals = [res.get() for res in results]
        # avoid zombies and release the memory
        pool.close()
        for retVal in retVals:
            # if retVal == 'ok':
            if retVal == PackStatus.DOWNLOADED:
                totaldownloaded = totaldownloaded+1
        logger.info("{0}/{1} packages done."
                    .format(totaldownloaded,
                            totalnumofpacks))
        endtime = time.time()
        timeelapsed = endtime - starttime
        logger.info('Time elapsed: {0:.3f} seconds.'.format(timeelapsed))
        if totaldownloaded < totalnumofpacks:
            logger.error('Failed to download all R packages')
        return retVals

    def upload_single(self, filepath, repo, properties=None,
                      overwrite=False, overwritepackages=None):
        logger.info('Deploying artifact: {0}'.format(filepath))
        # construct the url with the credentials, repo and file
        url = self.baseurl.replace(
            '://', '://{0}:{1}@'.format(self.auth[0],
                                        self.auth[1]))
        url = Utils.concaturls(
            Utils.concaturls(url, repo),
            os.path.basename(filepath))
        # append the properties if any
        if properties:
            # https://www.jfrog.com/confluence/display/RTF/Using+Properties+in+Deployment+and+Resolution
            properties_matrix = ""
            for k in properties.keys():
                properties_matrix += ";"
                properties_matrix += "{0}={1}".format(k, properties[k])
            url += properties_matrix
        cmd = None
        if self.verify:
            cmd = 'curl --cacert {0} -X PUT {1} -T {2}'.format(
                self.verify, url, filepath)
        else:
            cmd = 'curl -k -XPUT {0} -T {1}'.format(
                url, filepath)
        # launch the system command
        # res = subprocess.call(cmd, shell=True)
        res, out, err = Utils.subprocesscall(cmd)
        # curl doesn't return a none-zero return code
        # while getting any http status error code so we are checking
        # the output content
        if res != 0:
            logger.error('Failed to deploy file: {}'.format(filepath))
            logger.error('COMMAND: {}'.format(cmd))
            logger.error('STDOUT: {}'.format(out))
            logger.error('STDERR: {}'.format(err))
            return PackStatus.DEPLOY_FAILED
        if out is not None:
            if b'<html>' in out or b'status' in out:
                logger.error('Failed to deploy file: {}'.format(filepath))
                logger.error('COMMAND: {}'.format(cmd))
                logger.error('STDOUT: {}'.format(out))
                logger.error('STDERR: {}'.format(err))
                return PackStatus.DEPLOY_FAILED
        logger.info('Successfully deployed file: {} '
                    'to repository {}'.format(filepath, repo))
        return PackStatus.DEPLOYED

    def upload_multiple(self, filepaths, repo, procs=20, properties=None,
                        overwrite=False,
                        overwritepackages=None):
        starttime = time.time()
        totalnumoffiles = len(filepaths)
        totaldeployed = 0
        # multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=procs)
        # submit all processes at once and retrieve the results
        # as soon as they are finished
        results = None
        if properties:
            results = [pool.apply_async(self.upload_single,
                                        args=(filepaths[i],
                                              repo,
                                              properties[i],
                                              overwrite))
                       for i in range(0, totalnumoffiles)]
        else:
            results = [pool.apply_async(self.upload_single,
                                        args=(filepaths[i],
                                              repo,
                                              overwrite))
                       for i in range(0, totalnumoffiles)]
        retVals = [res.get() for res in results]
        # avoid zombies and release the memory
        pool.close()
        endtime = time.time()
        timeelapsed = endtime - starttime
        for retVal in retVals:
            if retVal == PackStatus.DEPLOYED:
                totaldeployed = totaldeployed+1
        logger.info("{0}/{1} artifacts deployed."
                    .format(totaldeployed,
                            totalnumoffiles))
        logger.info('Time elapsed: {0:.3f} seconds.'.format(timeelapsed))
        if totaldeployed < totalnumoffiles:
            logger.error('Failed to deploy all artifacts')
        return retVals

    def _get_fullpackagenames(self, packagename, repo):
        fullpackagenames = []
        if(".tar.gz" in packagename):
            fullpackagenames = self.find_repo(
                repo, '{0}'.format(packagename))
        else:
            fullpackagenames = self.find_repo(
                repo, '{0}_*.tar.gz'.format(packagename))
        return fullpackagenames

    def _get_name_and_repo(self, packagename):
        pathelements = [e for e in packagename.split('/') if e]
        repo = '/'.join(pathelements[0:len(pathelements)-1])
        packagename = pathelements[len(pathelements)-1]
        return packagename, repo
                
    def packinfo(self, packagename, repo=None, keeptempfiles=False):
        """
        :param packagename: can be one of "methods",
                            "methods_1.2.3.tar.gz" or
                            "repo1/methods_1.2.3.tar.gz"
        """
        fullpackagenames = []
        if repo is None:
            # TODO use pattern matching
            if('/' in packagename):
                packagename, repo = self._get_name_and_repo(packagename)
                fullpackagenames = self._get_fullpackagenames(
                    packagename, repo)
            else:
                if(".tar.gz" in packagename):
                    fullpackagenames = self.find(
                        '{0}'.format(packagename))
                else:
                    fullpackagenames = self.find(
                        '{0}_*.tar.gz'.format(packagename))
        else:
            fullpackagenames = self._get_fullpackagenames(packagename, repo)
        if len(fullpackagenames) == 0:
            if repo:
                logger.error('Package {0} not FOUND in Artifactory '
                             'repository \"{1}\"'
                             .format(packagename, repo))
            else:
                logger.error('Package {0} not FOUND in Artifactory '
                             'repositories \"{1}\"'
                             .format(packagename, ",".join(self.repos)))
            packinfo = PackInfo(packagename)
            packinfo.status = PackStatus.NOT_FOUND
            packinfo.fullstatus = 'Package not found'
        elif len(fullpackagenames) > 1:
            # fetch the most recent version
            packinfos_tarballs = []
            dest2 = tempfile.mkdtemp()
            for tarball in fullpackagenames:
                # download tarball prior to create the PackInfo object
                repo_orig = repo
                name, repo = self._get_name_and_repo(tarball)
                if not repo:
                    repo = repo_orig
                retVal = self.download_single_fullname(repo,
                                                       name,
                                                       dest2)
                if retVal == PackStatus.DOWNLOADED:
                    logger.info('Downloaded {0}'.format(tarball))
                    tarballfullpath = Utils.concatpaths(dest2, name)
                    packinfo = None
                    try:
                        packinfo = PackInfo(tarballfullpath)
                        packinfo.tempdir = dest2
                    except Exception as e:
                        pass
                    if packinfo and packinfo.status is None:
                        packinfo.packagepath = tarballfullpath
                        packinfos_tarballs.append(
                            {'packinfo': packinfo,
                             'repo': repo,
                             'tarball': tarball}
                        )
                    else:
                        logger.error('An error occured while reading the '
                                     'tarball contents at {0}'
                                     .format(tarballfullpath))
                        # packinfo = PackInfo(tarball.split('_')[0])
                        if(packinfo):
                            packinfo.tempdir = dest2
                            packinfo.status = PackStatus.DOWNLOAD_FAILED
                            packinfo.fullstatus = 'An error occured while'
                            ' reading the tarball contents of {0}'.format(
                                tarball)
                else:
                    logger.info('Failed to Download {0}'.format(tarball))
                    # packinfo = PackInfo(name)
                    if(packinfo):
                        packinfo.tempdir = dest2
                        packinfo.status = PackStatus.DOWNLOAD_FAILED
                        packinfo.fullstatus = 'Failed to download '
                        'package {0}'.format(tarball)
            mostrecentpit = None
            # logger.info('packinfos_tarballs = {}'.format(packinfos_tarballs))
            for pit in packinfos_tarballs:
                if mostrecentpit is None:
                    mostrecentpit = pit
                else:
                    try:
                        if LooseVersion(pit['packinfo'].version) \
                           > LooseVersion(mostrecentpit['packinfo'].version):
                            mostrecentpit = pit
                    except Exception as e:
                        logger.error('Error comparing version \"{}\" '
                                     'with version \"{}\"!'
                                     .format(
                                         pit['packinfo'].version,
                                         mostrecentpit['packinfo'].version))
                        logger.warn('Keeping {} as the most recent version'
                                    .format(mostrecentpit['packinfo'].version))
                        pass
            packinfo = mostrecentpit['packinfo']
            if dest2 and os.path.exists(dest2) and not keeptempfiles:
                shutil.rmtree(dest2)
            return packinfo
        else:
            # download tarball prior to create the PackInfo object
            dest = tempfile.mkdtemp()
            repo_orig = repo
            name, repo = self._get_name_and_repo(fullpackagenames[0])
            if not repo:
                repo = repo_orig
            # if repo is None:
            #     name, repo = self._get_name_and_repo(fullpackagenames[0])
            # else:
            #     name = fullpackagenames[0]
            retVal = self.download_single_fullname(repo,
                                                   name,
                                                   dest)
            if retVal == PackStatus.DOWNLOADED:
                tarballfullpath = os.path.join(
                    dest,
                    name)
                packinfo = PackInfo(tarballfullpath)
                packinfo.tempdir = dest
                packinfo.status = PackStatus.DOWNLOADED
                packinfo.packagepath = tarballfullpath
                logger.debug("PACKINFO: " + str(packinfo.as_dict))
            else:
                packinfo = PackInfo(fullpackagenames[0])
                packinfo.tempdir = dest
                packinfo.status = PackStatus.DOWNLOAD_FAILED
                packinfo.fullstatus = 'Failed to download package ' \
                                      + packagename
            if dest and os.path.exists(dest) and not keeptempfiles:
                shutil.rmtree(dest)
            return packinfo
