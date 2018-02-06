###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import configparser

class Config:
    """
    Holds configuration file properties
    """
    
    def __init__(self, filepath):
        self._config_file = filepath
        self._environment_config = configparser.ConfigParser()
        self._environment_config.read(self._config_file)
        
    def get(self, section, option):
        return self._environment_config.get(section, option).strip('"')
