import os
#from io import BytesIO
import subprocess
import requests

ARTIFACTORY_URL = "ARTIFACTORY_URL"
ARTIFACTORY_USER = 'ARTIFACTORY_USER'
ARTIFACTORY_PWD = 'ARTIFACTORY_PASSWD'

class ArtifactoryHelperException(Exception):
    pass


class ArtifactoryHelper(object):
    def __init__(self, reponame):
        self._reponame = reponame
        self._api_url = "{0}/api/storage/{1}".format(
                ARTIFACTORY_URL, reponame)

    @property
    def reponame(self):
        return self._reponame

    def exists(self):
        r = requests.get(self._api_url, auth=(
            ARTIFACTORY_USER, ARTIFACTORY_PWD))
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
        r = requests.get(self._api_url, auth=(
            ARTIFACTORY_USER, ARTIFACTORY_PWD))
        if r.status_code == 404:
            raise ArtifactoryHelperException('Repository does not exist')
        if r.status_code == 200:
            return ArtifactoryHelper.listfiles(r.json())
        else:
            raise ArtifactoryHelperException(
                    'Error when connecting to Artifactory')


    def download(self, filename, dest):
        url = self.downloadurl(filename)
        #print('Downloading file at URL: {0}'.format(
            #url))
        with open(dest, 'wb') as handle:
            r = requests.get(url, auth=(ARTIFACTORY_USER, ARTIFACTORY_PWD), stream=True)
            if not r.ok:
                raise ArtifactoryHelperException(
                        'Failed to download file')
            for block in r.iter_content(1024):
                if not block:
                    break
                handle.write(block)

    def downloadurl(self, filename):
        return '{0}/{1}/{2}'.format(ARTIFACTORY_URL,
                self._reponame, filename)

    @staticmethod
    def listfiles(content):
        #TODO Change this implementation when File List REST call will be available
        if 'children' not in content:
            raise ArtifactoryHelperException('Not well formated JSON response')
        files = [x['uri'][1:] for x in content['children'] if not x['folder']]
        return files

    @staticmethod
    def deploy(repos, folderpath):
        files = [ os.path.join(folderpath, f) for f in os.listdir(
            folderpath) if os.path.isfile(os.path.join(folderpath, f)) ]
        for f in files:
            print('Deploying artifact: {0}'.format(f))
            cmd = 'cat {0} | curl -X PUT --data-binary @- -u {1}:{2} -i {3}'.format(
                    f, ARTIFACTORY_USER, ARTIFACTORY_PWD, '{0}/{1}/{2}'.format(
                        ARTIFACTORY_URL, repos, os.path.basename(f))
                    )
            res = subprocess.call(cmd, shell=True)
            if res != 0:
                raise ArtifactoryHelperException('Failed to deploy file: {0}'.format(
                    f))
