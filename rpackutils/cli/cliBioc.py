#######################################
# Copyright 2019 PMP SA.              #
# SPDX-License-Identifier: Apache-2.0 #
#######################################

import argparse
import logging
import time

from ..providers.bioconductor import Bioconductor

# logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def rpacks_bioc():
    argparse.ArgumentParser(
        description='Query the Bioconductor repository for available releases')
    starttime = time.time()
    bioc = Bioconductor()
    releases = bioc.ls_releases()
    for release in releases:
        logger.info(release)
    endtime = time.time()
    logger.info('Time elapsed: {0:.3f} seconds.'.format(endtime - starttime))
