# RPackUtils

## Introduction

R package dependencies manager and mirroring tool for *Bioconductor* and
*CRAN* written in Python.  With **RPackUtils** you can:
*  Install R packages in a reproducible manner with the control of packages
       versions and dependencies
*  Clone existing R environments
*  Mirror past and current *CRAN* snapshots published on *MRAN*
*  Mirror past and current *Bioconductor* versions
*  Artifactory support

It is still under development. Currently refactoring to support different
source providers for R packages.

## Requirements

**RPackUtils** needs Python3.

## Installation

1. Get the source code.
```bash
$ git clone https://github.com/sgubianpm/RPackUtils.git
Cloning into 'RPackUtils'...
[...]
```
2. Enter the root folder and create a Virtualenv.
```bash
$ cd RPackUtils
$ python -m venv .
```

3. Activate the Virtualenv
```bash
$ . bin/activate
(RPackUtils) $
```

4. Optionnaly launch the unit tests

```bash
$ python setup.py build
[...]
(RPackUtils) $ cd tests
(RPackUtils) $ pytest
[...]
```

5. Install
```bash
(RPackUtils) $ python setup.py build install
[...]
```
This will install the binary commands in the *bin/* folder of your
Virtualenv.

You may want to specify an installation location with *--prefix*, please
check the documentation of the setup tool by typing :
```bash
(RPackUtils) $ python setup.py install --help
```

## Configuration

Customize the provided configuration file sample.

```bash
RPackUtils/tests/resources $ cp rpackutils.conf ~/
$ vim ~/rpackutils.conf
```

Provide the details about your Artifactory instance.
This is required in order to use the following commands:

* rpackc
* rpackd
* rpacki
* rpackm
* rpackq

The configuration file has to be systematically passed as an argument:
```bash
$ rpackc --conf="~/rpackutils.conf" ...
```

```
[global]
artifactory.url = https://artifactory.local/artifactory
artifactory.user = artifactoryUser
artifactory.pwd = "s3C437P4ssw@Rd"
artifactory.cert = /toto/Certificate_Chain.pem
```

## Usage

The entry points or commands are installed in *$PREFIX/bin*. This is either
inside your *bin/* folder of your Virtualenv or in the *bin/* folder of the
specified *--prefix*.

| Command   | Purpose                                                                                              |
|-----------|------------------------------------------------------------------------------------------------------|
| rpackbioc | Query the Bioconductor repository for available releases                                             |
| rpackmran | Query the MRAN repository for available snapshots                                                    |
| rpackq    | Search accross repositories for a package or a list of packages                                      |
| rpacki    | Install R packages with resolved dependencies                                                        |
| rpackc    | Install R packages based on an existing environments (clone)                                         |
| rpackd    | Download R packages and resolved dependencies                                                        |
| rpackm    | Download R packages from a specified repository (CRAN, Bioc) and upload them to Artifactory (mirror) |

The following sections provide use cases for each command.

### rpackbioc

Get all available **Bioconductor** releases from their website.

```bash
$ rpackbioc -h
usage: rpackbioc [-h]

Query the Bioconductor repository for available releases

optional arguments:
  -h, --help  show this help message and exit
```

Providing no argument will list all available realeases.

```bash
$ rpackbioc
Bioconductor 3.7 (devel)
Bioconductor 3.6 (release)
Bioconductor 3.5
Bioconductor 3.4
Bioconductor 3.3
Bioconductor 3.2
Bioconductor 3.1
Bioconductor 3.0
[...]
```

### rpackmran

```bash
$ rpackmran -h
usage: rpackmran [-h] [--Rversion RVERSION] [--procs PROCS]
                 [--dump DUMPFILEPATH] [--restore RESTOREFROMFILEPATH]

Search accross repositories for a package or a list of packages

optional arguments:
  -h, --help            show this help message and exit
  --Rversion RVERSION   The version of R, as "x.y.z" (ignored when --restore
                        is used)
  --procs PROCS         Number of parallel processes used to parse snapshots
                        properties, default=50
  --dump DUMPFILEPATH   a file where to dump the results
  --restore RESTOREFROMFILEPATH
                        a file where to read the results from
```

Providing no argument will fetch all available snapshots for all archived R versions.

```bash
$ rpackmran 
I will use 50 parallel processes to parse the R version from snapshots dates.
Fetching available MRAN snapshots from the Internet...
1225 snapshot dates found.
Snapshots processed/matching the specified R version (1225), skipped (0), errors (0).


Time elapsed: 19 seconds.
============================================================
R version 3.3.2, 125 snapshots
----------------------------------------
2016-11-01 2016-11-02 2016-11-03 2016-11-04 2016-11-05 2016-11-06 2016-11-07 2016-11-08 2016-11-09 2016-11-10 2016-11-11 2016-11-12 2016-11-13 2016-11-14 2016-11-15 2016-11-16 2016-11-17 2016-11-18 2016-11-19 2016-11-20 2016-11-21 2016-11-22 2016-11-23 2016-11-24 2016-11-25 2016-11-26 2016-11-27 2016-11-28 2016-11-29 2016-11-30 2016-12-01 2016-12-02 2016-12-03 2016-12-05 2016-12-06 2016-12-07 2016-12-08 2016-12-09 2016-12-10 2016-12-11 2016-12-12 2016-12-13 2016-12-14 2016-12-15 2016-12-16 2016-12-17 2016-12-18 2016-12-19 2016-12-20 2016-12-21 2016-12-22 2016-12-23 2016-12-24 2016-12-25 2016-12-26 2016-12-27 2016-12-28 2016-12-29 2016-12-30 2016-12-31 2017-01-01 2017-01-02 2017-01-03 2017-01-04 2017-01-05 2017-01-06 2017-01-07 2017-01-08 2017-01-09 2017-01-10 2017-01-11 2017-01-12 2017-01-13 2017-01-14 2017-01-15 2017-01-16 2017-01-17 2017-01-18 2017-01-19 2017-01-20 2017-01-21 2017-01-22 2017-01-23 2017-01-24 2017-01-25 2017-01-26 2017-01-27 2017-01-28 2017-01-29 2017-01-30 2017-01-31 2017-02-01 2017-02-02 2017-02-03 2017-02-04 2017-02-05 2017-02-06 2017-02-07 2017-02-08 2017-02-09 2017-02-10 2017-02-11 2017-02-12 2017-02-13 2017-02-14 2017-02-15 2017-02-16 2017-02-17 2017-02-18 2017-02-19 2017-02-20 2017-02-21 2017-02-22 2017-02-23 2017-02-24 2017-02-25 2017-02-26 2017-02-27 2017-02-28 2017-03-01 2017-03-02 2017-03-03 2017-03-04 2017-03-05 2017-03-06

R version 3.1.3, 38 snapshots
----------------------------------------
2015-03-10 2015-03-11 2015-03-12 2015-03-13 2015-03-14 2015-03-15 2015-03-16 2015-03-17 2015-03-18 2015-03-19 2015-03-20 2015-03-21 2015-03-22 2015-03-23 2015-03-24 2015-03-25 2015-03-26 2015-03-27 2015-03-28 2015-03-29 2015-03-30 2015-03-31 2015-04-01 2015-04-02 2015-04-03 2015-04-04 2015-04-05 2015-04-06 2015-04-07 2015-04-08 2015-04-09 2015-04-10 2015-04-11 2015-04-12 2015-04-13 2015-04-14 2015-04-15 2015-04-16

[...]
```

Usually, you are just interested with a particular R version.
For this, use the *--Rversion* argument.

```bash
$ rpackmran --Rversion="3.3.2"
I will use 50 parallel processes to parse the R version from snapshots dates.
Fetching available MRAN snapshots from the Internet...
1225 snapshot dates found.
Snapshots processed/matching the specified R version (125), skipped (1100), errors (0).


Time elapsed: 20 seconds.
============================================================
R version 3.3.2, 125 snapshots
----------------------------------------
2016-11-01 2016-11-02 2016-11-03 2016-11-04 2016-11-05 2016-11-06 2016-11-07 2016-11-08 2016-11-09 2016-11-10 2016-11-11 2016-11-12 2016-11-13 2016-11-14 2016-11-15 2016-11-16 2016-11-17 2016-11-18 2016-11-19 2016-11-20 2016-11-21 2016-11-22 2016-11-23 2016-11-24 2016-11-25 2016-11-26 2016-11-27 2016-11-28 2016-11-29 2016-11-30 2016-12-01 2016-12-02 2016-12-03 2016-12-05 2016-12-06 2016-12-07 2016-12-08 2016-12-09 2016-12-10 2016-12-11 2016-12-12 2016-12-13 2016-12-14 2016-12-15 2016-12-16 2016-12-17 2016-12-18 2016-12-19 2016-12-20 2016-12-21 2016-12-22 2016-12-23 2016-12-24 2016-12-25 2016-12-26 2016-12-27 2016-12-28 2016-12-29 2016-12-30 2016-12-31 2017-01-01 2017-01-02 2017-01-03 2017-01-04 2017-01-05 2017-01-06 2017-01-07 2017-01-08 2017-01-09 2017-01-10 2017-01-11 2017-01-12 2017-01-13 2017-01-14 2017-01-15 2017-01-16 2017-01-17 2017-01-18 2017-01-19 2017-01-20 2017-01-21 2017-01-22 2017-01-23 2017-01-24 2017-01-25 2017-01-26 2017-01-27 2017-01-28 2017-01-29 2017-01-30 2017-01-31 2017-02-01 2017-02-02 2017-02-03 2017-02-04 2017-02-05 2017-02-06 2017-02-07 2017-02-08 2017-02-09 2017-02-10 2017-02-11 2017-02-12 2017-02-13 2017-02-14 2017-02-15 2017-02-16 2017-02-17 2017-02-18 2017-02-19 2017-02-20 2017-02-21 2017-02-22 2017-02-23 2017-02-24 2017-02-25 2017-02-26 2017-02-27 2017-02-28 2017-03-01 2017-03-02 2017-03-03 2017-03-04 2017-03-05 2017-03-06

============================================================
```

You have the possibility to store any result as a JSON formatted file with
the *--dump* argument.  The opposite *--restore* argument will read the
file instead of querying the **MRAN** website.

### rpackq

```bash
$ rpackq -h
usage: rpackq [-h] [--repositories REPOS] --packages PACKAGES --config
              ARTIFACTORYCONFIG

Search accross repositories for a package or a list of packages

optional arguments:
  -h, --help            show this help message and exit
  --repositories REPOS  Comma separated list of repositories. Default are:
                        R-3.1.2, Bioc-3.0, R-local,R-Data-0.1
  --packages PACKAGES   Comma separated package names to install
  --config ARTIFACTORYCONFIG
                        File specifying the Artifactroy configuration. Sample
                        content: [global] artifactory.url =
                        "https://artifactoryhost/artifactory"artifactory.user
                        = "artiuser"artifactory.pwd = "***"artifactory.cert =
                        "Certificate_Chain.pem"
```

Search for the package *ggplot2* inside the Artifactory repository *R-3.1.2*.

```bash
$ rpackq --config="/gpfshpc/software/RPackUtils/rpackutils.conf" \
         --repositories="R-3.1.2" \
         --packages="ggplot2"
-------------------------------------
Package: ggplot2  Version: 1.0.0 in repository: R-3.1.2
Depends on: ['grid', 'reshape2', 'MASS', 'stats', 'plyr', 'R', 'proto', 'scales', 'methods', 'gtable', 'digest']

```

### rpacki

```bash
$ rpacki -h
usage: rpacki [-h] [--repositories REPOS] [--R-lib-path RLIBPATH]
              [--R-home RHOME] --packages PACKAGES --config ARTIFACTORYCONFIG

Install packages based on a list of packages

optional arguments:
  -h, --help            show this help message and exit
  --repositories REPOS  Comma separated list of repositories. Default are:
                        R-3.1.2, Bioc-3.0, R-local,R-Data-0.1
  --R-lib-path RLIBPATH
                        Path to the R library path where to install packages
  --R-home RHOME        Path to the R installation to use for installing
  --packages PACKAGES   Comma separated package names to install
  --config ARTIFACTORYCONFIG
                        File specifying the Artifactroy configuration. Sample
                        content: [global] artifactory.url =
                        "https://artifactoryhost/artifactory"artifactory.user
                        = "artiuser"artifactory.pwd = "***"artifactory.cert =
                        "Certificate_Chain.pem"
```

TODO

### rpackc

```bash
$ rpackc -h
usage: rpackc [-h] [--repositories REPOS] [--R-lib-path RLIBPATH]
              [--R-home RHOME] [--R-lib-refpath RLIBPATHREF] --config
              ARTIFACTORYCONFIG

Install R packages based on an existing environments (clone)

optional arguments:
  -h, --help            show this help message and exit
  --repositories REPOS  Comma separated list of repositories. Default are:
                        R-3.1.2, Bioc-3.0, R-local,R-Data-0.1
  --R-lib-path RLIBPATH
                        Path to the R library path where to install packages
  --R-home RHOME        Path to the installation to use
  --R-lib-refpath RLIBPATHREF
                        Path to the R library path used as reference
  --config ARTIFACTORYCONFIG
                        File specifying the Artifactroy configuration. Sample
                        content: [global] artifactory.url =
                        "https://artifactoryhost/artifactory"artifactory.user
                        = "artiuser"artifactory.pwd = "***"artifactory.cert =
                        "Certificate_Chain.pem"

```

TODO

### rpackd

```bash
$ rpackd -h
usage: rpackd [-h] [--repositories REPOS] --packages PACKAGES --config
              ARTIFACTORYCONFIG [--with-R-cmd] [--R-home RHOME] --R-lib-path
              RLIBPATH [--prefix PREFIX] [--dest DEST]

Download R packages and resolved dependencies

optional arguments:
  -h, --help            show this help message and exit
  --repositories REPOS  Comma separated list of repositories. Default are:
                        R-3.1.2, Bioc-3.0, R-local,R-Data-0.1
  --packages PACKAGES   Comma separated package names to install
  --config ARTIFACTORYCONFIG
                        File specifying the Artifactroy configuration. Sample
                        content: [global] artifactory.url =
                        "https://artifactoryhost/artifactory"artifactory.user
                        = "artiuser"artifactory.pwd = "***"artifactory.cert =
                        "Certificate_Chain.pem"
  --with-R-cmd          Print to the console the R command to install them
  --R-home RHOME        Path to the installation to use
  --R-lib-path RLIBPATH
                        Path to the R library path where to install packages
  --prefix PREFIX       Path to the location where R packages have been
                        downloaded
  --dest DEST           Path to the folder where packages are downloaded. If
                        notprovided, working folder will be used.

```

TODO

### rpackm

```bash
$ rpackm -h
usage: rpackm [-h] [--input-repository INPUTREPO] [--version VERSION]
              --output-repository OUTPUTREPO [--procs PROCS]
              [--config ARTIFACTORYCONFIG]

Download R packages from a specified repository (CRAN, Bioc) and upload them
to Artifactory (mirror)

optional arguments:
  -h, --help            show this help message and exit
  --input-repository INPUTREPO
                        The type of public R repository to mirror, possible
                        values: cran,bioc
  --version VERSION     The version of Bioconductor or the snapshot date of
                        CRAN
  --output-repository OUTPUTREPO
                        The Artifactory repository name
  --procs PROCS         Number of parallel downloads and uploads, default=10
  --config ARTIFACTORYCONFIG
                        File specifying the Artifactroy configuration. Sample
                        content: [global] artifactory.url = "https://rd-
                        artifactory.app.pmi/artifactory"artifactory.user = "s
                        -rd-atlassian"artifactory.pwd = "***"artifactory.cert
                        = "/gpfshpc/data/certs/GTS_PKI_Certificate_Chain.pem"

```

TODO


## Third parties

* Bioconductor: [Open source software for Bioinformatics](https://www.bioconductor.org/)
* CRAN: [The Comprehensive R Archive Network](https://cran.rstudio.com/)
* MRAN: [Microsoft R Application Network](https://mran.revolutionanalytics.com/)

## License

**RPackUtils** is distributed under the [GPL v2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.txt) license.
Copyright (c) 2018 PMPSA
