import sys
import os
import requests
import shutil
ppath = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), '..', 'rpackutils')
sys.path.append(ppath)

pack_example_name = 'GenSA'
pack_example_url = 'http://cran.r-project.org/src/contrib/GenSA_1.1.6.tar.gz'
pack_example_fp = os.path.join(os.path.dirname(__file__), 'PackTest.tar.gz')

def download_package_example():
    r = requests.get(pack_example_url)
    with open(pack_example_fp, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

def remove_package_example(uninstall=True):
    if os.path.exists(pack_example_fp):
        os.remove(pack_example_fp)
    if uninstall:
        p = os.path.join(os.environ['R_LIBS'], 'GenSA')
        if os.path.exists(p):
            shutil.rmtree(p)

