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
      version='0.1.7',
      description='R Package Manager',
      long_description='''R Package Dependencies Manager and Bioconductor & CRAN Mirroring Tool''',
      classifiers=[
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Intended Audience :: Developers',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Information Technology',
          'Intended Audience :: Science/Research',
          'Intended Audience :: System Administrators',
          'Natural Language :: English',
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
      ],
      author='Sylvain Gubian, Stephane Cano, PMP SA',
      author_email='DevelopmentSupport.HPC@pmi.com',
      url='https://github.com/pmpsa-hpc/RPackUtils.git',
      keywords= ['R', 'CRAN', 'MRAN', 'Bioconductor', 'Artifactory'
                 'dependency', 'manager', 'graph', 'network'],
      packages=find_packages(),
      include_package_data=False,
      zip_safe=False,
      install_requires=REQUIREMENTS,
      tests_require=REQUIREMENTS,
      test_suite="tests",
      entry_points = {
          'console_scripts': [
              'rpackc = rpackutils.cli.cliClone:rpacks_clone',
              'rpacki = rpackutils.cli.cliInstall:rpacks_install',
              'rpackq = rpackutils.cli.cliQuery:rpacks_query',
              'rpackm = rpackutils.cli.cliMirror:rpacks_mirror',
              'rpackmran = rpackutils.cli.cliMran:rpacks_mran',
              'rpackbioc = rpackutils.cli.cliBioc:rpacks_bioc',
              'rpackd = rpackutils.cli.cliDownload:rpacks_download',
              'rpackg = rpackutils.cli.cliDepsGraph:rpacks_deps_graph',
              'rpackcc = rpackutils.cli.cliConfigCheck:rpacks_config_check',
              'rpackscan = rpackutils.cli.cliScan:rpacks_scan',
        ],
      }
)
