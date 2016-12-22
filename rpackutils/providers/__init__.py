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

"""
For importing the available providers of R packages
"""

from .local import LocalProvider
from .nexus import NexusProvider
from .artifactory import ArtifactoryProvider
from .cran import CRANProvider
from .bioc import BiocProvider

__all__ = [x for x in dir() if not x.startswith('_')]
