###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import pytest
from rpackutils.packinfo import PackInfo
from rpackutils.packinfo import PackStatus


def test_constructor_packagetarball():
    tarballpath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources/FooBar_0.99.1.tar.gz')
    pi = PackInfo(tarballpath)
    print(pi.as_dict)
    assert(pi.name == 'FooBar')
    assert(pi.version == '0.99.1')
    assert(pi.depends == ['R'])
    assert(pi.imports == ['methods', 'utils'])
    assert(pi.suggests == ['Rtoto', 'Rtiti'])
    assert(pi.license == 'GPL-2')


def test_constructor_invalid_packagetarball():
    tarballpath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources/nonexistingpackage_0.99.1.tar.gz')
    try:
        PackInfo(tarballpath)
    except Exception:
        pytest.fail(
            'Constructing a packInfo with '
            'an invalid tarball must raise an Exception!'
        )
    except Exception:
        pass


def test_constructor_packagefolder():
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources',
        'FooBar')
    pi = PackInfo(path)
    print(pi.as_dict)
    assert(pi.name == 'FooBar')
    assert(pi.version == '0.99.1')
    assert(pi.depends == ['R'])
    assert(pi.imports == ['methods', 'utils', 'toto'])
    assert(pi.suggests == ['Rtoto', 'Rtiti', 'Rtata'])
    assert(pi.license == 'GPL-2 and some blahblah')


def test_filename():
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources',
        'FooBar')
    pi = PackInfo(path)
    assert(pi.filename == 'FooBar_0.99.1.tar.gz')


def test_tarball():
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources',
        'FooBar')
    pi = PackInfo(path)
    assert(pi.tarball == 'FooBar_0.99.1.tar.gz')


def test_has_depends():
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources',
        'FooBar')
    pi = PackInfo(path)
    assert(pi.has_depends)


def test_has_imports():
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources',
        'FooBar')
    pi = PackInfo(path)
    assert(pi.has_imports)


def test_dependencies():
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources',
        'FooBar')
    pi = PackInfo(path)
    assert(len(pi.dependencies(withBasePackages=True)) == 4)
    assert('methods' in pi.dependencies(withBasePackages=True))
    assert('utils' in pi.dependencies(withBasePackages=True))
    assert('toto' in pi.dependencies(withBasePackages=True))
    assert('R' in pi.dependencies(withBasePackages=True))
    assert(len(pi.dependencies()) == 1)
    assert('toto' in pi.dependencies())


def test__do_parse_descriptionfile():
    tarballpath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources/FooBar_0.99.1.tar.gz')
    pi = PackInfo(tarballpath)
    try:
        pi._do_parse_descriptionfile('/some/invalid/DESCRIPTION')
        pytest.fail('Calling the method that way must raise an Exception!')
    except Exception:
        pass


def test__parse_package_name_version():
    # invalid extension
    try:
        PackInfo._parse_package_name_version('/some/path/name_0.1.0.zip')
        pytest.fail('An exception was expected!')
    except Exception:
        pass
    # invalid name
    try:
        PackInfo._parse_package_name_version('/some/path/name-0.1.0.tar.gz')
        pytest.fail('An exception was expected!')
    except Exception:
        pass
    # correct name
    name, version = PackInfo._parse_package_name_version(
        '/some/path/name_0.1.0.tar.gz')
    assert(name == 'name')
    assert(version == '0.1.0')
