###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import pytest
from rpackutils.artifactory import ArtifactoryHelper


def test_custom_config():
    filename = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        'resources/rpackutils.conf')
    ah = ArtifactoryHelper("some-R-repository", filename)
    assert(ah.artifactory_url == "https://artifactory.local/artifactory")
    assert(ah.artifactory_user == "artifactoryUser")
    assert(ah.artifactory_pwd == "s3C437P4ssw@Rd")
    assert(ah.artifactory_cert == "/toto/Certificate_Chain.pem")
