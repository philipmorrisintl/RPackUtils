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
import json

from ..provider import AbstractPackageRepository
from ..packinfo import PackInfo
from ..packinfo import PackStatus
from ..utils import Utils

logger = logging.getLogger(__name__)

BIOC_BASE_URL = 'https://www.bioconductor.org'
BIOC_POSSIBLE_VIEWS = ['software', 'experimentData', 'annotationData']


class Bioconductor(AbstractPackageRepository):
    def __init__(self,
                 baseurl=BIOC_BASE_URL):
        """
        Create a Bioconductor R packages repository.
        :param baseurl: Default 'https://www.bioconductor.org'
        """
        super().__init__('bioc', baseurl, [])
        if not self.check_connection(numtries=3):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    baseurl)

    @property
    def bioc_chkres_url(self):
        return Utils.concaturls(self.baseurl, 'checkResults')

    @property
    def bioc_possible_views(self):
        return BIOC_POSSIBLE_VIEWS

    def get_bioc_software_url(self, bioc_release):
        path = 'packages/json/{0}/bioc/packages.js'
        return Utils.concaturls(self.baseurl, path.format(bioc_release))

    def get_bioc_experimentdata_url(self, bioc_release):
        path = 'packages/json/{0}/data/experiment/packages.js'
        return Utils.concaturls(self.baseurl, path.format(bioc_release))

    def get_bioc_annotationdata_url(self, bioc_release):
        path = 'packages/json/{0}/data/annotation/packages.js'
        return Utils.concaturls(self.baseurl, path.format(bioc_release))

    def get_bioc_software_page_url(self, bioc_release, package_name):
        path = 'packages/{0}/bioc/html/{1}.html'
        return Utils.concaturls(self.baseurl,
                                path.format(bioc_release, package_name))

    def get_bioc_experimentaldata_page_url(self, bioc_release, package_name):
        path = 'packages/{0}/data/experiment/html/{1}.html'
        return Utils.concaturls(self.baseurl,
                                path.format(bioc_release, package_name))

    def get_bioc_annotationdata_page_url(self, bioc_release, package_name):
        path = 'packages/{0}/data/annotation/html/{1}.html'
        return Utils.concaturls(self.baseurl,
                                path.format(bioc_release, package_name))

    def get_bioc_download_software_url(self, bioc_release, full_package_name):
        path = 'packages/{0}/bioc/src/contrib/{1}.tar.gz'
        return Utils.concaturls(
            self.baseurl,
            path.format(bioc_release, full_package_name)
        )

    def get_bioc_download_experimentaldata_url(self, bioc_release,
                                               full_package_name):
        path = 'packages/{0}/data/experiment/src/contrib/{1}.tar.gz'
        return Utils.concaturls(
            self.baseurl,
            path.format(bioc_release, full_package_name)
        )

    def get_bioc_download_annotationdata_url(self, bioc_release,
                                             full_package_name):
        path = 'packages/{0}/data/annotation/src/contrib/{1}.tar.gz'
        return Utils.concaturls(
            self.baseurl,
            path.format(bioc_release, full_package_name)
        )

    def _get_bioc_json_urls(self, bioc_release):
        softwareUrl = self.get_bioc_software_url(bioc_release)
        annotationDataUrl = self.get_bioc_annotationdata_url(bioc_release)
        experimentDataUrl = self.get_bioc_experimentdata_url(bioc_release)
        return {'software': softwareUrl,
                'annotationData': annotationDataUrl,
                'experimentData': experimentDataUrl}

    def _get_bioc_package_page_url(self, bioc_release, package_name, view):
        # This must be aligned with BIOC_POSSIBLE_VIEWS
        if view == 'software':
            return self.get_bioc_software_page_url(
                bioc_release, package_name)
        elif view == 'experimentData':
            return self.get_bioc_experimentaldata_page_url(
                bioc_release, package_name)
        elif view == 'annotationData':
            return self.get_bioc_annotationdata_page_url(
                bioc_release, package_name)
        else:
            logger.error('The view must be one of \"software\", '
                         '\"experimentData\" or \"annotationData\".')
            exit(-1)

    def _get_bioc_package_download_url(self, bioc_release, full_package_name,
                                       view):
        if view == 'software':
            return self.get_bioc_download_software_url(
                bioc_release, full_package_name)
        elif view == 'experimentData':
            return self.get_bioc_download_experimentaldata_url(
                bioc_release, full_package_name)
        elif view == 'annotationData':
            return self.get_bioc_download_annotationdata_url(
                bioc_release, full_package_name)
        else:
            logger.error('The view must be one of \"software\", '
                         '\"experimentData\" or \"annotationData\".')
            exit(-1)

    @property
    def as_dict(self):
        return self.__dict__

    def _get_full_package_name(self, bioc_release, view, package_name):
        """
        Given a package name (like "RGrah2js"), a Bioconductor release
        (like "3.0") and a valid Bioc view (like "software"), the
        so called full package name is returned.
        Example of full package name: "RGraph2js_0.99.0"
        """
        package_page_url = self._get_bioc_package_page_url(
            bioc_release, package_name, view)
        r = requests.get(url=package_page_url)
        if not r.status_code == 200:
            logger.error('Cannot open the BIOC package page URL, '
                         'HTTP status code {0}: {1}'
                         .format(r.status_code, package_page_url))
            return {"status": "error",
                    "url": package_page_url,
                    "full_package_name": None,
                    "name": package_name}
        soup = BeautifulSoup(r.text, 'html.parser')
        anchors = soup.findAll('a')
        hrefs = [anchor['href'] for anchor in anchors
                 if 'href' in anchor.attrs.keys()]
        package_source_link = [href for href in hrefs
                               if '.tar.gz' in href]
        # example result: ['../src/contrib/ABAData_1.4.0.tar.gz']
        if not len(package_source_link) == 1:
            logger.error('Could not find the package '
                         'source link from {0}.'
                         .format(package_page_url))
            return {"status": "error",
                    "url": package_page_url,
                    "full_package_name": None,
                    "name": package_name}
            exit(-1)
        full_package_name = package_source_link[0] \
            .replace('../src/contrib/', '') \
            .replace('.tar.gz', '')
        return {"status": "ok",
                "url": package_page_url,
                "full_package_name": full_package_name,
                "name": package_name}

    def ls_releases(self):
        r1 = requests.get(self.bioc_chkres_url)
        if not r1.status_code == 200:
            logger.error("Cannot open BIOC checkResults URL, "
                         "HTTP status code {0}: {1}"
                         .format(r1.status_code, self.bioc_chkres_url))
        soup = BeautifulSoup(r1.text, 'html.parser')
        # <h3>Bioconductor X.Y (release)</h3>
        anchors = soup.findAll('h3')
        releases = [str(anchor.contents[0]) for anchor in anchors]
        return releases

    def ls(self, bioc_release, view, procs=10):
        """
        List available packages (as package names) given
        a Bioconductor release and view.
        The list of valid releases can be fetched with ls_releases().
        Possible views are: 'software', 'experimentData', 'annotationData'
        """
        starttime = time.time()
        if view not in self.bioc_possible_views:
            logger.error('The view must be one of {0}.'
                         .format(",".join(self.bioc_possible_views)))
            exit(-1)
        url = self._get_bioc_json_urls(bioc_release)[view]
        rjs = requests.get(url=url)
        if not rjs.status_code == 200:
            logger.error("Cannot open BIOC view URL, "
                         "HTTP status code {0}: {1}"
                         .format(rjs.status_code, url))
        logger.info('Fetching list of BIOC {0} packages...'.format(view))
        js = rjs.text
        json_str = ''
        if view == 'software':
            json_str = js.replace("var bioc_packages = ", "") \
                .replace("};", "}")
        elif view == 'experimentData':
            json_str = js.replace("var data_experiment_packages = ", "") \
                .replace("};", "}")
        else:
            json_str = js.replace("var data_annotation_packages = ", "") \
                .replace("};", "}")
        json_obj = json.loads(json_str)
        packageNames = []
        # packagePageUrls = []
        for c in json_obj['content']:
            packageName = c[0]
            packageNames.append(packageName)
            # packagePageUrl = self._get_bioc_package_page_url(
            #     bioc_release, c[0], view)
            # packagePageUrls.append(packagePageUrl)
        rjs.close()
        totalNumOfPackages = len(packageNames)
        logger.info("{0} {1} pakages found.".format(totalNumOfPackages, view))
        pool = multiprocessing.Pool(processes=procs)
        # submit all processes at once and retrieve the results
        # as soon as they are finished
        results = [pool.apply_async(self._get_full_package_name,
                                    args=(bioc_release, view, packageNames[i]))
                   for i in range(0, totalNumOfPackages)]
        retVals = [res.get() for res in results]
        # avoid zombies and release the memory
        pool.close()
        totalprocessed = 0
        totalerrors = 0
        packageFullNames = []
        for retVal in retVals:
            if retVal['status'] == 'ok':
                packageFullNames.append(retVal['name'])
                totalprocessed = totalprocessed+1
            if retVal['status'] == 'error':
                totalerrors = totalerrors+1
        logger.info("Package pages processed to get version numbers "
                    "({0}), errors ({1})."
                    .format(totalprocessed,
                            totalerrors))
        endtime = time.time()
        timeelapsed = endtime - starttime
        logger.info('Time elapsed: {0:.3f} seconds.\n'.format(timeelapsed))
        if totalerrors > 0:
            logger.error('Could not extract all packages versions.')
            # exit(-1)
        return packageFullNames

    def find(self, pattern, bioc_release, view):
        """
        Return a list of packages matching a filename pattern
        for a given Bioconductor release and view.
        This does a pattern matching against the ls function
        and return a list of package names.
        The pattern may contain simple shell-style wildcards a la
        fnmatch. However, unlike fnmatch, filenames starting with a
        dot are special cases that are not matched by '*' and '?'
        patterns.
        """
        matches = []
        files = self.ls(bioc_release, view)
        for entry in files:
            if fnmatch.fnmatch(entry, pattern):
                matches.append(entry)
        return matches

    def upload_single(self, filepath, bioc_release, view,
                      overwrite=False, overwritepackages=None):
        raise NotImplementedError(
            'Uploading to Bioconductor is not implemented')

    def upload_multiple(self, filepaths, bioc_release, view,
                        overwrite=False, overwritepackages=None):
        raise NotImplementedError(
            'Uploading to Bioconductor is not implemented')

    def download_single(self, packagename, bioc_release, view, dest):
        """
        Download a R package to the specified dest folder
        given a Bioconductor release and view.
        returns:
        PackStatus.DOWNLOADED upon success
        PackStatus.DOWNLOAD_FAILED if any download error occured
        PackStatus.NOT_FOUND if the package could not be found
        """
        logger.info('Downloading BIOC R {0}: {1}'.format(view, packagename))
        gfpn = self._get_full_package_name(
            bioc_release, view, packagename)
        if gfpn['status'] == 'error':
            logger.error("Download canceled due to previous error!")
            return PackStatus.DOWNLOAD_FAILED
        fullpackagename = gfpn['full_package_name']
        url = self._get_bioc_package_download_url(
            bioc_release, fullpackagename, view)
        retVal = PackStatus.DOWNLOADED
        package_tarball = os.path.basename(url)
        targetpath = os.path.join(dest, package_tarball)
        try:
            r = requests.get(url, stream=True)
            with open(targetpath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            logger.info('Done downloading BIOC R {0}: {1}'
                        .format(view, packagename))
            retVal = PackStatus.DOWNLOADED
        except Exception:
            error_message = 'Error downloading R {0}: {1}\n{2}\n{3}' \
                .format(view,
                        packagename,
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

    def download_multiple(self, packagenames, bioc_release, view, dest,
                          procs=10):
        """
        Download R packages given their names.

        Multiple downloads can be launched in parrallel with
        the procs parameter.
        """
        starttime = time.time()
        totalnumofpacks = len(packagenames)
        totaldownloaded = 0
        pool = multiprocessing.Pool(processes=procs)
        # submit all processes at once and retrieve the results
        # as soon as they are finished
        results = [pool.apply_async(self.download_single,
                                    args=(packagenames[i], bioc_release,
                                          view, dest))
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

    def packinfo(self, packagename, bioc_release, view, keeptempfiles=False):
        packagenames = self.find("{}*".format(packagename),
                                 bioc_release, view)
        if len(packagenames) == 0:
            logger.error('Package {} not FOUND in Bioconductor {} {}'
                         .format(packagename, bioc_release, view))
            packinfo = PackInfo(packagename)
            packinfo.status = PackStatus.NOT_FOUND
            packinfo.fullstatus = 'Package not found'
        elif len(packagenames) > 1:
            logger.error('Multiple packages {} FOUND in Bioconductor {} {}: '
                         .format(packagename,
                                 bioc_release,
                                 view,
                                 ','.join(packagenames)))
            packinfo = PackInfo(packagename)
            packinfo.status = PackStatus.NOT_FOUND
            packinfo.fullstatus = 'Multiple packages found: ' \
                                  + ','.join(packagenames)
        else:
            # download tarball prior to create the PackInfo object
            dest = tempfile.mkdtemp()
            retVal = self.download_single(packagename,
                                          bioc_release,
                                          view,
                                          dest)
            if retVal == PackStatus.DOWNLOADED:
                gfpn = self._get_full_package_name(
                    bioc_release, view, packagename)
                fullpackagename = gfpn['full_package_name']
                packinfo = PackInfo(os.path.join(
                    dest,
                    "{}.tar.gz".format(fullpackagename)))
                packinfo.tempdir = dest
                packinfo.packagepath = Utils.concatpaths(
                    dest, "{}.tar.gz".format(fullpackagename))
                logger.debug("PACKINFO: " + str(packinfo.as_dict))
            else:
                packinfo = PackInfo(packagename)
                packinfo.tempdir = dest
                packinfo.status = PackStatus.DOWNLOAD_FAILED
                packinfo.fullstatus = 'Failed to download package ' \
                                      + packagename
            if dest and os.path.exists(dest) and not keeptempfiles:
                shutil.rmtree(dest)
            return packinfo
