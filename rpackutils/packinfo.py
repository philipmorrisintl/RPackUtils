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

import os
from pygments import lex
from pygments.token import *
# R DESCRIPTION file is based on Debian control files syntax
from pygments.lexers.installers import DebianControlLexer

BASE_PACKAGES = [
            'R',
            'utils',
            'mgcv',
            'foreign',
            'survival',
            'tcltk',
            'translations',
            'cluster',
            'MASS',
            'grDevices',
            'nlme',
            'grid',
            'base',
            'compiler',
            'KernSmooth',
            'class',
            'spatial',
            'boot',
            'tools',
            'lattice',
            'nnet',
            'graphics',
            'methods',
            'codetools',
            'stats4',
            'rpart',
            'datasets',
            'stats',
            'splines',
            'parallel',
            'Matrix',
        ]


def enum(**enums):
    return type('Enum', (), enums)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


PackStatus = enum(
        DOWNLOADED=1,
        DOWNLOAD_FAILED=-1,
        DEPLOYED=2,
        DEPLOY_FAILED=-2,
        NOT_FOUND=-3,
        INVALID=-4,
        )


class PackInfo(object):
    def __init__(self, name, version=None):
        self.name = name
        #  self.location = None
        self.version = version
        self.status = None
        #  self.install_date = None
        self.fullstatus = None
        self.provider = None
        self.repos = None
        self.depends = None
        self.imports = None
        #  self.author = None
        #  self.title = None
        #  self.date = None

    @property
    def as_dict(self):
        return self.__dict__

    @property
    def filename(self):
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
        return self.imports is not None or len(self.imports) > 0 

def update_from_desc(pack, filepath):
    if not os.path.exists(filepath):
        pack.status = PackStatus.INVALID
        pack.fullstatus = 'DESCRIPTION file not FOUND'
        raise(IOError, 'DESCRIPTION file not found')
    desc = parse_description(filepath)
    pack.version = desc['version']
    if desc['depends']:
        pack.depends = _clean_children(desc['depends'])
    if desc['imports']:
        pack.imports = _clean_children(desc['imports'])
    pack.status = PackStatus.DEPLOYED

def _clean_children(s):
    lst = s.strip().split(',')
    lst = [x.strip() if not '(' in x else x[:x.index(
        '(')].strip() for x in lst]
    lst = [x for x in lst if x]
    return lst 

def parse_description(fp):
    lines = open(fp, 'r').readlines()
    context = None
    d = {
        'package': None,
        'depends': None,
        'imports': None,
        'version': None,
    }
    for l in lines:
        words = l.split()
        first = words[0]
        if first[0].isalpha() and ':' in first:
            context = first[:-1].lower()
            del words[0]
        if context in ['package', 'version']:
            d[context] = words[0]
            continue
        if context == 'depends' or context == 'imports':
            content = ' '.join(words)
            if d[context] is None:
                d[context] = ''
            d[context] += content
    return d

