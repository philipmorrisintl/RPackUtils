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
      version='0.1.5',
      description='R Package Manager',
      classifiers=[
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Intended Audience :: Developers',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Information Technology',
          'Intended Audience :: Science/Research',
          'Intended Audience :: System Administrators',
          'Natural Language :: English',
          "Programming Language :: Python",
      ],
      author='Sylvain Gubian, Stephane Cano, PMP SA',
      author_email='sylvain.gubian@pmi.com',
      url='',
      keywords='Python R CRAN Bioconductor Artifactory',
      packages=find_packages(),
      include_package_data=False,
      zip_safe=False,
      install_requires=REQUIREMENTS,
      tests_require=REQUIREMENTS,
      test_suite="tests",
      entry_points = {
          'console_scripts': [
              'rpackc = rpackutils.cli:rpacks_clone',
              'rpacki = rpackutils.cli:rpacks_install',
              'rpackq = rpackutils.cli:rpacks_query',
              'rpackm = rpackutils.cli:rpacks_mirror',
              'rpackmran = rpackutils.cli:rpacks_mran',
              'rpackbioc = rpackutils.cli:rpacks_bioc',
              'rpackd = rpackutils.cli:rpacks_download',
              'rpackg = rpackutils.cli:rpacks_deps_graph',
              'rpackcc = rpackutils.cli:rpacks_config_check',
        ],
      }
)

