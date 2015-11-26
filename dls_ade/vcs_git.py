from vcs import BaseVCS
import tempfile
import subprocess
import os

from pkg_resources import require
require('GitPython')
import git


GIT_ROOT = "dascgitolite@dasc-git.diamond.ac.uk"
GIT_SSH_ROOT = "ssh://dascgitolite@dasc-git.diamond.ac.uk/"


def is_repo_path(server_repo_path):

    list_cmd = "ssh " + GIT_ROOT + " expand controls"
    list_cmd_output = subprocess.check_output(list_cmd.split())

    return server_repo_path in list_cmd_output


def get_repository_list():

    list_cmd = "ssh " + GIT_ROOT + " expand controls"
    list_cmd_output = subprocess.check_output(list_cmd.split())
    split_list = list_cmd_output.split()

    return split_list


def clone(source, module):

    if not is_repo_path(source):
        raise Exception("Repository does not contain " + source)
    elif os.path.isdir(module):
        raise Exception(module + " already exists in current directory")

    if source[-1] == '/':
        source = source[:-1]

    git.Repo.clone_from(os.path.join(GIT_SSH_ROOT, source),
                        os.path.join("./", module))


def clone_multi(source, module):

    if not is_repo_path(source):
        raise Exception("Repository does not contain " + source)
    elif os.path.isdir(module):
        raise Exception(module + " already exists in current directory")

    if source[-1] == '/':
        source = source[:-1]

    split_list = get_repository_list()
    for path in split_list:
        if source in path:
            source_length = len(source) + 1
            target_path = path[source_length:]
            if target_path not in os.listdir("./"):
                print("Cloning: " + path + "...")
                git.Repo.clone_from(os.path.join(GIT_SSH_ROOT, path),
                                    os.path.join("./", target_path))
            else:
                print(target_path + " already exists in current directory")


class Git(BaseVCS):

    def __init__(self, module, options):

        self._module = module
        self.area = options.area

        server_repo_path = 'controls/' + self.area + '/' + self._module

        if not is_repo_path(server_repo_path):
            raise Exception('repo not found on gitolite server')

        repo_dir = tempfile.mkdtemp(suffix="_" + self._module.replace("/", "_"))
        self._remote_repo = os.path.join(GIT_SSH_ROOT, server_repo_path)

        self.client = git.Repo.clone_from(self._remote_repo, repo_dir)
        self._version = None

    @property
    def vcs_type(self):
        return 'git'

    @property
    def module(self):
        return self._module

    @property
    def source_repo(self):
        return self._remote_repo

    @property
    def version(self):
        if not self._version:
            raise Exception('version not set')
        return self._version

    def cat(self, filename):
        '''
        Fetch contents of file in repository, if version not set then uses
        master.
        '''
        tag = 'master'
        if self._version:
            if self.check_version_exists(self._version):
                tag = self._version
        return self.client.git.cat_file('-p', tag + ':' + filename)

    def list_releases(self):
        '''Return list of release tags of module.'''
        if not hasattr(self, 'releases'):
            self.releases = []
            for tag in self.client.tags:
                self.releases.append(tag.name)
        return self.releases

    def set_log_message(self, message):
        '''Git support will not do a commit, so log message not needed.'''
        return None

    def check_version_exists(self, version):
        return version in self.list_releases()

    def set_branch(self, branch):
        raise NotImplementedError('branch handling for git not implemented')

    def set_version(self, version):
        if not self.check_version_exists(version):
            raise Exception('version does not exist')
        self._version = version

    def release_version(self, version):
        raise NotImplementedError('version release for git not implemented')

# sanity check: ensure class fully implements the interface (abc)
assert issubclass(Git, BaseVCS), "Git is not a base class of BaseVCS"
