###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import sys
import traceback
import requests
import tempfile
from bs4 import BeautifulSoup
from .artifactory import ArtifactoryHelper
import re
import multiprocessing
import time


class MirrorCRAN():

    def __init__(self):
        self.MRAN_SNAPSHOTS_URL = "https://mran.revolutionanalytics.com/snapshot/"
        # with a snapshot "2014-09-08", the url is:
        # https://mran.revolutionanalytics.com/snapshot/2014-09-08/src/contrib/

    def get_mran_packages_url(self, snapshot_date):
        return self.MRAN_SNAPSHOTS_URL + snapshot_date + "/src/contrib/"

    def get_mran_package_url(self, snapshot_date, package_name):
        return '{0}/{1}'.format(
            self.get_mran_packages_url(snapshot_date),
            package_name)

    def _process_mran_snapshot(self, href, rversion, date):
        r2 = requests.get(href)
        soup2 = BeautifulSoup(r2.text, 'html.parser')
        anchors2 = soup2.findAll('a')
        regex = re.compile(".*(R-).*(\.tar\.gz)")
        # example of matches:
        # ['<a href="src/base/R-3/R-3.1.1.tar.gz">R-3.1.1.tar.gz']
        matches = [m.group(0) for l in anchors2
                   for m in [regex.search(str(l))] if m]
        if not len(matches) == 1:
            print("Snapshot \"{0}\": " \
                      "Could not parse the R version number " \
                      "from the html page!".format(date))
            sys.stdout.flush()
            return {"status": "error", "version": "?", "date": date}
        soup3 = BeautifulSoup(matches[0], 'html.parser')
        version_full = str(soup3.findAll('a')[0].contents[0])
        # remove "R-" and ".tar.gz" from "R-X.Y.Z.tar.gz"
        version = version_full.replace("R-", "").replace(".tar.gz", "")
        if version == rversion or rversion is None:
            # sys.stdout.write('.')
            # sys.stdout.flush()
            return {"status": "ok", "version": version, "date": date}
        else:
            # print('Snapshot \"{0}\": skipping R version {1}' \
            #           .format(date, version))
            # sys.stdout.flush()
            return {"status": "skipped", "version": version, "date": date}

    def get_mran_snapshots_list(self, procs, rversion=None):
        starttime = time.time()
        # hold "R version to snashot date"
        version2dates = dict()
        # fetch the snapshot dates list
        r1 = requests.get(self.MRAN_SNAPSHOTS_URL)
        if not r1.status_code == 200:
            print("Cannot open MRAN snapshots URL, HTTP status code {0}: {1}" \
                      .format(r1.status_code, self.MRAN_SNAPSHOTS_URL))
        soup = BeautifulSoup(r1.text, 'html.parser')
        # example of 1 anchor: "<a href="2014-08-18_0233/">2014-08-18_0233/</a>"
        anchors = soup.findAll('a')
        # example of 1 href:
        # u'https://mran.revolutionanalytics.com/snapshot/2014-09-08/'
        # we skip the 1st one which is "../"
        hrefs = [self.MRAN_SNAPSHOTS_URL + anchor['href'] + "banner.shtml"
                 for anchor in anchors][1:]
        dates = [str(anchor.contents[0]).replace('/','')
                 for anchor in anchors][1:]
        print("{0} snapshot dates found.".format(len(dates)))
        pool = multiprocessing.Pool(processes=procs)
        # submit all processes at once and retrieve the results
        # as soon as they are finished
        results = [pool.apply_async(self._process_mran_snapshot,
                                    args=(hrefs[i], rversion, dates[i])) \
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
        print("Snapshots processed/matching the specified " \
                  "R version ({0}), skipped ({1}), errors ({2})." \
                  .format(totalprocessed,
                          totalskipped,
                          totalerrors))
        print("\n")
        endtime = time.time()
        timeelapsed = int(endtime - starttime)
        print('Time elapsed: {0} seconds.'.format(timeelapsed))
        return version2dates

    def get_cran_packs_list(self, snapshot_date):
        r = requests.get(self.get_mran_packages_url(snapshot_date))
        if not r.status_code == 200:
            print("Cannot open MRAN packages URL, HTTP status code {0}: {1}" \
                      .format(r.status_code, self.MRAN_SNAPSHOTS_URL))
        soup = BeautifulSoup(r.text, 'html.parser')
        packs = []
        anchors = soup.findAll('a')
        allpacks = [str(anchor['href']) for anchor in anchors][1:]
        # select tarballs only (R packages)
        regex = re.compile(".*(\.tar\.gz)")
        packs = [m.group(0) for l in allpacks for m in [regex.search(str(l))] if m]
        if not packs:
            print("Could not parse the R package names (tarballs) from the html page!")
        print("Number of R packages available: {0}".format(len(packs)))
        return packs

    def download(self, url, pack, targetpath):
        print('Downloading R package: {0}'.format(pack))
        retVal = 'ok'
        try:
            r = requests.get(url, stream=True)
            with open(targetpath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
            print('Done downloading R package: {0}'.format(pack))
            retVal = 'ok'
        except:
            error_message = 'Error downloading R package: {0}\n{1}\n{2}\n{3}' \
                .format(pack,
                        url,
                        sys.exc_info()[0],
                        traceback.extract_tb(sys.exc_info()[2]))
            print(error_message)
            retVal = error_message
        return retVal    

    def download_cran_packs(self, snapshot_date, packs, tofolder, procs):
        starttime = time.time()
        totalnumofpacks = len(packs)
        totaldownloaded = 0
        urls = []
        targetpaths = []
        print('Selecting the MRAN snapchot: {0}'.format(snapshot_date))
        for idx, pack in enumerate(packs):
            urls.append( self.get_mran_package_url(snapshot_date, pack) )
            targetpaths.append( os.path.join(tofolder, pack) )
        # multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=procs)
        # submit all processes at once and retrieve the results
        # as soon as they are finished
        results = [pool.apply_async(self.download,
                                    args=(urls[i], packs[i], targetpaths[i])) \
                       for i in range(0, totalnumofpacks)]
        retVals = [res.get() for res in results]
        # avoid zombies and release the memory
        pool.close()
        for retVal in retVals:
            if retVal == 'ok':
                totaldownloaded = totaldownloaded+1
        print("{0}/{1} packages done." \
                  .format(totaldownloaded,
                          totalnumofpacks))
        endtime = time.time()
        timeelapsed = int(endtime - starttime)
        print('Time elapsed: {0} seconds.'.format(timeelapsed))
        if totaldownloaded < totalnumofpacks:
            print('Failed to download all R packages')

    def deploy_cran_packs(self, repos, folder, procs, artifactoryConfig):
        ah = ArtifactoryHelper(artifactoryConfig)
        ah.deploy(repos, folder, procs)
