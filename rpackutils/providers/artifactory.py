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

from ..provider import AbstractProvider
from ..packinfo import PackStatus

class ArtifactoryProvider(AbstractProvider):

    def __init__(self, baseurl, repos, auth):
        AbstractProvider.__init__(self)
        self.name = 'Artifactory'
        self._url = '{0}/api/storage/{1}'.format(
            baseurl, repos)
        self.repos = repos
        self._auth = auth
        # Testing connection to the provider
        if not self._test_connection():
            logger.warning(
                'Connection to provider: {0} for url: '
                '{1} not working...'.format(
                self.name, self._url))
        self._list_cache = None


    def _test_connection(self):
        r = requests.get(self._url, auth=self._auth)
        if r.status_code == 404:
            return False
        elif r.status_code == 200:
            return True
        return False

    def ls(self, full=False):
        if self._list_cache:
            return self._list_cache
        r = requests.get(self._url, auth=self._auth)
        if not r.status_code == 200:
           raise(IOError, 'Connection to resource failed.')
        content = r.json()
        if 'children' not in content:
            raise(NameError, 'No children found in JSON response')
        if not full:
            files = [x['uri'][1:] for x in content[
                'children'] if not x['folder']]
        return files

    def download(self, pack, dest=None):
        pass

    def push(self, pack, source, overwrite=False):
        logger.info('Pushing {0} to provider: {1} (repos: {2})...'.format(
            os.path.basename, self.name, self.repos))
        availables = self.ls(full=)


    def packinfo(self, pack):
        pass



