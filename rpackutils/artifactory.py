###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
#from io import BytesIO
import subprocess
import requests
from rpackutils.config import Config
import multiprocessing
import time


class ArtifactoryHelperException(Exception):
    pass


class ArtifactoryHelper(object):
    def __init__(self, reponame, artifactoryConfig):
        self._reponame = reponame
        # read configuation file
        config = Config(artifactoryConfig)
        self.artifactory_url = config.get("global", "artifactory.url")
        self.artifactory_user = config.get("global", "artifactory.user") 
        self.artifactory_pwd = config.get("global", "artifactory.pwd")
        self.artifactory_cert = config.get("global", "artifactory.cert")
        self._api_url = "{0}/api/storage/{1}".format(
            self.artifactory_url, reponame)

    @property
    def reponame(self):
        return self._reponame

    def _do_request(self, url, stream=False):
        r = requests.get(
            url,
            auth=(self.artifactory_user, self.artifactory_pwd),
            verify=self.artifactory_cert,
            stream=stream)
        return r

    def exists(self):
        r = self._do_request(self._api_url)
        if r.status_code == 404:
            return False
        elif r.status_code == 200:
            return True
        else:
            print(r.text)
            raise ArtifactoryHelperException(
                    'Error when connecting to Artifactory: {0}'.format(
                        r.status_code))

    @property
    def files(self):
        ''' Return the available files available in that repos as a list'''
        #TODO Replace this call by the File List one that is more appropriate
        # It has arguments like deep, listFolders, etc. but only in pro version
        r = self._do_request(self._api_url)
        if r.status_code == 404:
            raise ArtifactoryHelperException('Repository does not exist')
        if r.status_code == 200:
            return ArtifactoryHelper.listfiles(r.json())
        else:
            raise ArtifactoryHelperException(
                    'Error when connecting to Artifactory')


    def download(self, filename, dest):
        url = self.downloadurl(filename)
        #  print('Downloading file at URL: {0}'.format(
                #  url))
        with open(dest, 'wb') as handle:
            r = self._do_request(url, stream=True)
            if not r.ok:
                raise ArtifactoryHelperException(
                        'Failed to download file')
            for block in r.iter_content(1024):
                if not block:
                    break
                handle.write(block)

    def downloadurl(self, filename):
        return '{0}/{1}/{2}'.format(self.artifactory_url,
                self._reponame, filename)

    @staticmethod
    def listfiles(content):
        #TODO Change this implementation when File List REST call will be available
        if 'children' not in content:
            raise ArtifactoryHelperException('Not well formated JSON response')
        files = [x['uri'][1:] for x in content['children'] if not x['folder']]
        return files

    def deployArtifact(self, filepath, repo, url):
        print('Deploying artifact: {0}'.format(filepath))
        cmd = 'curl --cacert {0} -X PUT {1} --data-binary {2}'.format(
            self.artifactory_cert, url, filepath)
        res = subprocess.call(cmd, shell=True)
        retVal = 'ok'
        if res != 0:
            retval = 'Failed to deploy file: {0}'.format(filepath)
            # raise ArtifactoryHelperException(retval)
            print(retVal)
        print('Successfully deployed file: {0}'.format(filepath))
        return retVal

    def deploy(self, repo, folderpaths, procs=1, properties=None):
        starttime = time.time()
        files = [ os.path.join(folderpaths, f) for f in os.listdir(
            folderpaths) if os.path.isfile(os.path.join(folderpaths, f)) ]
        totalnumoffiles = len(files)
        totaldeployed = 0
        urls = []
        for idx, f in enumerate(files):
            targetUrl = self.artifactory_url.replace(
                '://', '://{0}:{1}@'.format(self.artifactory_user,
                                            self.artifactory_pwd))
            targetUrl = '{0}/{1}/{2}'.format(targetUrl,
                                             repo,
                                             os.path.basename(f))
            if properties:
                # https://www.jfrog.com/confluence/display/RTF/Using+Properties+in+Deployment+and+Resolution
                if properties[idx]:
                    properties_matrix = ""
                    for k in properties[idx].keys():
                        properties_matrix += ";"
                        properties_matrix += "{0}={1}".format(k, properties[k])
                    targetUrl += properies_matrix
            urls.append(targetUrl)
        # multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=procs)
        # submit all processes at once and retrieve the results
        # as soon as they are finished
        results = [pool.apply_async(self.deployArtifact,
                                    args=(files[i], repo, urls[i])) \
                       for i in range(0, totalnumoffiles)]
        retVals = [res.get() for res in results]
        # avoid zombies and release the memory
        pool.close()
        endtime = time.time()
        timeelapsed = int(endtime - starttime)
        for retVal in retVals:
            if retVal == 'ok':
                totaldeployed = totaldeployed+1
        print("{0}/{1} artifacts deployed." \
                  .format(totaldeployed,
                          totalnumoffiles))
        print('Time elapsed: {0} seconds.'.format(timeelapsed))
        if totaldeployed < totalnumoffiles:
            print('Failed to deploy all artifacts')
