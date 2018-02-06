###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import sys
import requests
import tempfile
import shutil
import requests
import pytest
from rpackutils.mirror_bioc import MirrorBioc
from rpackutils.mirror_cran import MirrorCRAN


# def test_mran_packages_url():
#     mirror = MirrorCRAN()
#     snapshot = '2016-12-22'
#     url = mirror.get_mran_packages_url(snapshot)
#     r = requests.get(url)
#     assert r.status_code == 200, "Cannot connect to MRAN ({0})".format(url)

# def test_get_mran_package_url():
#     snapshot = '2016-12-22'
#     packs = ['lbfgs_1.2.1.tar.gz', 'pmg_0.9-43.tar.gz ']
#     mirror = MirrorCRAN()
#     url1 = mirror.get_mran_package_url(snapshot, packs[0])
#     url2 = mirror.get_mran_package_url(snapshot, packs[1])
#     r1 = requests.get(url1)
#     r2 = requests.get(url2)
#     assert r1.status_code == 200, "Cannot connect to MRAN ({0})".format(url1)
#     assert r2.status_code == 200, "Cannot connect to MRAN ({0})".format(url2)

# def test_download_cran_packs():
#     tempfolder = tempfile.mkdtemp()
#     mirror = MirrorCRAN()
#     mirror.download_cran_packs(
#         '2016-12-22',
#         ['lbfgs_1.2.1.tar.gz', 'pmg_0.9-43.tar.gz '],
#         tempfolder)
#     filepath1 = os.path.join(tempfile, 'lbfgs_1.2.1.tar.gz')
#     filepath2 = os.path.join(tempfile, 'pmg_0.9-43.tar.gz')
#     assert os.path.isfile(filepath1) == True, "Download failed!"
#     assert os.path.isfile(filepath2) == True, "Download failed!"

# def test_cran_packs_list():
    # l = get_cran_packs_list()
    # assert(len(l) > 0)

# def test_bioc_packs_list():
    # l = get_bioc_packs_list()
    # assert(len(l) > 0)

# def test_get_bioc_data_list():
    # l = get_bioc_data_list('annotation')
    # assert(len(l) > 0)
    # l = get_bioc_data_list('experiment')
    # assert(len(l) > 0)

# def test_download_cran():
    # packs = cran_packs_list()
    # download_cran_packs(packs, CRAN_DOWNLOAD_PATH)
    # assert(len(os.listdir(CRAN_DOWNLOAD_PATH)) > 100)

# def test_download_bioc():
    # packs = get_bioc_packs_list()
    # download_bioc_packs(packs, BIOC_DOWNLOAD_PATH)
    # assert(len(os.listdir(BIOC_DOWNLOAD_PATH)) > 100)

# def test_download_bioc_data():
    # packs = get_bioc_data_list('annotation')
    # download_bioc_data(packs, BIOC_DATA_PATH, 'annotation')
    # assert(len(os.listdir(BIOC_DATA_PATH)) > 10)
    # nb_files = len(os.listdir(BIOC_DATA_PATH))
    # packs = get_bioc_data_list('experiment')
    # download_bioc_data(packs, BIOC_DATA_PATH, 'experiment')
    # assert(len(os.listdir(BIOC_DATA_PATH)) > nb_files + 10)

# def test_deploy_cran():
    # deploy_cran_packs('R-3.2.2', CRAN_DOWNLOAD_PATH)

# def test_deploy_bioc():
    # deploy_bioc_packs('Bioc-3.2', BIOC_DATA_PATH)

