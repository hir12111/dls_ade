from vcs import BaseVCS
from pkg_resources import require
require('GitPython')
import git
import tempfile
import subprocess


class Git(BaseVCS):


    def __init__(self, module, options):

        self.vcs_type = 'git'

        list_cmd = 'ssh dascgitolite@dasc-git.diamond.ac.uk expand controls'
        list_cmd_output = subprocess.check_output(list_cmd.split())

        server_repo_path = 'controls/'+options.area+'/'+module
        if server_repo_path not in list_cmd_output:
            raise Exception('repo not found on gitolite server')

        repo_dir = tempfile.mkdtemp(suffix="_"+module)
        remote_repo = 'ssh://dascgitolite@dasc-git.diamond.ac.uk/'
        remote_repo += server_repo_path

        self.client = git.Repo.clone_from(remote_repo, repo_dir)


    def cat(self, filename, version):
        ''' Fetch contents of file in repository, requires tag/version '''
        return self.client.git.cat_file('-p', version+':'+filename)


    def list_releases(self, module, area):
        ''' Return list of release tags of module '''
        releases = []
        for tag in self.client.tags:
            releases.append(tag.name)
        return releases


    def set_log_message(self, message):
        ''' Git support will not do a commit, so log message not needed. '''
        return None


    def check_version_exists(self, version):
        pass


# sanity check: ensure class fully implements the interface (abc)
assert issubclass(Git, BaseVCS)
