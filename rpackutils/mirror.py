import os
import sys
import requests
import tempfile
from bs4 import BeautifulSoup
from artifactory import ArtifactoryHelper


CRAN_HTML = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), '..', 'CRAN-contrib-R-3.2.2.html')

BIOC_HTML = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), '..', 'BIOC-3.2.html')

BIOC_DATA_HTML = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), '..', 'BIOC-{0}-3.2.html')

CRAN_PACKAGES_URL = 'https://cran.r-project.org/src/contrib/'
BIOC_PACKAGES_URL = 'http://bioconductor.org/packages/release/bioc/src/contrib/'
BIOC_DATA_URL = 'http://bioconductor.org/packages/release/data/{0}/src/contrib'


def get_cran_packs_list():
    if not os.path.exists(CRAN_HTML):
        print('CRAN html file does not exist: {0}'.format(CRAN_HTML))
    with open(CRAN_HTML, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')
    packs = []
    tables = soup.findChildren('table')
    table = tables[0]
    rows = table.findChildren('tr')
    for row in rows:
        cells = row.findChildren('td')
        for cell in cells:
            if cell.string is None:
                continue
            if cell.string.endswith('.tar.gz'):
                packs.append(cell.string)
    return packs

def get_bioc_packs_list():
    if not os.path.exists(BIOC_HTML):
        print('BIOC html file does not exist: {0}'.format(BIOC_HTML))
    with open(BIOC_HTML, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')
    packs = []
    table = soup.find('table', class_='mainrep')
    rows = table.findChildren('tr')
    for row in rows:
        cls = row.attrs.get("class")
        if cls is None:
            continue
        cname = " ".join(cls)
        if cname not in ['odd ok', 'even ok', 'odd warnings',
                         'even warnings', 'even timeout', 'odd timeout']:
            continue
        cells = row.findChildren('td')
        cell = cells[0]
        b = cell.find('b')
        if b:
            a = cell.find('a')
            if a is not None:
                link = a.get('href')
                if link is not None:
                    pack = b.get_text().replace(u'\xa0', '_')
                    packs.append(pack)
    return packs

def get_bioc_data_list(name):
    """
    name: String value, can be annotation or experiment
    Returns a python list of available annotations or experiment
    Usually found at :
        https://www.bioconductor.org/packages/release/data/experiment/
        https://www.bioconductor.org/packages/release/data/annotation/
    """
    if name not in ['annotation', 'experiment']:
        print('Bioconductor data name has to be annotation or experiment')
        sys.exit(-1)
    list_file = BIOC_DATA_HTML.format(name)
    if not os.path.exists(list_file):
        print('BIOC {0} html file does not exist: {1}'.format(
            name, list_file))
    pages_list = []
    packs = []
    print('Retrieving DATA list of pages...')
    with open(list_file, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')
    div = soup.find('div', class_="do_not_rebase")
    tables = div.find_all('table')
    table = tables[0]
    rows = table.findChildren('tr')
    for row in rows:
        clazz = row.attrs.get("class")
        if clazz is None:
            continue
        if clazz[0] not in ['row_odd', 'row_even']:
            continue
        cells = row.findChildren('td')
        cell = cells[0]
        a = cell.find('a')
        if a is not None:
            link = a.get('href')
            pages_list.append(link)
    for page in pages_list:
        print('Parsing page: {0}...'.format(page))
        fd, path = tempfile.mkstemp()
        r = requests.get(page, stream=True)
        with open(fd, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
        sp = BeautifulSoup(open(path, 'rb'), 'html.parser')
        tables = sp.find_all('table')
        for table in tables:
            rows = table.findChildren('tr')
            for row in rows:
                cells = row.findChildren('td')
                for cell in cells:
                    clazz = cell.attrs.get("class")
                    if clazz is not None and clazz[0] == 'rpack':
                        a = cell.find('a')
                        if a is not None:
                            link = a.get('href')
                            if link is not None:
                                pack = a.get_text().strip()
                                packs.append(pack)
        os.remove(path)
    packs = [x for x in packs if x]
    return packs

def download_cran_packs(packs, tofolder):
    for pack in packs:
        print('Downloading CRAN R package: {0}'.format(pack))
        url = '{0}/{1}'.format(CRAN_PACKAGES_URL, pack)
        r = requests.get(url, stream=True)
        with open(os.path.join(tofolder, pack), 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

def download_bioc_packs(packs, tofolder):
    for pack in packs:
        print('Downloading BIOC R package: {0}'.format(pack))
        url = '{0}/{1}.tar.gz'.format(BIOC_PACKAGES_URL, pack)
        r = requests.get(url, stream=True)
        with open(os.path.join(tofolder, '{0}.tar.gz'.format(
            pack)), 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

def download_bioc_data(packs, tofolder, name):
    for pack in packs:
        print('Downloading BIOC DATA: {0}'.format(pack))
        url = '{0}/{1}'.format(BIOC_DATA_URL.format(name), pack)
        r = requests.get(url, stream=True)
        with open(os.path.join(tofolder, '{0}'.format(
            pack)), 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

def deploy_cran_packs(repos, folder):
    ArtifactoryHelper.deploy(repos, folder)

def deploy_bioc_packs(repos, folder):
    ArtifactoryHelper.deploy(repos, folder)

