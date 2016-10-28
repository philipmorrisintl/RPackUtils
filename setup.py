import os

from setuptools import setup, find_packages
from pip.req import parse_requirements
from pip.download import PipSession

here = os.path.abspath(os.path.dirname(__file__))

#install_reqs = parse_requirements("requirements.txt", session=PipSession())
#requires = [str(ir.req) for ir in install_reqs]

requires = [
    'pytest',
    'requests'
]

setup(name='RPackUtils',
        version='0.0.6',
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
        install_requires=requires,
        tests_require=requires,
        test_suite="tests",
        entry_points = {
            'console_scripts': [
                'rpackc = rpackutils.deps:rpacks_clone',
                'rpacki = rpackutils.deps:rpacks_install',
                'rpackq = rpackutils.deps:rpacks_query',
            ],
        }
      )

