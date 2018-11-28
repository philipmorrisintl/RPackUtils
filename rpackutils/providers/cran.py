###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
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

from ..provider import AbstractPackageRepository
from ..packinfo import PackInfo
from ..packinfo import PackStatus
from ..utils import Utils

logger = logging.getLogger(__name__)

MRAN_BASE_URL = 'https://mran.revolutionanalytics.com'


class CRAN(AbstractPackageRepository):
    def __init__(self,
                 baseurl=MRAN_BASE_URL):
        """
        Create a MRAN R packages repository.
        :param baseurl: Default 'https://mran.revolutionanalytics.com'
        """
        super().__init__('cran', baseurl, [])
        if not self.check_connection(numtries=3):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    baseurl)

    def check_connection_mran_snapshot(self, numtries=3, verbose=True):
        """
        Returns True if the connection to mran_snapshots_url is successful.
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
                if(verbose):
                    logger.info('Checking connection to {0} ...'
                                .format(self.mran_snapshots_url))
                retVal = (requests.get(self.mran_snapshots_url)
                          .status_code == 200)
            except Exception as e:
                retVal = False
                logger.error('FATAL: Cannot connect to {0}: {1}'
                             .format(self.mran_snapshots_url, e))
                time.sleep(3)
                continue
            break
        if retVal:
            if(verbose):
                logger.info('Connection to {0} established.'
                            .format(self.mran_snapshots_url))
        return retVal

    @property
    def mran_snapshots_url(self):
        return Utils.concaturls(self.baseurl, 'snapshot')

    def get_mran_packages_url(self, snapshot_date):
        return Utils.concaturls(
            Utils.concaturls(self.mran_snapshots_url, snapshot_date),
            "/src/contrib/")

    def get_mran_package_url(self, snapshot_date, package_name):
        return Utils.concaturls(
            self.get_mran_packages_url(snapshot_date),
            package_name)

    @property
    def as_dict(self):
        return self.__dict__

    def ls_snapshots(self, procs=10, rversion=None):
        starttime = time.time()
        if not self.check_connection(numtries=3, verbose=False):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    self.baseurl)
        # store "R version to snapshot date"
        version2dates = dict()
        # fetch the snapshot dates list
        r1 = requests.get(self.mran_snapshots_url)
        if not r1.status_code == 200:
            logger.error(
                "Cannot open MRAN snapshots URL, "
                "HTTP status code {0}: {1}"
                .format(r1.status_code, self.mran_snapshots_url))
        soup = BeautifulSoup(r1.text, 'html.parser')
        # example of 1 anchor:
        # "<a href="2014-08-18_0233/">2014-08-18_0233/</a>"
        anchors = soup.findAll('a')
        # example of 1 href:
        # u'https://mran.revolutionanalytics.com/snapshot/2014-09-08/'
        # we skip the 1st one which is "../"
        hrefs = [Utils.concaturls(
            Utils.concaturls(self.mran_snapshots_url, anchor['href']),
            "banner.shtml"
        ) for anchor in anchors][1:]
        dates = [str(anchor.contents[0]).replace('/', '')
                 for anchor in anchors][1:]
        logger.info("{0} snapshot dates found.".format(len(dates)))
        pool = multiprocessing.Pool(processes=procs)
        # submit all processes at once and retrieve the results
        # as soon as they are finished
        results = [pool.apply_async(self._ls_snapshot,
                                    args=(hrefs[i], rversion, dates[i]))
                   for i in range(0, len(hrefs))]
        retVals = [res.get() for res in results]
        # avoid zombies and release the memory
        pool.close()
        totalprocessed = 0
        totalskipped = 0
        totalerrors = 0
        for retVal in retVals:
            if retVal['status'] == 'ok':
                if retVal['version'] not in version2dates.keys():
                    version2dates[retVal['version']] = []
                version2dates[retVal['version']].append(retVal['date'])
                totalprocessed = totalprocessed+1
            if retVal['status'] == 'skipped':
                totalskipped = totalskipped+1
            if retVal['status'] == 'error':
                totalerrors = totalerrors+1
        logger.info("Snapshots processed/matching the specified "
                    "R version ({0}), skipped ({1}), errors ({2})."
                    .format(totalprocessed,
                            totalskipped,
                            totalerrors))
        endtime = time.time()
        timeelapsed = endtime - starttime
        logger.info('Time elapsed: {0:.3f} seconds.'.format(timeelapsed))
        return version2dates

    def _ls_snapshot(self, href, rversion, date):
        r2 = requests.get(href)
        soup2 = BeautifulSoup(r2.text, 'html.parser')
        anchors2 = soup2.findAll('a')
        regex = re.compile(".*(R-).*(\.tar\.gz)")
        # example of matches:
        # ['<a href="src/base/R-3/R-3.1.1.tar.gz">R-3.1.1.tar.gz']
        matches = [m.group(0) for l in anchors2
                   for m in [regex.search(str(l))] if m]
        if not len(matches) == 1:
            logger.info("Snapshot \"{0}\": "
                        "Could not parse the R version number "
                        "from the html page!".format(date))
            sys.stdout.flush()
            return {"status": "error", "version": "?", "date": date}
        soup3 = BeautifulSoup(matches[0], 'html.parser')
        version_full = str(soup3.findAll('a')[0].contents[0])
        # remove "R-" and ".tar.gz" from "R-X.Y.Z.tar.gz"
        version = version_full.replace("R-", "").replace(".tar.gz", "")
        if version == rversion or rversion is None:
            return {"status": "ok", "version": version, "date": date}
        else:
            # logger.info('Snapshot \"{0}\": skipping R version {1}' \
            #           .format(date, version))
            return {"status": "skipped", "version": version, "date": date}

    def ls(self, snapshot_date, packagenamesonly=False):
        """
        List available packages (tarballs) given a MRAN snapshot date.
        The list of valid snapshot dates can be fetched with ls_snapshots().
        Return a list of tarballs by default.
        If packagenamesonly is set to True, only names are returned.
        """
        if not self.check_connection(numtries=3, verbose=False):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    self.baseurl)
        r = requests.get(self.get_mran_packages_url(snapshot_date))
        if not r.status_code == 200:
            logger.error(
                "Cannot open MRAN packages URL, "
                "HTTP status code {0}: {1}"
                .format(r.status_code,
                        self.get_mran_packages_url(snapshot_date)))
        soup = BeautifulSoup(r.text, 'html.parser')
        tarballs = []
        anchors = soup.findAll('a')
        allhrefs = [str(anchor['href']) for anchor in anchors][1:]
        # select tarballs only (R packages)
        regex = re.compile(".*(\.tar\.gz)")
        tarballs = [m.group(0) for l in allhrefs
                    for m in [regex.search(str(l))] if m]
        if not tarballs:
            logger.error(
                "Could not parse the R package names "
                "(tarballs) from the html page!")
        logger.info("Number of R packages available: {0}"
                    .format(len(tarballs)))
        if packagenamesonly:
            names = [os.path.basename(p)
                     .replace('.tar.gz', '').split('_')[0]
                     for p in tarballs]
            return names
        else:
            return tarballs

    def find(self, pattern, snapshot_date):
        """
        Return a list of repository paths matching a filename pattern
        for a given snapshot date.
        The returned paths are relative to the snapshot folder of
        the repository.
        The pattern may contain simple shell-style wildcards a la
        fnmatch. However, unlike fnmatch, filenames starting with a
        dot are special cases that are not matched by '*' and '?'
        patterns.
        """
        if not self.check_connection(numtries=3, verbose=False):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    self.baseurl)
        matches = []
        files = self.ls(snapshot_date)
        for entry in files:
            if fnmatch.fnmatch(entry, pattern):
                matches.append(entry)
        return matches

    def _get_package_download_url(self, snapshot_date, packagename):
        tarballs = []
        if('.tar.gz' in packagename):
            tarballs = self.find("{}".format(packagename),
                                 snapshot_date)
        else:
            tarballs = self.find("{}_*.tar.gz".format(packagename),
                                 snapshot_date)
        if len(tarballs) == 0:
            logger.error('Package {0} not FOUND for snapshot {1}'
                         .format(packagename, snapshot_date))
            return None
        elif len(tarballs) > 1:
            logger.error('Found multiple packages matching '
                         '{} for snapshot {}: '
                         .format(packagename,
                                 snapshot_date,
                                 ",".join(tarballs)))
            return None
        else:
            return self.get_mran_package_url(snapshot_date, tarballs[0])

    def download_single(self, snapshot_date, packagename, dest):
        """
        Download a R package to the specified dest folder
        given a MRAN snapchot date.
        returns:
        PackStatus.DOWNLOADED upon success
        PackStatus.DOWNLOAD_FAILED if any download error occured
        PackStatus.NOT_FOUND if the package could not be found
        """
        logger.info('Downloading R package: {0}'.format(packagename))
        retVal = PackStatus.DOWNLOADED
        url = self._get_package_download_url(snapshot_date, packagename)
        if url is None:
            return PackStatus.DOWNLOAD_FAILED
        package_tarball = os.path.basename(url)
        targetpath = os.path.join(dest, package_tarball)
        if not self.check_connection(numtries=3, verbose=False):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    self.baseurl)
        try:
            r = requests.get(url, stream=True)
            with open(targetpath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            logger.info('Done downloading R package: {0}'.format(packagename))
            retVal = PackStatus.DOWNLOADED
        except Exception:
            error_message = 'Error downloading R package: {0}\n{1}\n{2}\n{3}' \
                .format(packagename,
                        url,
                        sys.exc_info()[0],
                        traceback.extract_tb(sys.exc_info()[2]))
            logger.error(error_message)
            # retVal = error_message
            retVal = PackStatus.DOWNLOAD_FAILED
        # check tarball size
        if retVal == PackStatus.DOWNLOADED:
            if os.path.getsize(targetpath) == 0:
                retVal = PackStatus.DOWNLOAD_FAILED
                error_message = "The downloaded package has a zero size: " \
                                "{0}\nURL: {1}" \
                                .format(targetpath, url)
                logger.error(error_message)
        return retVal

    def download_multiple(self, snapshot_date, packagenames, dest, procs=10):
        """
        Download R packages given their names.

        Multiple downloads can be launched in parrallel with
        the procs parameter.
        """
        starttime = time.time()
        totalnumofpacks = len(packagenames)
        totaldownloaded = 0
        # urls = []
        targetpaths = []
        snapshot_dates = []
        logger.info('Selecting the MRAN snapchot: {0}'.format(snapshot_date))
        for idx, packagename in enumerate(packagenames):
            targetpaths.append(dest)
            snapshot_dates.append(snapshot_date)
        # multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=procs)
        # submit all processes at once and retrieve the results
        # as soon as they are finished
        results = [pool.apply_async(self.download_single,
                                    args=(snapshot_dates[i],
                                          packagenames[i],
                                          targetpaths[i]))
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

    def upload(self, filepath, repo, overwrite=False, overwritepackages=None):
        raise NotImplementedError('Uploading is not implemented for CRAN')

    def upload_multiple(self, filepaths, repo, overwrite=False,
                        overwritepackages=None):
        raise NotImplementedError('Uploading is not implemented for CRAN')

    def packinfo(self, packagename, snapshot_date, keeptempfiles=False):
        tarballs = None
        # TODO this can be done in a smarter way
        if ".tar.gz" in packagename:
            tarballs = self.find("{}".format(packagename),
                                 snapshot_date)
        else:
            tarballs = self.find("{}_*.tar.gz".format(packagename),
                                 snapshot_date)
        if len(tarballs) == 0:
            logger.error('Package {} not FOUND for snapshot {}'
                         .format(packagename, snapshot_date))
            packinfo = PackInfo(packagename)
            packinfo.status = PackStatus.NOT_FOUND
            packinfo.fullstatus = 'Package not found'
        elif len(tarballs) > 1:
            logger.error('Multiple packages {} FOUND for snapshot {}: '
                         .format(packagename, snapshot_date,
                                 ','.join(tarballs)))
            packinfo = PackInfo(packagename)
            packinfo.status = PackStatus.NOT_FOUND
            packinfo.fullstatus = 'Multiple packages found: '
            + ','.join(tarballs)
        else:
            # download tarball prior to create the PackInfo object
            dest = tempfile.mkdtemp()
            retVal = self.download_single(snapshot_date, packagename, dest)
            if retVal == PackStatus.DOWNLOADED:
                packinfo = PackInfo(os.path.join(dest, tarballs[0]))
                packinfo.tempdir = dest
                packinfo.packagepath = Utils.concatpaths(dest, tarballs[0])
                logger.debug("PACKINFO: " + str(packinfo.as_dict))
            else:
                packinfo = PackInfo(packagename)
                packinfo.tempdir = dest
                packinfo.status = PackStatus.DOWNLOAD_FAILED
                packinfo.fullstatus = 'Failed to download package '
                + packagename
            if dest and os.path.exists(dest) and not keeptempfiles:
                shutil.rmtree(dest)
        return packinfo
