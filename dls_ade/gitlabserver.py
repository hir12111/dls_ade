import os
import logging

import gitlab

from dls_ade.gitserver import GitServer
from dls_ade.dls_utilities import GIT_ROOT_DIR


def test_given_invalid_source_then_empty_list_of_modules(self):
    self.server_mock.get_server_repo_list.return_value = \
        ["test/not_source/module"]

    source = "test/source"

    module_list = dls_list_modules.get_module_list(source)
    self.assertIsNotNone(module_list)
    self.assertListEqual(module_list, [])


GITLAB_API_URL = "https://gitlab.diamond.ac.uk"
GITLAB_CREATE_URL = "ssh://git@gitlab.diamond.ac.uk"
GITLAB_CLONE_URL = "ssh://git@gitlab.diamond.ac.uk"
GITLAB_RELEASE_URL = "https://gitlab.diamond.ac.uk"
TOKEN_HELP_LINK = "https://confluence.diamond.ac.uk/display/CNTRLS/" \
                  "How+to+generate+a+GitLab+API+token+for+use+with+dls_ade"
GITLAB_API_VERSION = 4
GITLAB_PER_PAGE = 100
HTTP_NOT_FOUND = 404
# make sure the file mode is 440
USER_TOKEN_FILE_PATH = os.path.expanduser("~/.config/gitlab/token")

GITLAB_DEFAULT_PROJECT_ATTRIBUTES = {
    "visibility": "public",
    "issues_enabled": False,
    "wiki_enabled": False,
    "snippets_enabled": False,
    # This setting enables Gitlab CI. We may want to turn this on but
    # can do so per-repository when setting up CI.
    "jobs_enabled": False
}

GITLAB_DEFAULT_GROUP_ATTRIBUTES = {
    'visibility': 'public'
}

log = logging.getLogger(__name__)


class GitlabServer(GitServer):

    def __init__(self):
        super(GitlabServer, self).__init__(GITLAB_CREATE_URL,
                                           GITLAB_CLONE_URL,
                                           GITLAB_RELEASE_URL)

        self._anon_gitlab_handle = gitlab.Gitlab(
            GITLAB_API_URL,
            private_token="",
            api_version=GITLAB_API_VERSION,
            per_page=GITLAB_PER_PAGE
        )
        self._private_gitlab_handle = None

    def _setup_private_gitlab_handle(self):
        if self._private_gitlab_handle:
            return

        if not os.access(USER_TOKEN_FILE_PATH, os.F_OK):
            raise ValueError("Gitlab token file {} not found. "
                             " See {} for help.".format(USER_TOKEN_FILE_PATH,
                                                        TOKEN_HELP_LINK))

        if (os.stat(USER_TOKEN_FILE_PATH).st_mode & 0o777) != 0o400:
            raise ValueError("Incorrect Gitlab token file permissions. "
                             "It should be 400. "
                             " See {} for help.".format(TOKEN_HELP_LINK))

        with open(USER_TOKEN_FILE_PATH, 'r') as fhandle:
            token = fhandle.read().strip()

        self._private_gitlab_handle = \
            gitlab.Gitlab(GITLAB_API_URL, private_token=token,
                          api_version=GITLAB_API_VERSION)

    def is_server_repo(self, server_repo_path):
        """
        Checks if path exists on repository

        Args:
            server_repo_path(str): Path to module to check for

        Returns:
            bool: True if path does exist False if not

        """
        if server_repo_path.endswith(".git"):
            server_repo_path = server_repo_path[:-4]

        return self._is_project(server_repo_path)

    def _is_project(self, path):
        try:
            project = self._anon_gitlab_handle.projects.get(path)
            name = os.path.split(path)[-1]
            return name == project.name
        except gitlab.exceptions.GitlabGetError as e:
            if e.response_code == HTTP_NOT_FOUND:
                return False
            else:
                raise
        return True

    def get_server_repo_list(self, path=GIT_ROOT_DIR):
        """
        Returns list of module repository paths from all projects below
        'path' in the Gitlab server tree.

        Includes .git suffix.

        Arguments:
            path: Gitlab server path

        Returns:
            List[str]: Repository paths on the server.
        """
        projects = (
            self._anon_gitlab_handle.groups.get(path).projects.list(
                all=True, include_subgroups=True
            )
        )

        repos = []
        for project in projects:
            repo_path = os.path.join(
                project.namespace["full_path"], project.name
            )
            repo_path = "{}.git".format(repo_path)
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

        self._setup_private_gitlab_handle()

        path, repo_name = dest.rsplit('/', 1)

        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        self._create_groups_in_path(path)
        group_id = self._private_gitlab_handle.groups.get(path).id

        project_data = dict(GITLAB_DEFAULT_PROJECT_ATTRIBUTES)
        project_data["name"] = repo_name
        self._private_gitlab_handle.projects.create(project_data,
                                                    namespace_id=group_id)

    def _is_group(self, path):
        try:
            self._anon_gitlab_handle.groups.get(path)
        except gitlab.exceptions.GitlabGetError as e:
            if e.response_code == HTTP_NOT_FOUND:
                return False
            else:
                raise
        return True

    def _create_groups_in_path(self, path):
        if self._is_group(path):
            return
        parts = path.split('/')
        for i in range(1, len(parts)):
            semi_path = "/".join(parts[:i])
            if not self._is_group(semi_path):
                self._create_group(semi_path)
        self._create_group(path)

    def _create_group(self, path):
        if "/" not in path:
            parent_id = None
        else:
            parent_id = self._private_gitlab_handle.groups.get(
                os.path.dirname(path)).id
        group_name = os.path.basename(path)
        group_data = dict(GITLAB_DEFAULT_GROUP_ATTRIBUTES)
        group_data.update({
            'name': group_name,
            'path': group_name,
            'parent_id': parent_id
        })
        self._private_gitlab_handle.groups.create(group_data)

    @staticmethod
    def dev_area_path(area="support"):
        """
        Return the full server path for the given area e.g. controls/support

        Args:
            area(str): The area of the module.

        Returns:
            str: The full server path for the given area.

        """
        return os.path.join(GIT_ROOT_DIR, area)

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

    def dev_module_path(self, module, area="support"):
        """
        Return the full server path for the given module and area.

         Args:
             area(str): The area of the module.
             module(str): The module name.

         Returns:
             str: The full server path for the given module.

         """
        # Use .git ending to make it work when redirection is not supported
        return os.path.join(self.dev_area_path(area), "{}.git".format(module))
