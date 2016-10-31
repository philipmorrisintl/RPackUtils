##############################################################################
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
##############################################################################
# -*- coding: utf-8 > -*-
__author__ = "Sylvain Gubian"
__copyright__ = "Copyright 2016, PMP SA"
__license__ = "GPL2.0"
__email__ = "Sylvain.Gubian@pmi.com"

import inspect


class AbstractProvider(object):

    def __init__(self):
        self.baseurl = None
        self.repos = None
        self.name = None

    def download(self, pack, dest=None):
        pass

    def push(self, pack, source, overwrite=False):
        pass

    def packinfo(self, pack):
        pass


class Provider(object):
    def __init__(self, name):
        self.name = name
        providers = [x[0][0:x[0].index('Provider')] for x in self.providers()]
        if name not in providers:
            raise(ValueError, 'Provider {} not available'.format(name))
        index= providers.index(name)
        klass = self.providers()[index][1]
        self.provider = klass()

    @property
    def baseurl(self):
        return self.provider.baseurl

    @property
    def repos(self):
        return self.provider.repos

    @staticmethod
    def providers():
        import providers as pdrs
        l = inspect.getmembers(pdrs, inspect.isclass)
        return l

    def download(self, pack, dest=None):
        self.provider.download(pack, dest)

    def push(self, pack, source, overwrite=False):
        self.provider.push(pack, source)

    def packinfo(self, pack):
        self.provider.packinfo(pack)






