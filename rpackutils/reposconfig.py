###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import logging

from .config import Config
from configparser import NoSectionError, NoOptionError
from rpackutils.providers.artifactory import Artifactory
from rpackutils.providers.renvironment import REnvironment
from rpackutils.providers.localrepository import LocalRepository

logger = logging.getLogger(__name__)
REPOSITORIES = "repositories"


class ReposConfig:

    def __init__(self, config):
        self._artifactory_instances = {}
        self._renvironment_instances = {}
        self._local_instances = {}
        if not isinstance(config, Config):
            raise TypeError
        self._config = config
        self._build_repositories(
            "artifactory_repos",
            "_build_artifactory_repos")
        self._build_repositories(
            "renvironment_repos",
            "_build_renvironment_repos")
        self._build_repositories(
            "local_repos",
            "_build_local_repos")

    @property
    def repository_instances(self):
        repositories = []
        # fetch artifactory instances
        for artifactory_instance_name in self.artifactory_instances:
            arti = self.artifactory_instance(artifactory_instance_name)
            repositories.append(arti)
        # fetch renvironment instances
        for renvironment_instance_name in self.renvironment_instances:
            renv = self.renvironment_instance(renvironment_instance_name)
            repositories.append(renv)
        # fetch local instances
        for local_instance_name in self.local_instances:
            local = self.local_instance(local_instance_name)
            repositories.append(local)
        return repositories

    def repository_instances_by_name(self, names):
        """
        :param names: list of repository names to get.
        """
        repositories = []
        for name in names:
            repositories.append(self.instance(name))
        # remove None values if any
        repositories = [r for r in repositories if r]
        return repositories

    def instance(self, name):
        """
        Get a repository by its name.
        None is returned if it cannot be found.
        """
        if name in self.artifactory_instances:
            return self.artifactory_instance(name)
        elif name in self.renvironment_instances:
            return self.renvironment_instance(name)
        elif name in self.local_instances:
            return self.local_instance(name)
        else:
            logger.error('Repository named \"{0}\" not found!'
                         .format(name))
            return None

    @property
    def artifactory_instances(self):
        return self._artifactory_instances.keys()

    def artifactory_instance(self, name):
        return self._artifactory_instances[name]

    @property
    def renvironment_instances(self):
        return self._renvironment_instances.keys()

    def renvironment_instance(self, name):
        return self._renvironment_instances[name]

    @property
    def local_instances(self):
        return self._local_instances.keys()

    def local_instance(self, name):
        return self._local_instances[name]

    def _build_repositories(self, repositoriesKey, buildFunction):
        try:
            repos_config = self._config.get(REPOSITORIES, repositoriesKey)
            if not repos_config == "":
                names = [x.strip() for x in repos_config.split(',')]
                getattr(self, buildFunction)(names)
        except NoOptionError:
            pass
        except NoSectionError:
            logger.error(
                'The section \"{}\" is missing '
                'in the configuration file!'.format(REPOSITORIES))
            pass

    def _build_artifactory_repos(self, names):
        for name in names:
            logger.info('Building Artifactory instance \"{0}\"'
                        .format(name))
            auth = (
                self._config.get(name, "user"),
                self._config.get(name, "password")
            )
            repos = [x.strip() for x in self._config.get(
                name, "repos").split(',')]
            provider = Artifactory(
                self._config.get(name, "baseurl"),
                repos,
                auth,
                self._config.get(name, "verify")
            )
            provider.name = name
            self._artifactory_instances[name] = provider

    def _build_renvironment_repos(self, names):
        for name in names:
            logger.info('Building R environment instance \"{0}\"'
                        .format(name))
            licensecheck = False
            try:
                licensecheck = self._config.getboolean(name, "licensecheck")
            except Exception:
                licensecheck = False
            provider = REnvironment(
                self._config.get(name, "rhome"),
                self._config.get(name, "librarypath"),
                licensecheck
            )
            provider.name = name
            if(provider._licensecheck):
                logger.info('License checking is ON')
            else:
                logger.info('License checking is OFF')
            self._renvironment_instances[name] = provider

    def _build_local_repos(self, names):
        for name in names:
            logger.info('Building Local repository instance \"{0}\"'
                        .format(name))
            repos = [x.strip() for x in self._config.get(
                name, "repos").split(',')]
            provider = LocalRepository(
                self._config.get(name, "baseurl"),
                repos
            )
            provider.name = name
            self._local_instances[name] = provider
