import os
from rpackutils.repos import RRepository


PACKNAME01 = 'CompQuadForm_1.4.1.tar.gz'
PACKNAME02 = 'FakePackTest.0.0.0.tar.gz'
REPOS_TEST = 'R-3.1.2'
REPOS_TEST2 = 'R-local'
PACKS = ['CompQuadForm', 'Rvmmin', 'GenSA', 'diptest', 'ade4']

def test_parse_pack_name():
    name, version = RRepository.parse_pack_name(PACKNAME01)
    assert(name == 'CompQuadForm')
    assert(version == '1.4.1')

def test_latest_version():
    rr = RRepository(REPOS_TEST2)
    packs = rr.packages
    for p in packs:
        print('{0} - Version: {1}'.format(p,
            rr.package_version(p)))

def test_pack_list():
    rr = RRepository(REPOS_TEST)
    assert(len(rr.packages) > 0)
    name = PACKNAME01.split('_')[0]
    assert(rr.package_version(name) == '1.4.1')

def test_description():
    rr = RRepository(REPOS_TEST)
    name = PACKNAME01.split('_')[0]
    packname, version, deps = rr.description(name)
    assert(packname == name)
    assert(version == rr.package_version(name))
    assert(len(deps) == 0)

def test_descriptions():
    for pack in PACKS:
        rr = RRepository(REPOS_TEST)
        packname, version, deps = rr.description(pack)
        print('Found package: {0} - version: {1}'.format(
            packname, version))
        assert(packname == pack)
        assert(version is not None)
