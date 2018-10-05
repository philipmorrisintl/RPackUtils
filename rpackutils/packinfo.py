###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import errno
import tempfile
import tarfile
import shutil
import codecs
import logging
from .utils import Utils
from .rbasepackages import RBasePackages
from .license import License

logger = logging.getLogger(__name__)

class ParsingError(RuntimeError):
    '''raise this on package filename parsing error'''

def enum(**enums):
    return type('Enum', (), enums)

PackStatus = enum(
    PARSED=0,
    DOWNLOADED=1,
    DOWNLOAD_FAILED=-1,
    DEPLOYED=2,
    DEPLOY_FAILED=-2,
    NOT_FOUND=-3,
    INVALID=-4,
)

#####################################################################
# Please note the attributes should not start with an '_' since the #
# as_dist() method is called to fetch node's attributes to generate #
# dependency graph with the networkx module. networkx prefers plain #
# clean names.                                                      #
#####################################################################

class PackInfo(object):
    
    def __init__(self, path):
        """
        Construct a PackInfo given a path to a R package archive tarball
        or to a folder where the package is either installed or has been
        extracted.
        An instance can also be created by giving a package name.
        In that case, no description file will be parsed.

        R DESCRIPTION file spec:
        https://cran.r-project.org/doc/manuals/r-release/R-exts.html#The-DESCRIPTION-file
        """
        self.name = os.path.basename(path)
        self.version = None
        self.packagepath = None
        self.status = None
        #  self.install_date = None
        self.fullstatus = None
        self.depends = None
        self.imports = None
        self.suggests = None
        self.license = None
        self.licenseclass = None
        self.installationisallowed = True
        self.installationwarning = False
        self.tempdir = None
        #  self.author = None
        #  self.title = None
        #  self.date = None
        istarball = "tar.gz" in os.path.basename(path)
        ispath = "/" in path
        if istarball:
            try:
                self.name, self.version = PackInfo._parse_package_name_version(path)
            except Exception as e:
                logger.error(
                    'Unexpected R package file name'
                    ' \"{0}\": '.format(path, e))
        elif ispath:
            self.name = os.path.basename(path)
            self.version = None
        else:
            self.name = path
            self.version = None
        descriptionfilepath = None
        folder = None
        if istarball:
            folder = tempfile.mkdtemp()
            try:
                tarf = tarfile.open(path, 'r:gz')
                tarf.extract(member=os.path.join(
                    self.name, 'DESCRIPTION'),
                             path=folder)
                tarf.close()
                descriptionfilepath = os.path.join(
                    folder, self.name, 'DESCRIPTION')
            except Exception as e:
                logger.error(
                    'Unexpected error while reading the tarball '
                    'for package: {0}, tarball: {1}, '
                    'error message: {2}'.format(self.name, path, e))
                self.status = PackStatus.INVALID
                self.fullstatus = e
        elif ispath:
            descriptionfilepath = os.path.join(path, 'DESCRIPTION')
        if descriptionfilepath:
            self._parse_descriptionfile(descriptionfilepath)
        if folder and os.path.exists(folder):
            shutil.rmtree(folder)

    @property
    def as_dict(self):
        return self.__dict__

    @property
    def dependslist(self):
        return self.depends if self.depends else []

    @property
    def importslist(self):
        return self.imports if self.imports else []

    @property
    def suggestslist(self):
        return self.suggests if self.suggests else []

    def dependencies(self, withBasePackages=False):
        """
        Returns an aggregated list of both imports and depends.

        :param withBasepackages: if True, remove all R base packages
        """
        all = self.importslist + self.dependslist
        if not withBasePackages:
            all = [x for x in all if x not in RBasePackages.getnames()]
        return all

    @property
    def filename(self):
        """
        filename as 'packagename_version.tar.gz'
        """
        return('{0}_{1}.tar.gz'.format(self.name, self.version))

    @property
    def tarball(self):
        """
        filename as 'packagename_version.tar.gz'
        """
        return('{0}_{1}.tar.gz'.format(self.name, self.version))

    @property
    def has_depends(self):
        if self.depends is None:
            return False
        return len(self.depends) > 0

    @property
    def has_imports(self):
        if self.imports is None:
            return False
        return len(self.imports) > 0

    @property
    def has_suggests(self):
        if self.suggests is None:
            return False
        return len(self.suggests) > 0

    @property
    def installation_is_allowed(self):
        return self.installationisallowed

    @property
    def installation_warning(self):
        return self.installationwarning

    @staticmethod
    def _parse_package_name_version(filepath):
        filename = os.path.basename(filepath)
        # we expect only 1 underscore
        spl = filename.split('_')
        if not len(spl) == 2:
            name = spl[0]
            raise ParsingError('Unrecognized R package file name')
        name = spl[0]
        try:
            pos = spl[1].index('.tar.gz')
        except ValueError:
            raise ParsingError(
                    'Wrong package extention')
        version = spl[1][:pos]
        return name, version

    def _parse_descriptionfile(self, descriptionfilepath):
        if not os.path.exists(descriptionfilepath):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    descriptionfilepath)
        self._do_parse_descriptionfile(descriptionfilepath)

    def _do_parse_descriptionfile(self, descriptionfilepath):
        if not os.path.exists(descriptionfilepath):
            self.status = PackStatus.INVALID
            self.fullstatus = 'DESCRIPTION file not FOUND'
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    descriptionfilepath)
        lines = open(descriptionfilepath,
                     'r',
                     encoding='utf-8',
                     errors='ignore').readlines()
        cleanlines = [Utils.cleanCRLFTAB(line) for line in lines]
        context = None
        d = {
            'package': None,
            'depends': None,
            'imports': None,
            'suggests': None,
            'version': None,
            'license': None
        }
        self._read_desc_line_recurse(d, context, cleanlines, 0)
        self.name = d['package']
        self.depends = PackInfo._clean_children(d['depends'])
        self.imports = PackInfo._clean_children(d['imports'])
        self.suggests = PackInfo._clean_children(d['suggests'])
        self.version = d['version']
        self.license = d['license']
        # compute the license-class
        lic = License(d['license'])
        self.licenseclass = lic.license_class
        self.installationisallowed = lic.installation_is_allowed
        self.installationwarning = lic.installation_warning

    @staticmethod
    def _clean_children(s):
        if s:
            lst = s.strip().split(',')
            lst = [x.strip() if '(' not in x else x[:x.index(
                '(')].strip() for x in lst]
            lst = [x for x in lst if x]
            return lst
        else:
            return []

    @staticmethod
    def _is_context(lines, index):
        return(':' in lines[index])

    def _newcontext_or_endofcontent(self, d, context, lines, index):
        if PackInfo._is_context(lines, index+1):
            # end of content, a new context follows
            self._read_desc_line_recurse(d, None, lines, index+1)
        else:
            # more content ahead
            self._read_desc_line_recurse(d, context, lines, index+1)

    def _read_desc_line_recurse(self, d, context, lines, index):
        if context is None:
            # anchor on a new context
            if PackInfo._is_context(lines, index):
                context = lines[index].split(':')[0].lower()
                self._read_desc_line_recurse(d, context, lines, index)
        else:
            if PackInfo._is_context(lines, index):
                # we are starting to collect content for the current context
                d[context] = ' '.join(lines[index].split(':')[1:]).strip()
                if index+1 < len(lines):
                    self._newcontext_or_endofcontent(d, context, lines, index)
                # EOF
            else:
                # continue to collect data for the current context
                d[context] += lines[index].strip()
                if index+1 < len(lines):
                    self._newcontext_or_endofcontent(d, context, lines, index)
                # EOF
