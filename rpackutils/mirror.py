###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import errno
import requests
import sys
import argparse
import subprocess
import tempfile
import shutil
from .mirror_cran import MirrorCRAN
from .mirror_bioc import MirrorBioc
from .json_serializer import JSONSerializer

ARTIFACTORY_CONFIG_HELP = "File specifying the Artifactroy configuration.\n" \
    "Sample content:\n" \
    "\n" \
    "[global]\n" \
    "artifactory.url = \"https://artifactoryhost/artifactory\"" \
    "artifactory.user = \"artiuser\"" \
    "artifactory.pwd = \"***\"" \
    "artifactory.cert = \"Certificate_Chain.pem\""

def rpacks_bioc():
    parser = argparse.ArgumentParser(
        description='Query the Bioconductor repository for available releases')
    args = parser.parse_args()
    mirror = MirrorBioc()
    mirror.get_bioc_releases_list()
    
def rpacks_mran():
    parser = argparse.ArgumentParser(
        description='Search accross repositories for a package or a list of packages')
    parser.add_argument(
            '--Rversion',
            dest='rversion',
            action='store',
            default=None,
            help='The version of R, as \"x.y.z\" (ignored when --restore is used)',
            ) and None
    parser.add_argument(
            '--procs',
            dest='procs',
            action='store',
            default='50',
            type=int,
            help='Number of parallel processes used to parse snapshots properties, default=50',
            ) and None
    parser.add_argument(
            '--dump',
            dest='dumpfilepath',
            action='store',
            default=None,
            help='a file where to dump the results',
            ) and None
    parser.add_argument(
            '--restore',
            dest='restorefromfilepath',
            action='store',
            default=None,
            help='a file where to read the results from',
            ) and None
    args = parser.parse_args()
    if args.dumpfilepath is not None and args.restorefromfilepath is not None:
        print("Please choose either dump or restore, they are exclusive!")
        exit(-1)
    snapshots = None
    if args.restorefromfilepath is None:
        print("I will use {0} parallel processes to parse the R version from snapshots dates." \
              .format(args.procs))
        print("Fetching available MRAN snapshots from the Internet...")
        mirror = MirrorCRAN()
        snapshots = mirror.get_mran_snapshots_list(args.procs, args.rversion)
    else:
        if args.rversion is not None:
            print('Ignoring the --Rversion parameter since --restore is used.')
        if args.procs is not None:
            print('Ignoring the --procs parameter since --restore is used.')
        print("Reading available MRAN snapshots from {0}...".format(args.restorefromfilepath))
        snapshots = JSONSerializer.deserializefromfile(args.restorefromfilepath)
    print("============================================================")
    for version in snapshots.keys():
        print("R version {0}, {1} snapshots\n"\
                  "----------------------------------------" \
                  "\n{2}\n" \
                  .format(version,
                          len(snapshots[version]),
                          " ".join(snapshots[version])))
    print("============================================================")
    if args.dumpfilepath is not None:
        JSONSerializer.serialize2file(snapshots, args.dumpfilepath)
        print("Results dumped to {0}.".format(args.dumpfilepath))

def rpacks_mirror():
    parser = argparse.ArgumentParser(
        description='Download R packages from a specified repository ' \
        '(CRAN, Bioc) and upload them to Artifactory (mirror)')
    parser.add_argument(
            '--input-repository',
            dest='inputrepo',
            action='store',
            default='',
            help='The type of public R repository to mirror, ' \
                'possible values: cran,bioc',
            ) and None
    parser.add_argument(
            '--version',
            dest='version',
            action='store',
            default='',
            help='The version of Bioconductor or the snapshot date of CRAN',
            ) and None
    parser.add_argument(
            '--output-repository',
            dest='outputrepo',
            action='store',
            default=None,
            required=True,
            help='The Artifactory repository name',
            ) and None
    parser.add_argument(
            '--procs',
            dest='procs',
            action='store',
            default='10',
            type=int,
            help='Number of parallel downloads and uploads, default=10',
            ) and None
    parser.add_argument(
            '--config',
            dest='artifactoryConfig',
            action='store',
            default=None,
            required=False,
            help=ARTIFACTORY_CONFIG_HELP,
            ) and None
    args = parser.parse_args()
    if args.inputrepo not in ['cran','bioc']:
        print('The specified Input Repository is invalid')
        sys.exit(-1)
    if not args.version:
        print('Version or snapshot date not provided')
        sys.exit(-1)
    if not args.outputrepo:
        print('Output Repository not provided')
        sys.exit(-1)
    artifactoryConfig = None
    if args.artifactoryConfig is not None:
        artifactoryConfig = args.artifactoryConfig
    procs = args.procs
    outputrepo = args.outputrepo
    # create a temp folder
    tempfolder = tempfile.mkdtemp()
    print("Using the temporary folder " + tempfolder)
    print('I will use {0} parallel processes for ' \
              'parsing, downloads and uploads.' \
              .format(procs))
    if args.inputrepo == "cran":
        # CRAN
        mirror = MirrorCRAN()
        packs = mirror.get_cran_packs_list(args.version)
        mirror.download_cran_packs(args.version,
                                   packs,
                                   tempfolder,
                                   procs)
        mirror.deploy_cran_packs(outputrepo,
                                 tempfolder,
                                 procs,
                                 artifactoryConfig)
    else:
        # Bioconductor
        mirror = MirrorBioc()
        # get the list of data and packages
        software_packs = mirror.get_bioc_packs_list(
            args.version, 'software', procs)
        experimentData_packs = mirror.get_bioc_packs_list(
            args.version, 'experimentData', procs)
        annotationData_packs = mirror.get_bioc_packs_list(
            args.version, 'annotationData', procs)
        # Download
        mirror.download_bioc_packs(
            software_packs, args.version, 'software', tempfolder,
            procs)
        mirror.download_bioc_packs(
            experimentData_packs, args.version, 'experimentData', tempfolder,
            procs)
        mirror.download_bioc_packs(
            annotationData_packs, args.version, 'annotationData', tempfolder,
            procs)
        # Deploy
        mirror.deploy_bioc_packs(outputrepo,
                                 tempfolder,
                                 procs,
                                 artifactoryConfig)
    print("Cleaning up the temporary folder " + tempfolder)
    shutil.rmtree(tempfolder)
