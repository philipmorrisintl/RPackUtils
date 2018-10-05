###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
from .packinfo import PackInfo
from .packinfo import PackStatus
from .utils import Utils
from abc import ABCMeta, abstractmethod, abstractproperty
import inspect
import time
import logging
import requests

logger = logging.getLogger(__name__)


class AbstractProvider():
    __metaclass__ = ABCMeta

    def __init__(self, name, baseurl, repos):
        self.name = name
        self.baseurl = baseurl
        self.repos = repos
        super().__init__()

    @abstractmethod
    def download_single(self, packagename, dest):
        pass

    @abstractmethod
    def download_multiple(self, packagenames, dest):
        pass

    @abstractmethod
    def upload_single(self, filepath, repo, overwrite=False,
                      overwritepackages=None):
        pass

    @abstractmethod
    def upload_multiple(self, filepaths, repos, overwrite=False,
                        overwritepackages=None):
        pass

    @abstractmethod
    def packinfo(self, packagename):
        pass

    @abstractmethod
    def ls(self, packagenamesonly=False):
        pass

    @abstractmethod
    def find(self, pattern):
        pass


class AbstractREnvironment(AbstractProvider):
    __metaclass__ = ABCMeta

    def __init__(self, name, rhome, librarypath):
        super().__init__(name, rhome, [librarypath])

    @abstractmethod
    def packinfo(self, packagename, keeptempfiles=False):
        folders = self.find(packagename)
        if len(folders) == 0:
            logger.error('Package {} not FOUND'.format(packagename))
            packinfo = PackInfo(packagename)
            packinfo.status = PackStatus.NOT_FOUND
            packinfo.fullstatus = 'Package not found'
        # this is impossible
        # elif len(folders) > 1:
        else:
            repofullpath = Utils.concatpaths(self.baseurl, self.repos[0])
            packinfo = PackInfo(Utils.concatpaths(repofullpath, folders[0]))
            packinfo.status = PackStatus.DOWNLOADED
        return packinfo

    @abstractmethod
    def install_dryrun(self, packnode, dest, overwrite=False,
                       overwritepackages=None):
        '''
        This method is used to simulate the installion of
        packages and is called from the Depsmanager class.
        '''
        pass

    @abstractmethod
    def install(self, packnode, overwrite=False,
                overwritepackages=None):
        '''
        This method is used to install packages and is called from
        the Depsmanager class.
        '''
        pass
    
    @abstractmethod
    def download_single(self, pack, dest):
        raise NotImplementedError(
            'Downloading package from a R environment is not implemented')

    @abstractmethod
    def download_multiple(self, packs, dest):
        raise NotImplementedError(
            'Downloading package from a R environment is not implemented')


class AbstractPackageRepository(AbstractProvider):
    __metaclass__ = ABCMeta

    def __init__(self, name, baseurl, repos):
        super().__init__(name, baseurl, repos)

    @abstractmethod
    def check_connection(self, numtries=3, verbose=True):
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
                if(verbose):
                    logger.info('Checking connection to {0} ...'
                                .format(self.baseurl))
                retVal = (requests.get(self.baseurl).status_code == 200)
            except Exception as e:
                retVal = False
                logger.error('FATAL: Cannot connect to {0}: {1}'
                             .format(self.baseurl, e))
                time.sleep(3)
                continue
            break
        if retVal:
            if(verbose):
                logger.info('Connection to {0} established.'
                            .format(self.baseurl))
        return retVal
