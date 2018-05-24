###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import logging

logger = logging.getLogger(__name__)

BLACKLISTED_LICENSES = [
    'ACADEMIC FREE', 'AFL',
    'AGPL', 'AFFERO',
    'APPLE',
    'OPEN SOFTWARE',
    'NON-PROFIT',
    'REALNETWORKS',
    'RECIPROCAL'
]

RESTRICTED_LICENSES = [
    'AMAZON',
    'ARTISTIC',
    'CDDL', 'COMMON DEVELOPMENT AND DISTRIBUTION',
    'CPAL', 'COMMON PUBLIC ATTRIBUTION',
    'CC BY-SA', 'CREATIVE COMMONS ATTRIBUTION-SHAREALIKE',
    'EPL', 'ECLIPSE PUBLIC',
    'GNU GENERAL PUBLIC', 'GPL',
    'GNU LESSER GENERAL PUBLIC', 'LGPL',
    'JAVASCRIPT OBJECT NOTATION', 'JSON',
    'MICROSOFT RECIPROCAL', 'MS-RL',
    'MOZILLA PUBLIC LICENSE', 'MPL',
    'Q PUBLIC',
    'IBM PUBLIC'
]

class License:

    def __init__(self, name):
        self._name = name
        self._restricted = False
        self._blacklisted = False
        self._license_class = None
        self._check()

    @property
    def restricted(self):
        return self._restricted

    @property
    def blacklisted(self):
        return self._blacklisted

    @property
    def license_class(self):
        return self._license_class

    @property
    def installation_is_allowed(self):
        """
        Allows or denies the installation
        """
        return(not self._blacklisted)

    @property
    def installation_warning(self):
        """
        Tells if a warning has to be issued to the user
        """
        return(not self._restricted)

    def _check(self):
        self._blacklisted = any(
            ss in self._name.upper() for ss in BLACKLISTED_LICENSES
        )
        self._restricted = any(
            ss in self._name.upper() for ss in RESTRICTED_LICENSES
        )
        # compute the license-class
        self._license_class = 'ALLOWED'
        if(self._blacklisted):
            self._license_class = 'BLACKLISTED'
        if(self._restricted):
            self._license_class = 'RESTRICTED'
