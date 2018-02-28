###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import sys
import requests
import tempfile
from bs4 import BeautifulSoup
from .artifactory import ArtifactoryHelper
import json
import re
import multiprocessing
import time

class MirrorBioc():

    def __init__(self):
        self.BIOC_CHKRES_URL = 'https://www.bioconductor.org/' \
            'checkResults/'
        
        self.BIOC_VIEW_URL = 'https://www.bioconductor.org/' \
            'packages/{0}/BiocViews.html{1}'

        self.POSSIBLE_VIEWS = ['software', 'experimentData', 'annotationData']
        
        self.BIOC_SOFTWARE_URL = 'https://www.bioconductor.org/' \
            'packages/json/{0}/bioc/packages.js'
        self.BIOC_EXPERIMENTDATA_URL = 'https://www.bioconductor.org/' \
            'packages/json/{0}/data/experiment/packages.js'
        self.BIOC_ANNOTATIONDATA_URL = 'https://www.bioconductor.org/' \
            'packages/json/{0}/data/annotation/packages.js'
        
        self.BIOC_SOFTWARE_PAGE_URL = 'https://www.bioconductor.org/' \
            'packages/{0}/bioc/html/{1}.html'
        self.BIOC_EXPERIMENTDATA_PAGE_URL = 'https://www.bioconductor.org/' \
            'packages/{0}/data/experiment/html/{1}.html'
        self.BIOC_ANNOTATIONDATA_PAGE_URL = 'https://www.bioconductor.org/' \
            'packages/{0}/data/annotation/html/{1}.html'
        
        self.BIOC_DOWNLOAD_SOFTWARE_URL = 'https://www.bioconductor.org/' \
            'packages/{0}/bioc/src/contrib/{1}.tar.gz'
        self.BIOC_DOWNLOAD_EXPERIMENTDATA_URL = 'https://www.bioconductor.org/' \
            'packages/{0}/data/experiment/src/contrib/{1}.tar.gz'
        self.BIOC_DOWNLOAD_ANNOTATIONDATA_URL = 'https://www.bioconductor.org/' \
            'packages/{0}/data/annotation/src/contrib/{1}.tar.gz'

    def get_bioc_releases_list(self):
        r1 = requests.get(self.BIOC_CHKRES_URL)
        if not r1.status_code == 200:
            print("Cannot open BIOC checkResults URL, HTTP status code {0}: {1}" \
                      .format(r1.status_code, self.BIOC_CHKRES_URL))
        soup = BeautifulSoup(r1.text, 'html.parser')
        # <h3>Bioconductor X.Y (release)</h3>
        anchors = soup.findAll('h3')
        releases = [str(anchor.contents[0]) for anchor in anchors]
        print("\n".join(releases))
    
    def _get_bioc_json_urls(self, bioc_release):
        softwareUrl = self.BIOC_SOFTWARE_URL.format(bioc_release)
        annotationDataUrl = self.BIOC_ANNOTATIONDATA_URL.format(bioc_release)
        experimentDataUrl = self.BIOC_EXPERIMENTDATA_URL.format(bioc_release)
        return {'software': softwareUrl,
                'annotationData': annotationDataUrl,
                'experimentData': experimentDataUrl}

    def _get_bioc_package_page_urls(self, bioc_release, packageName, view):
        if view == 'software':
            softwareUrl = self.BIOC_SOFTWARE_PAGE_URL.format(
                bioc_release, packageName)
            return softwareUrl
        elif view == 'experimentData':
            experimentDataUrl = self.BIOC_EXPERIMENTDATA_PAGE_URL.format(
                bioc_release, packageName)
            return experimentDataUrl
        elif view == 'annotationData':
            annotationDataUrl = self.BIOC_ANNOTATIONDATA_PAGE_URL.format(
                bioc_release, packageName)
            return annotationDataUrl
        else:
            print('The view must be one of \"software\", ' \
                      '\"experimentData\" or \"annotationData\".')
            exit(-1)

    def _get_bioc_package_download_urls(self, bioc_release, packageName, view):
        if view == 'software':
            softwareUrl = self.BIOC_DOWNLOAD_SOFTWARE_URL.format(
                bioc_release, packageName)
            return softwareUrl
        elif view == 'experimentData':
            experimentDataUrl = self.BIOC_DOWNLOAD_EXPERIMENTDATA_URL.format(
                bioc_release, packageName)
            return experimentDataUrl
        elif view == 'annotationData':
            annotationDataUrl = self.BIOC_DOWNLOAD_ANNOTATIONDATA_URL.format(
                bioc_release, packageName)
            return annotationDataUrl
        else:
            print('The view must be one of \"software\", ' \
                      '\"experimentData\" or \"annotationData\".')
            exit(-1)

    def _get_full_package_name(self, package_page_url, package_name):
        r = requests.get(url=package_page_url)
        if not r.status_code == 200:
            print("Cannot open the BIOC package page URL, HTTP status code {0}: {1}" \
                      .format(r.status_code, package_page_url))
            return {"status": "error",
                    "url": package_page_url,
                    "package_name": package_name,
                    "name": None}
        soup = BeautifulSoup(r.text, 'html.parser')
        anchors = soup.findAll('a')
        hrefs = [anchor['href'] for anchor in anchors \
                     if 'href' in anchor.attrs.keys()]
        package_source_link = [href for href in hrefs \
                                   if '.tar.gz' in href]
        # example result: ['../src/contrib/ABAData_1.4.0.tar.gz']
        if not len(package_source_link) == 1:
            print('Could not find the package source link from {0}.' \
                      .format(package_page_url))
            return {"status": "error",
                    "url": package_page_url,
                    "package_name": package_name,
                    "name": None}
            exit(-1)
        package_name = package_source_link[0] \
            .replace('../src/contrib/', '') \
            .replace('.tar.gz', '')
        return {"status": "ok",
                "url": package_page_url,
                "package_name": package_name,
                "name": package_name}

    def get_bioc_packs_list(self, bioc_release, view, procs):
        starttime = time.time()
        if view not in self.POSSIBLE_VIEWS:
            print('The view must be one of {0}.'\
                      .format(",".join(self.POSSIBLE_VIEWS)))
            exit(-1)
        url = self._get_bioc_json_urls(bioc_release)[view]
        packs = []
        rjs = requests.get(url=url)
        if not rjs.status_code == 200:
            print("Cannot open BIOC view URL, HTTP status code {0}: {1}" \
                      .format(rjs.status_code, url))
        print('Fetching list of BIOC {0} packages...'.format(view))
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
        packagePageUrls = []
        for c in json_obj['content']:
            packageName = c[0]
            packageNames.append(packageName)
            packagePageUrl = self._get_bioc_package_page_urls(
                bioc_release, c[0], view)
            packagePageUrls.append(packagePageUrl)
        rjs.close()
        totalNumOfPackages = len(packageNames)
        print("{0} {1} pakages found.".format(totalNumOfPackages, view))
        pool = multiprocessing.Pool(processes=procs)
        # submit all processes at once and retrieve the results
        # as soon as they are finished
        results = [pool.apply_async(self._get_full_package_name,
                                    args=(packagePageUrls[i], packageNames[i])) \
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
        print("Package pages processed to get version numbers " \
                  "({0}), errors ({1})." \
                  .format(totalprocessed,
                          totalerrors))
        endtime = time.time()
        timeelapsed = int(endtime - starttime)
        print('Time elapsed: {0} seconds.\n'.format(timeelapsed))
        if totalerrors > 0:
            print('Could not extract all packages versions. Exiting.')
            exit(-1)
        return packageFullNames

    def download(self, url, pack, targetpath, packtype):
        print('Downloading BIOC R {0}: {1}'.format(packtype, pack))
        retVal = 'ok'
        try:
            r = requests.get(url, stream=True)
            with open(targetpath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
            print('Done downloading BIOC R {0}: {1}'.format(packtype, pack))
            retVal = 'ok'
        except:
            error_message = 'Error downloading R {0}: {1}\n{2}\n{3}' \
                .format(packtype,
                        pack,
                        sys.exc_info()[0],
                        traceback.extract_tb(sys.exc_info()[2]))
            print(error_message)
            retVal = error_message
        return retVal

    def spawn_downloads(self, procs, urls, packs, targetpaths, packtype):
        starttime = time.time()
        totalnumofpacks = len(packs)
        totaldownloaded = 0
        pool = multiprocessing.Pool(processes=procs)
        # submit all processes at once and retrieve the results
        # as soon as they are finished
        results = [pool.apply_async(self.download,
                                    args=(urls[i], packs[i],
                                          targetpaths[i], packtype)) \
                       for i in range(0, totalnumofpacks)]
        retVals = [res.get() for res in results]
        # avoid zombies and release the memory
        pool.close()
        for retVal in retVals:
            if retVal == 'ok':
                totaldownloaded = totaldownloaded+1
        print("{0}/{1} BIOC {2} done." \
                  .format(totaldownloaded,
                          totalnumofpacks,
                          packtype))
        endtime = time.time()
        timeelapsed = int(endtime - starttime)
        print('Time elapsed: {0} seconds.'.format(timeelapsed))
        if totaldownloaded < totalnumofpacks:
            print('Failed to download all BIOC R {0}'.format(packtype))

    def download_bioc_packs(self, packs, bioc_release, view, tofolder, procs):
        packtype = view
        urls = []
        targetpaths = []
        for pack in packs:
            url = self._get_bioc_package_download_urls(bioc_release, pack, view)
            urls.append(url)
            targetpath = os.path.join(tofolder, '{0}.tar.gz'.format(pack))
            targetpaths.append(targetpath)
        self.spawn_downloads(procs, urls, packs, targetpaths, packtype)

    def deploy_bioc_packs(self, repos, folder, procs, artifactoryConfig=None):
        ah = ArtifactoryHelper(artifactoryConfig)
        ah.deploy(repos, folder, procs)
