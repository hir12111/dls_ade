import os
import logging

import gitlab

from dls_ade.gitserver import GitServer
from dls_ade.dls_utilities import GIT_ROOT_DIR

GITLAB_API_URL = "https://gitlab.diamond.ac.uk"
GITLAB_CREATE_URL = "ssh://git@gitlab.diamond.ac.uk"
GITLAB_CLONE_URL = "ssh://git@gitlab.diamond.ac.uk"
GITLAB_RELEASE_URL = "https://gitlab.diamond.ac.uk"
GITLAB_API_VERSION = 4
GITLAB_TOKEN_ENV = "GITLAB_TOKEN"
GITLAB_DEFAULT_TOKEN = ""
# make sure the file mode is 440
GLOBAL_TOKEN_FILE_PATH = "/dls_sw/prod/common/python/gitlab/token"
# 400 for this one
USER_TOKEN_FILE_PATH = os.path.expanduser("~/.config/gitlab/token")

GITLAB_DEFAULT_PROJECT_ATTRIBUTES = {
    "visibility": "public",
    "issues_enabled": True,
    "wiki_enabled": False
}

GITLAB_DEFAULT_GROUP_ATTRIBUTES = {
    'visibility': 'public'
}

log = logging.getLogger(__name__)


class GitlabServer(GitServer):

    def __init__(self, token='', create_on_push=True):
        super(GitlabServer, self).__init__(GITLAB_CREATE_URL,
                                           GITLAB_CLONE_URL,
                                           GITLAB_RELEASE_URL)

        self.create_on_push = create_on_push

        if not token:
            # first try to get it from environment
            token = os.environ.get(GITLAB_TOKEN_ENV, '')

        if not token:
            # if argument and environment variable are not set, get it from a
            # predefined file
            token_location = ''
            if os.access(USER_TOKEN_FILE_PATH, os.R_OK):
                token_location = USER_TOKEN_FILE_PATH
            elif os.access(GLOBAL_TOKEN_FILE_PATH, os.R_OK):
                token_location = GLOBAL_TOKEN_FILE_PATH

            if token_location:
                with open(token_location, 'r') as fhandle:
                    token = fhandle.read().strip()
            else:
                # if every token source fails, use a default token
                token = GITLAB_DEFAULT_TOKEN

        log.debug("Initializing Gitlab server with token \"%s\"", token)
        self._gitlab_handle = gitlab.Gitlab(GITLAB_API_URL,
                                            private_token=token,
                                            api_version=GITLAB_API_VERSION)

    def is_server_repo(self, server_repo_path):
        """
        Checks if path exists on repository

        Args:
            server_repo_path(str): Path to module to check for

        Returns:
            bool: True if path does exist False if not

        """
        if server_repo_path.endswith('.git'):
            server_repo_path = server_repo_path[:-4]
        repo_list = self.get_server_repo_list()
        return server_repo_path in repo_list

    def get_server_repo_list(self):
        """
        Returns list of module repository paths from all projects

        Returns:
            List[str]: Repository paths on the server.
        """

        repos = []
        projects = self._gitlab_handle.projects.list()

        for project in projects:
            repo_path = os.path.join(project.namespace["full_path"],
                                     project.name)
            repos.append(repo_path)

        return repos

    def create_remote_repo(self, dest):
        """
        Create a git repository on the given gitlab server path.

        Args:
            dest(str): The server path for the git repository to be created.

        Raises:
            :class:`~dls_ade.exceptions.VCSGitError`: If a git repository
            already exists on the destination path.
        """

        if not self.create_on_push:
            path, repo_name = dest.rsplit('/', 1)

            group_id = self._gitlab_handle.groups.get(path).id

            project_data = dict(GITLAB_DEFAULT_PROJECT_ATTRIBUTES)
            project_data["name"] = repo_name
            self._gitlab_handle.projects.create(project_data,
                                                namespace_id=group_id)

    @staticmethod
    def dev_area_path(area="support"):
        """
        Return the full server path for the given area.

        Args:
            area(str): The area of the module.

        Returns:
            str: The full server path for the given area.

        """
        return os.path.join(GIT_ROOT_DIR, area)

    def dev_module_path(self, module, area="support"):
        """
        Return the full server path for the given module and area.

        Args:
            area(str): The area of the module.
            module(str): The module name.

        Returns:
            str: The full server path for the given module.

        """
        # Gitlab doesn't allow "create project on push" if the repository url
        # doesn't end with .git
        return os.path.join(self.dev_area_path(area), "{}.git".format(module))

    def get_clone_repo(self, server_repo_path, local_repo_path,
                       origin='gitlab'):
        """
        Get Repo clone given server and local repository paths

        Args:
            server_repo_path(str): server repository path
            local_repo_path(str): local repository path
        """
        return super(GitlabServer, self).get_clone_repo(server_repo_path,
                                                        local_repo_path,
                                                        'gitlab')

    @staticmethod
    def get_clone_path(path):
        """
        Return path; no changes are required for gitlab server

        Args:
            path(str): Full path to repo

        Returns:
            str: Path that can be use to clone repo
        """

        return path
