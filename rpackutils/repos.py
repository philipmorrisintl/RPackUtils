###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import re
import shutil
import tarfile
import requests
import tempfile
from distutils.version import StrictVersion
from .artifactory import ArtifactoryHelper

class RRepositoryException(Exception):
    pass

class RRepository(object):
    def __init__(self, version, artifactoryConfig=None):
        self._repversion = version
        self._artifactoryConfig = artifactoryConfig
        self._ah = ArtifactoryHelper(self._repversion, artifactoryConfig)
        self._packs = {}
        self.initialize()

    @property
    def packages(self):
        ''' Get the list of available packages '''
        return self._packs.keys()

    def package_version(self, name):
        ''' Get the version of a package '''
        if name not in self._packs:
            raise RRepositoryException('Package not found in repos')
        return self._packs[name]['version']

    def packurl(self, name):
        ''' Get the url where to download the package '''
        if not name in self._packs:
            raise RRepositoryException('Package not in repos')
        return self._ah.downloadurl('{0}_{1}.tar.gz'.format(
            name, self.package_version(name)))

    @property
    def version(self):
        return self._repversion

    def create(self):
        pass

    def initialize(self):
        if not self._ah.exists():
            raise RRepositoryException('Repository {0} not found'.format(
                    self._ah.reponame
                ))
        files = self._ah.files
        for f in files:
            try:
                pname, pversion = self.parse_pack_name(f)
            except RRepositoryException:
                continue
                #print('Ignoring non R package: {0}'.format(f))
            # Overwriting with the last version of the package
            if pname in self._packs:
                if self._lt(self._packs[pname]['version'],
                        pversion):
                    self._packs[pname] = {'version': pversion}
            else:
                self._packs[pname] = {'version': pversion}

    def _lt(self, a, b):
        try:
            res = StrictVersion(a) < StrictVersion(b)
            return res
        except Exception:
            return False

    @staticmethod
    def parse_pack_name(name):
        spl = name.split('_')
        if not len(spl) == 2:
            raise RRepositoryException('Incorrect R package name')
        name = spl[0]
        try:
            pos = spl[1].index('.tar.gz')
        except ValueError:
            raise RRepositoryException(
                    'Wrong package extention')
        version = spl[1][:pos]
        return name, version

    def description(self, pack):
        version = self.package_version(pack)
        filename = '{0}_{1}{2}'.format(pack, version, '.tar.gz')
        dest = tempfile.mkstemp()
        folder = tempfile.mkdtemp()
        self._ah.download(filename, dest[1])
        try:
            tarf = tarfile.open(dest[1], 'r:gz')
            tarf.extract(member=os.path.join(pack, 'DESCRIPTION'),
                path=folder)
            tarf.close()
        except tarfile.ReadError:
            print('!!!! ERROR when reading tarfile for pack: {0}'.format(
                pack))
            print('!!!! tarfile: {0}'.format(dest[1]))
            return pack, self.package_version(pack), []
        descpath = os.path.join(folder, pack, 'DESCRIPTION')
        if not os.path.exists(descpath):
            raise RRepositoryException(
                    'No DESCRIPTION file found in the archive')
        f = open(descpath, 'r', encoding='utf-8', errors='ignore')
        content = f.readlines()
        f.close()
        os.remove(dest[1])
        shutil.rmtree(folder)
        return RRepository.parse_descfile(content)

    def download(self, pack, dest=None):
        version = self.package_version(pack)
        filename = '{0}_{1}{2}'.format(pack, version, '.tar.gz')
        if dest is None:
            dest = tempfile.mkstemp()[1]
        self._ah.download(filename, dest)
        return dest

    @staticmethod
    def parse_descfile(content):
        in_depends = False
        in_imports = False
        depends = None
        imports = None
        for line in content:
            change = False
            if ':' in line:
                change = True
                if in_depends:
                    in_depends = False
                if in_imports:
                    in_imports = False
            if line.startswith('Version:'):
                version = line
            elif line.startswith('Depends:'):
                depends = line.replace('\n', '')
                in_depends = True
            elif line.startswith('Imports:'):
                imports = line.replace('\n', '')
                in_imports = True
            elif line.startswith('Package:'):
                package = line
            if not change:
                if in_depends:
                    depends += line
                if in_imports:
                    imports += line

        version = version.strip().split(':')[1].strip()
        package = package.strip().split(':')[1].strip()
        if depends:
            depends = depends.strip().replace(' ', '')
            depends = depends.split(':')[1]
            depends = depends.split(',')
            depends = [x.strip() for x in depends]
            for i in range(len(depends)):
                if '(' in depends[i]:
                    depends[i] = depends[i][0:(depends[i].index('('))]
            depends = [x.strip() for x in depends]
        else:
            depends = []
        # Improve the following by factoring this ugly part...
        if imports:
            imports = imports.strip().replace(' ', '')
            imports = imports.split(':')[1]
            imports = imports.split(',')
            imports = [x.strip() for x in imports]
            for i in range(len(imports)):
                if '(' in imports[i]:
                    imports[i] = imports[i][0:(imports[i].index('('))]
            imports = [x.strip() for x in imports]
            depends.extend(imports)
            depends = set(depends)
            depends = list(depends)
        return package, version, depends
