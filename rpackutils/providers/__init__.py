###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

"""
For importing the available providers of R packages
"""

from .renvironment import REnvironment
from .nexus import Nexus
from .artifactory import Artifactory
from .cran import CRAN
from .bioconductor import Bioconductor
from .localrepository import LocalRepository

__all__ = [x for x in dir() if not x.startswith('_')]
