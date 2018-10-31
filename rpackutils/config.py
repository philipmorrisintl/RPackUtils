###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import errno
import configparser
import logging

logger = logging.getLogger(__name__)


class Config:
    """
    Holds configuration file properties
    """
    def __init__(self, filepath):
        if not os.path.isfile(filepath):
            logger.error('Configuration file \"{0}\" not found!'
                         .format(filepath))
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    filepath)
        if not os.access(filepath, os.R_OK):
            logger.error('Configuration file \"{0}\" is not readable(no access)!'
                         .format(filepath))
            raise PermissionError(errno.EACCESS,
                                  os.strerror(errno.EACCESS),
                                  filepath)
        self._config_file = filepath
        self._environment_config = configparser.ConfigParser()
        self._environment_config.read(self._config_file)

    def get(self, section, option):
        return self._environment_config.get(section, option).strip('"')

    def getboolean(self, section, option):
        return self._environment_config.getboolean(
            section, option, fallback=False)
