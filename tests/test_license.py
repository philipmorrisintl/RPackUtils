#######################################
# Copyright 2019 PMP SA.              #
# SPDX-License-Identifier: Apache-2.0 #
#######################################

import os
import pytest
from rpackutils.license import License


def test_check_blacklist():
    license = License('GNU Affero General Public License v3')
    assert license.blacklisted
    assert license.license_class == 'BLACKLISTED'
    license = License('AGPL v3')
    assert license.blacklisted
    assert license.license_class == 'BLACKLISTED'
    license = License('AGPL-3 | file LICENSE')
    assert license.blacklisted
    assert license.license_class == 'BLACKLISTED'
    license = License('Academic Free License v3.0')
    assert license.blacklisted
    assert license.license_class == 'BLACKLISTED'
    license = License('AFL v3.0')
    assert license.blacklisted
    assert license.license_class == 'BLACKLISTED'
    license = License('Apple Public Source License v2.0')
    assert license.blacklisted
    assert license.license_class == 'BLACKLISTED'
    license = License('Non-Profit Open Source License v3.0')
    assert license.blacklisted
    assert license.license_class == 'BLACKLISTED'
    license = License('RealNetworks Public Source License v1.0')
    assert license.blacklisted
    assert license.license_class == 'BLACKLISTED'
    license = License('Reciprocal Public License v1.5')
    assert license.blacklisted
    assert license.license_class == 'BLACKLISTED'


def test_check_restricted():
    license = License('Amazon Software License')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('Artistic License v1.0, v2.0')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('Common Development and Distribution License v1.0')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('CDDL v1.0')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('Common Public Attribution License')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('CPAL v1.0')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('Creative Commons Attribution-ShareAlike v4.0')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('CC BY-SA')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('Eclipse Public License v1.0')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('EPL')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('GNU General Public License v2.0')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('GPL')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('GNU Lesser General Public License v2.1')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('LGPL')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('Javascript Object Notation License')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('JSON')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('Microsoft Reciprocal License')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('Ms-RL')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('Mozilla Public License')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('MPL')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('Q Public License v1.0')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('IBM Public License Version - Secure Mailer v1.0')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('GPL-2 | GPL-3')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'
    license = License('GPL (>= 2)')
    assert license.restricted
    assert license.license_class == 'RESTRICTED'


def test_check_allowed():
    license = License('Internal')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('2-Clause BSD License')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('Apache v2.0')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('Boost Software License v1.0')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('BSL v1.0')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('Bzip2 License')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('Creative Commons Zero')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('CC0')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('Creative Commons Attribution-Only v4.0')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('CC BY')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('Henry Spencer RegEx License')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('ISC License')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('Microsoft Public License')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('Ms-PL')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('MIT License')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('PHP License v3.01')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('PostgreSQL License v1.0')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('Python License v3.6.2')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('zlib/libpng')
    assert license.allowed
    assert license.license_class == 'ALLOWED'
    license = License('Supervisor V3.3.3')
    assert license.allowed
    assert license.license_class == 'ALLOWED'


def test_check_unknown():
    license = License('file LICENSE')
    assert license.unknown
    assert license.license_class == 'UNKNOWN'
    license = License('MIT License | file LICENSE')
    assert license.unknown
    assert license.license_class == 'UNKNOWN'
