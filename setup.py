###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open('requirements.txt') as f:
    REQUIREMENTS = f.read().splitlines()
    
setup(name='RPackUtils',
      version='0.1.4',
      description='R Package Manager',
      classifiers=[
          "Programming Language :: Python",
      ],
      author='Sylvain Gubian, PMP SA',
      author_email='sylvain.gubian@pmi.com',
      url='',
      keywords='python R CRAN Bioconductor Artifactory',
      packages=find_packages(),
      include_package_data=False,
      zip_safe=False,
      install_requires=REQUIREMENTS,
      tests_require=REQUIREMENTS,
      test_suite="tests",
      entry_points = {
          'console_scripts': [
            'rpackc = rpackutils.deps:rpacks_clone',
            'rpacki = rpackutils.deps:rpacks_install',
            'rpackq = rpackutils.deps:rpacks_query',
            'rpackm = rpackutils.mirror:rpacks_mirror',
            'rpackmran = rpackutils.mirror:rpacks_mran',
            'rpackbioc = rpackutils.mirror:rpacks_bioc',
            'rpackd = rpackutils.deps:rpacks_download',
        ],
      }
)

