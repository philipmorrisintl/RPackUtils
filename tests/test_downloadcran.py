###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import pytest
from rpackutils.mirror_cran import MirrorCRAN

# CRAN_DOWNLOAD_PATH='/home/sgubian/tmp/R_PACKAGES_3.2.2'
# BIOC_DOWNLOAD_PATH='/home/sgubian/tmp/BIOC_PACKAGES_3.2'

# @pytest.fixture
# def test_cran_packs_list():
    # l = get_cran_packs_list()
    # assert(len(l) > 0)
    # return l

# def test_bioc_packs_list():
    # l = get_bioc_packs_list()
    # assert(len(l) > 0)
    # return l

# # def test_download_cran():
    # # packs = cran_packs_list()
    # # download_cran_packs(packs, CRAN_DOWNLOAD_PATH)
    # # assert(len(os.listdir(CRAN_DOWNLOAD_PATH)) > 100)

# def test_download_bioc():
    # packs = get_bioc_packs_list()
    # download_bioc_packs(packs, BIOC_DOWNLOAD_PATH)
    # assert(len(os.listdir(BIOC_DOWNLOAD_PATH)) > 100)

# def test_deploy_cran():
    # deploy_cran_packs('R-3.2.2', CRAN_DOWNLOAD_PATH)
