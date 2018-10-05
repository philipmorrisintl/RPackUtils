###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

base_packages = [
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


# FUTURE: we may get the list of base packages
# from some CRAN/MRAN web page or from a real R environment?
#
# rownames(installed.packages(priority="base"))
# rownames(installed.packages(priority="recommended"))
#
# For now, it seems it's reasonnable to have the full list
# of base R packages no matter the version.
class RBasePackages:

    @staticmethod
    def getnames():
        return base_packages
