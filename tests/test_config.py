#######################################
# Copyright 2019 PMP SA.              #
# SPDX-License-Identifier: Apache-2.0 #
#######################################

import os
import pytest
from rpackutils.config import Config


def test_custom_config():
    configfilepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources/rpackutils.conf')
    config = Config(configfilepath)
    assert(
        config.get("repositories", "artifactory_repos")
        == "artifactory, artifactorydev"
    )
    assert(
        config.get("repositories", "renvironment_repos")
        == "R-3.1.2, R-3.2.5, R-3.2.2"
    )
    assert(
        config.get("repositories", "local_repos")
        == "local")
    # artifactory
    assert(
        config.get("artifactory", "baseurl")
        == "https://YOUR_ARTIFACTORY_HOSTNAME/artifactory")
    assert(
        config.get("artifactory", "user")
        == "YOUR_ARTIFACTORY_USER")
    assert(
        config.get("artifactory", "password")
        == "YOUR_ARTIFACTORY_PASSWORD")
    assert(
        config.get("artifactory", "verify")
        == "/toto/Certificate_Chain.pem")
    assert(
        config.get("artifactory", "repos")
        == "R-3.1.2, Bioc-3.0, R-local, R-Data-0.1")
    assert(
        not config.getboolean("R-3.1.2", "licensecheck")
    )
    assert(
        not config.getboolean("R-3.2.2", "licensecheck")
    )
    assert(
        config.getboolean("R-3.2.5", "licensecheck")
    )
