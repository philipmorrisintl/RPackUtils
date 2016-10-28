import os
import pytest
from rpackutils.mirror import download_cran_packs
from rpackutils.mirror import download_bioc_packs
from rpackutils.mirror import download_bioc_data
from rpackutils.mirror import get_cran_packs_list
from rpackutils.mirror import get_bioc_packs_list
from rpackutils.mirror import get_bioc_data_list
from rpackutils.mirror import deploy_cran_packs
from rpackutils.mirror import deploy_bioc_packs

CRAN_DOWNLOAD_PATH='/tmp/R_PACKAGES_3.2.2'
BIOC_DOWNLOAD_PATH='/tmp/BIOC_PACKAGES_3.2'
BIOC_DATA_PATH='/tmp/BIOC_DATA_3.2'

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

