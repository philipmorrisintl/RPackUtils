# RPackUtils

## Introduction

R package dependencies manager and mittoring tool for *Bioconductor* and
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

4. Optionnaly lauch the unit tests

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

| Command   | Purpose                                                                                              |
|-----------|------------------------------------------------------------------------------------------------------|
| rpackbioc | Query the Bioconductor repository for available releases                                             |
| rpackmran | Query the MRAN repository for available snapshots                                                    |
| rpackq    | Search accross repositories for a package or a list of packages                                      |
| rpacki    | Install R packages with resolved dependencies                                                        |
| rpackc    | Install R packages based on an existing environments (clone)                                         |
| rpackd    | Download R packages and resolved dependencies                                                        |
| rpackm    | Download R packages from a specified repository (CRAN, Bioc) and upload them to Artifactory (mirror) |

### rpackbioc
TODO

### rpackmran
TODO

### rpackq
TODO

### rpacki
TODO

### rpackc
TODO

### rpackd
TODO

### rpackm
TODO


## Third parties

* Bioconductor: [Open source software for Bioinformatics](https://www.bioconductor.org/)
* CRAN: [The Comprehensive R Archive Network](https://cran.rstudio.com/)
* MRAN: [Microsoft R Application Network](https://mran.revolutionanalytics.com/)

## License

**RPackUtils** is distributed under the [GPL v2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.txt) license.
Copyright (c) 2018 PMPSA
