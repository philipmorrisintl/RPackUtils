###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import pytest
from rpackutils.license import License

def test_check_blacklist():
    license = License('GNU Affero General Public License v3')
    assert license.blacklisted
    license = License('AGPL v3')
    assert license.blacklisted
    license = License('Academic Free License v3.0')
    assert license.blacklisted
    license = License('AFL v3.0')
    assert license.blacklisted
    license = License('Apple Public Source License v2.0')
    assert license.blacklisted
    license = License('Non-Profit Open Source License v3.0')
    assert license.blacklisted
    license = License('RealNetworks Public Source License v1.0')
    assert license.blacklisted
    license = License('Reciprocal Public License v1.5')
    assert license.blacklisted

def test_check_restricted():
    license = License('Amazon Software License')
    assert license.restricted
    license = License('Artistic License v1.0, v2.0')
    assert license.restricted
    license = License('Common Development and Distribution License v1.0')
    assert license.restricted
    license = License('CDDL v1.0')
    assert license.restricted
    license = License('Common Public Attribution License')
    assert license.restricted
    license = License('CPAL v1.0')
    assert license.restricted
    license = License('Creative Commons Attribution-ShareAlike v4.0')
    assert license.restricted
    license = License('CC BY-SA')
    assert license.restricted
    license = License('Eclipse Public License v1.0')
    assert license.restricted
    license = License('EPL')
    assert license.restricted
    license = License('GNU General Public License v2.0')
    assert license.restricted
    license = License('GPL')
    assert license.restricted
    license = License('GNU Lesser General Public License v2.1')
    assert license.restricted
    license = License('LGPL')
    assert license.restricted
    license = License('Javascript Object Notation License')
    assert license.restricted
    license = License('JSON')
    assert license.restricted
    license = License('Microsoft Reciprocal License')
    assert license.restricted
    license = License('Ms-RL')
    assert license.restricted
    license = License('Mozilla Public License')
    assert license.restricted
    license = License('MPL')
    assert license.restricted
    license = License('Q Public License v1.0')
    assert license.restricted
    license = License('IBM Public License Version - Secure Mailer v1.0')
    assert license.restricted

def test_check_allowed():
    license = License('2-Clause BSD License')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('Apache v2.0')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('Boost Software License v1.0')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('BSL v1.0')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('Bzip2 License')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('Creative Commons Zero')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('CC0')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('Creative Commons Attribution-Only v4.0')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('CC BY')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('Henry Spencer RegEx License')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('ISC License')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('Microsoft Public License')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('Ms-PL')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('MIT License')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('PHP License v3.01')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('PostgreSQL License v1.0')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('Python License v3.6.2')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('zlib/libpng')
    assert(license.blacklisted == False and license.restricted == False)
    license = License('Supervisor V3.3.3')
    assert(license.blacklisted == False and license.restricted == False)
