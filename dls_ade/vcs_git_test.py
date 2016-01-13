from dls_ade import vcs_git
import os
import unittest
from pkg_resources import require
require("mock")
from mock import patch, ANY, MagicMock, PropertyMock  # @UnresolvedImport


def setUpModule():
    vcs_git.GIT_SSH_ROOT = "ssh://GIT_SSH_ROOT/"
    vcs_git.GIT_ROOT_DIR = "controlstest"


class IsGitDirTest(unittest.TestCase):

    def test_given_invalid_file_path_then_error_raised(self):
        path = "/not/a/path"

        with self.assertRaises(Exception):
            vcs_git.is_git_dir(path)

    def test_given_not_git_dir_then_returns_false(self):
        path = "/"

        return_value = vcs_git.is_git_dir(path)

        self.assertFalse(return_value)

    @patch('dls_ade.vcs_git.git')
    def test_given_git_dir_then_returns_true(self, mock_git):
        path = "/"

        git_inst = MagicMock()
        mock_git.Repo.return_value = git_inst

        return_value = vcs_git.is_git_dir(path)

        self.assertTrue(return_value)


class IsGitRootDirTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.is_git_dir', return_value=True)
    @patch('dls_ade.vcs_git.git')
    def test_given_git_dir_then_git_repo_assigned_to_path(self, mock_git, _2):
        path = "test/path"

        git_inst = MagicMock()
        mock_git.Repo = git_inst

        vcs_git.is_git_root_dir(path)

        git_inst.assert_called_once_with(path)

    @patch('dls_ade.vcs_git.is_git_dir', return_value=False)
    @patch('dls_ade.vcs_git.git')
    def test_given_not_git_dir_then_git_repo_not_assigned(self, mock_git, _2):
        path = "test/path"

        git_inst = MagicMock()
        mock_git.Repo = git_inst

        vcs_git.is_git_root_dir(path)

        self.assertFalse(git_inst.call_count)

    @patch('dls_ade.vcs_git.os.getcwd', return_value="top/level/")
    @patch('dls_ade.vcs_git.is_git_dir', return_value=True)
    @patch('dls_ade.vcs_git.git')
    def test_given_git_dir_and_at_top_level_then_return_true(self, mock_git, _2, _3):
        path = "test/path"

        git_inst = MagicMock()
        mock_git.Repo.return_value = git_inst
        git_inst.git.rev_parse.return_value = "top/level/test/path"

        return_value = vcs_git.is_git_root_dir(path)

        self.assertTrue(return_value)

    @patch('dls_ade.vcs_git.os.getcwd', return_value="not/top/level/")
    @patch('dls_ade.vcs_git.is_git_dir', return_value=True)
    @patch('dls_ade.vcs_git.git')
    def test_given_git_dir_and_at_top_level_then_return_false(self, mock_git, _2, _3):
        path = "test/path"

        git_inst = MagicMock()
        mock_git.Repo.return_value = git_inst
        git_inst.git.rev_parse.return_value = "top/level/test/path"

        return_value = vcs_git.is_git_root_dir(path)

        self.assertFalse(return_value)

    @patch('dls_ade.vcs_git.is_git_dir', return_value=False)
    @patch('dls_ade.vcs_git.git')
    def test_given_not_git_dir_then_git_repo_return_false(self, mock_git, _2):
        path = "/test/path"

        git_inst = MagicMock()
        mock_git.Repo = git_inst

        return_value = vcs_git.is_git_root_dir(path)

        self.assertFalse(return_value)


class IsInRepoTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.subprocess.check_output', return_value=['controls/test/path'])
    def test_given_path_exists_then_return_true(self, mock_check):

        self.assertTrue(vcs_git.is_repo_path("controls/test/path"))

    @patch('dls_ade.vcs_git.subprocess.check_output', return_value=['controls/test/otherpath'])
    def test_given_path_does_not_exist_then_return_false(self, mock_check):

        self.assertFalse(vcs_git.is_repo_path("controls/test/path"))


class InitRepoTest(unittest.TestCase):

    def setUp(self):

        self.patch_is_dir = patch('dls_ade.vcs_git.os.path.isdir')
        self.patch_is_git_root_dir = patch('dls_ade.vcs_git.is_git_root_dir')
        self.patch_git_repo_init = patch('dls_ade.vcs_git.git.Repo.init')

        self.addCleanup(self.patch_is_dir.stop)
        self.addCleanup(self.patch_is_git_root_dir.stop)
        self.addCleanup(self.patch_git_repo_init.stop)

        self.mock_is_dir = self.patch_is_dir.start()
        self.mock_is_git_root_dir = self.patch_is_git_root_dir.start()
        self.mock_git_repo_init = self.patch_git_repo_init.start()

    def test_given_is_dir_false_then_exception_raised_with_correct_message(self):

        self.mock_is_dir.return_value = False

        comp_message = "Path {path:s} is not a directory".format(path="fake_path")

        with self.assertRaises(Exception) as e:
            vcs_git.init_repo("fake_path")

        self.mock_is_dir.assert_called_once_with("fake_path")
        self.assertEqual(str(e.exception), comp_message)

    def test_given_is_dir_true_but_is_git_root_dir_also_true_then_exception_raised_with_correct_message(self):

        self.mock_is_dir.return_value = True
        self.mock_is_git_root_dir.return_value = True

        comp_message = "Path {path:s} is already a git repository".format(path="non_repo_path")

        with self.assertRaises(Exception) as e:
            vcs_git.init_repo("non_repo_path")

        self.mock_is_dir.assert_called_once_with("non_repo_path")
        self.assertEqual(str(e.exception), comp_message)

    def test_given_both_tests_pass_then_repo_initialised_correctly(self):

        self.mock_is_dir.return_value = True
        self.mock_is_git_root_dir.return_value = False

        vcs_git.init_repo("test_path")

        self.mock_git_repo_init.assert_called_once_with("test_path")

    def test_given_no_input_then_sensible_default_applied(self):

        self.mock_is_dir.return_value = True
        self.mock_is_git_root_dir.return_value = False

        vcs_git.init_repo()

        self.mock_is_dir.assert_called_once_with("./")


class StageAllFilesAndCommitTest(unittest.TestCase):

    def setUp(self):
        self.patch_is_dir = patch('dls_ade.vcs_git.os.path.isdir')
        self.patch_is_git_root_dir = patch('dls_ade.vcs_git.is_git_root_dir')
        self.patch_git_repo = patch('dls_ade.vcs_git.git.Repo')

        self.addCleanup(self.patch_is_dir.stop)
        self.addCleanup(self.patch_is_git_root_dir.stop)
        self.addCleanup(self.patch_git_repo.stop)

        self.mock_is_dir = self.patch_is_dir.start()
        self.mock_is_git_root_dir = self.patch_is_git_root_dir.start()
        self.mock_git_repo = self.patch_git_repo.start()

        self.mock_repo = MagicMock()

        self.mock_git_repo.return_value = self.mock_repo

    def test_given_is_dir_false_then_exception_raised_with_correct_message(self):

        self.mock_is_dir.return_value = False

        comp_message = "Path {path:s} is not a directory".format(path="fake_path")

        with self.assertRaises(Exception) as e:
            vcs_git.stage_all_files_and_commit("fake_path")

        self.mock_is_dir.assert_called_once_with("fake_path")
        self.assertEqual(str(e.exception), comp_message)

    def test_given_is_dir_true_but_is_git_root_dir_false_then_exception_raised_with_correct_message(self):

        self.mock_is_dir.return_value = True
        self.mock_is_git_root_dir.return_value = False

        comp_message = "Path {path:s} is not a git repository".format(path="non_repo_path")

        with self.assertRaises(Exception) as e:
            vcs_git.stage_all_files_and_commit("non_repo_path")

        self.mock_is_dir.assert_called_once_with("non_repo_path")
        self.assertEqual(str(e.exception), comp_message)

    def test_given_both_tests_pass_then_repo_staged_and_committed_correctly(self):

        self.mock_is_dir.return_value = True
        self.mock_is_git_root_dir.return_value = True

        vcs_git.stage_all_files_and_commit("test_path")

        self.mock_repo.git.add.assert_called_once_with("--all")
        self.mock_repo.git.commit.assert_called_once_with(m="Initial commit")

    def test_given_no_input_then_sensible_default_applied(self):

        self.mock_is_dir.return_value = True
        self.mock_is_git_root_dir.return_value = True

        vcs_git.stage_all_files_and_commit()

        self.mock_is_dir.assert_called_once_with("./")


class AddNewRemoteAndPushTest(unittest.TestCase):

    class BranchEntry(object):
        def __init__(self, name):
            self.name = name  # Allows us to specify x.name in list comprehension

    class RemoteEntry(object):
        def __init__(self, name):
            self.name = name

    class StubGitRepo(object):  # Used to mock out the git.Repo() function
        def __init__(self, branches_list, remotes_list, mock_remote, mock_create_remote):
            self.branches = branches_list  # set this to a list eg. [BranchEntry("branch_name")] for list comprehension
            self.remotes = remotes_list
            self.mock_remote = mock_remote
            self.mock_create_remote = mock_create_remote

        def create_remote(self, *args):
            self.mock_create_remote(*args)  # allows us to interrogate the calls to repo.create_remote()
            return self.mock_remote

    def setUp(self):
        self.patch_is_git_root_dir = patch('dls_ade.vcs_git.is_git_root_dir')
        self.patch_create_remote_repo = patch('dls_ade.vcs_git.create_remote_repo')
        self.patch_git = patch('dls_ade.vcs_git.git')

        self.addCleanup(self.patch_is_git_root_dir.stop)
        self.addCleanup(self.patch_create_remote_repo.stop)
        self.addCleanup(self.patch_git.stop)

        self.mock_is_git_root_dir = self.patch_is_git_root_dir.start()
        self.mock_create_remote_repo = self.patch_create_remote_repo.start()
        self.mock_git = self.patch_git.start()

    def test_given_is_git_root_dir_false_then_exception_raised_with_correct_message(self):

        self.mock_is_git_root_dir.return_value = False

        comp_message = "Path {path:s} is not a git repository"
        comp_message = comp_message.format(path="test_path")

        with self.assertRaises(Exception) as e:
            vcs_git.add_new_remote_and_push("test_destination", path="test_path")

        self.mock_is_git_root_dir.assert_called_once_with("test_path")
        self.assertEqual(str(e.exception), comp_message)

    def test_given_is_git_root_dir_true_then_git_repo_called_with_correct_arguments(self):

        self.mock_is_git_root_dir.return_value = True

        try:
            vcs_git.add_new_remote_and_push("test_destination", path="test_path")
        except:
            pass

        self.mock_git.Repo.assert_called_once_with("test_path")

    def test_given_branch_name_not_in_repo_branches_then_exception_raised_with_correct_message(self):

        self.mock_is_git_root_dir.return_value = True
        branches_list = [self.BranchEntry("branch_1"), self.BranchEntry("branch_2"), self.BranchEntry("branch_3")]
        mock_repo = self.StubGitRepo(branches_list, [], MagicMock(), MagicMock())
        self.mock_git.Repo.return_value = mock_repo

        comp_message = "Local repository branch {branch:s} does not currently exist.".format(branch="test_branch")

        with self.assertRaises(Exception) as e:
            vcs_git.add_new_remote_and_push("test_destination", branch_name="test_branch")

        self.assertEqual(str(e.exception), comp_message)

    def test_given_remote_name_in_repo_remotes_then_exception_raised_with_correct_message(self):

        self.mock_is_git_root_dir.return_value = True
        branches_list = [self.BranchEntry("test_branch")]
        remotes_list = [self.RemoteEntry("remote_1"), self.RemoteEntry("remote_2"), self.RemoteEntry("test_remote")]
        mock_repo = self.StubGitRepo(branches_list, remotes_list, MagicMock(), MagicMock())
        self.mock_git.Repo.return_value = mock_repo

        comp_message = "Cannot push local repository to destination as remote {remote:s} is already defined"
        comp_message = comp_message.format(remote="test_remote")

        with self.assertRaises(Exception) as e:
            vcs_git.add_new_remote_and_push("test_destination", remote_name="test_remote", branch_name="test_branch")

        self.assertEqual(str(e.exception), comp_message)

    def test_given_all_checks_pass_then_function_runs_correctly(self):

        mock_remote = MagicMock()  # Mock to represent the 'remote' local variable
        mock_create_remote = MagicMock()  # Mock to represent the 'create_remote' function

        self.mock_is_git_root_dir.return_value = True
        branches_list = [self.BranchEntry("test_branch")]
        mock_repo = self.StubGitRepo(branches_list, [], mock_remote, mock_create_remote)
        self.mock_git.Repo.return_value = mock_repo

        vcs_git.add_new_remote_and_push("test_destination", remote_name="test_remote", branch_name="test_branch")

        self.mock_create_remote_repo.assert_called_once_with("test_destination")
        mock_create_remote.assert_called_once_with("test_remote", "ssh://GIT_SSH_ROOT/test_destination")
        mock_remote.push.assert_called_once_with("test_branch")

    def test_given_only_destination_given_then_sensible_defaults_applied(self):

        mock_remote = MagicMock()  # Mock to represent the 'remote' local variable
        mock_create_remote = MagicMock()  # Mock to represent the 'create_remote' function

        self.mock_is_git_root_dir.return_value = True
        branches_list = [self.BranchEntry("master")]
        mock_repo = self.StubGitRepo(branches_list, [], mock_remote, mock_create_remote)
        self.mock_git.Repo.return_value = mock_repo

        vcs_git.add_new_remote_and_push("test_destination")

        self.mock_is_git_root_dir.assert_called_once_with("./")
        self.mock_create_remote_repo.assert_called_once_with("test_destination")
        mock_create_remote.assert_called_once_with("origin", "ssh://GIT_SSH_ROOT/test_destination")
        mock_remote.push.assert_called_once_with("master")


class CreateRemoteRepoTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.is_repo_path', return_value=False)
    @patch('dls_ade.vcs_git.tempfile.mkdtemp', return_value = 'tempdir')
    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    @patch('dls_ade.vcs_git.shutil.rmtree')
    def test_given_arguments_reasonable_then_function_runs_correctly(self, mock_rmtree, mock_clone_from, mock_mkdtemp, mock_is_repo_path):

        vcs_git.create_remote_repo("test_destination")

        mock_mkdtemp.assert_called_once_with()
        mock_clone_from.assert_called_once_with(os.path.join(vcs_git.GIT_SSH_ROOT, "test_destination"), "tempdir")
        mock_rmtree.assert_called_once_with("tempdir")

    @patch('dls_ade.vcs_git.is_repo_path', return_value=True)
    @patch('dls_ade.vcs_git.tempfile.mkdtemp', return_value = 'tempdir')
    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    @patch('dls_ade.vcs_git.shutil.rmtree')
    def test_given_is_repo_path_true_then_exception_raised_with_correct_message(self, mock_rmtree, mock_clone_from, mock_mkdtemp, mock_is_repo_path):

        comp_message = "{dest:s} already exists".format(dest="test_destination")

        with self.assertRaises(Exception) as e:
            vcs_git.create_remote_repo("test_destination")

        mock_is_repo_path.assert_called_once_with("test_destination")
        self.assertEqual(str(e.exception), comp_message)


class PushToRemoteTest(unittest.TestCase):

    class BranchEntry(object):
        def __init__(self, name):
            self.name = name  # Allows us to specify x.name in list comprehension

    class RemoteEntry(object):
        def __init__(self, name):
            self.name = name

    class StubGitRepo(object):  # Used to mock out the git.Repo() function
        def __init__(self, branches_list, remotes_list, mock_remote, remote_name="origin", remote_url=""):

            self.branches = branches_list  # set this to a list eg. [BranchEntry("branch_name")] for list comprehension
            self.remotes_list = remotes_list
            self.remotes_count = 0

            self.mock_remote = mock_remote
            mock_url = PropertyMock(return_value=remote_url)
            type(self.mock_remote).url = mock_url
            self.remote_name = remote_name

        @property  # Needed to change result for second .branches request - don't want to overload dictionary lookup!
        def remotes(self):
            if self.remotes_count == 0:
                self.remotes_count = 1
                return self.remotes_list
            else:
                return {self.remote_name: self.mock_remote}

    def setUp(self):

        self.patch_is_git_root_dir = patch('dls_ade.vcs_git.is_git_root_dir')
        self.patch_create_remote_repo = patch('dls_ade.vcs_git.create_remote_repo')
        self.patch_is_repo_path = patch('dls_ade.vcs_git.is_repo_path')
        self.patch_git = patch('dls_ade.vcs_git.git')

        self.addCleanup(self.patch_is_git_root_dir.stop)
        self.addCleanup(self.patch_create_remote_repo.stop)
        self.addCleanup(self.patch_is_repo_path.stop)
        self.addCleanup(self.patch_git.stop)

        self.mock_is_git_root_dir = self.patch_is_git_root_dir.start()
        self.mock_create_remote_repo = self.patch_create_remote_repo.start()
        self.mock_is_repo_path = self.patch_is_repo_path.start()
        self.mock_git = self.patch_git.start()

    def test_given_is_git_root_dir_false_then_exception_raised_with_correct_message(self):

        self.mock_is_git_root_dir.return_value = False

        comp_message = "Path {path:s} is not a git repository".format(path="test_path")

        with self.assertRaises(Exception) as e:
            vcs_git.push_to_remote(path="test_path")

        self.mock_is_git_root_dir.assert_called_once_with("test_path")
        self.assertEqual(str(e.exception), comp_message)

    def test_given_is_git_root_dir_true_then_git_repo_called_with_correct_arguments(self):

        self.mock_is_git_root_dir.return_value = True

        try:
            vcs_git.push_to_remote(path="test_path")
        except:
            pass

        self.mock_git.Repo.assert_called_once_with("test_path")

    def test_given_branch_name_not_in_repo_branches_then_exception_raised_with_correct_message(self):

        self.mock_is_git_root_dir.return_value = True
        branches_list = [self.BranchEntry("branch_1"), self.BranchEntry("branch_2"), self.BranchEntry("branch_3")]
        mock_repo = self.StubGitRepo(branches_list, [], MagicMock())
        self.mock_git.Repo.return_value = mock_repo

        comp_message = "Local repository branch {branch:s} does not currently exist.".format(branch="test_branch")

        with self.assertRaises(Exception) as e:
            vcs_git.push_to_remote(branch_name="test_branch")

        self.assertEqual(str(e.exception), comp_message)

    def test_given_remote_name_does_not_exist_then_exception_raised_with_correct_message(self):

        self.mock_is_git_root_dir.return_value = True
        branches_list = [self.BranchEntry("test_branch")]
        remotes_list = [self.RemoteEntry("remote_1"), self.RemoteEntry("remote_2"), self.RemoteEntry("remote_3")]
        mock_repo = self.StubGitRepo(branches_list, remotes_list, MagicMock())
        self.mock_git.Repo.return_value = mock_repo

        comp_message = "Local repository does not have remote {remote:s}".format(remote="test_remote")

        with self.assertRaises(Exception) as e:
            vcs_git.push_to_remote(remote_name="test_remote", branch_name="test_branch")

        self.assertEqual(str(e.exception), comp_message)

    def test_given_remote_url_does_not_start_with_git_ssh_root_then_exception_raised_with_correct_message(self):

        self.mock_is_git_root_dir.return_value = True
        branches_list = [self.BranchEntry("test_branch")]
        remotes_list = [self.RemoteEntry("test_remote")]
        mock_repo = self.StubGitRepo(branches_list, remotes_list, MagicMock(), "test_remote", "ssh://GIT_FAKE_SSH_ROOT/test_URL")
        self.mock_git.Repo.return_value = mock_repo

        comp_message = "Remote repository URL {remoteURL:s} does not begin with the gitolite server path".format(remoteURL="ssh://GIT_FAKE_SSH_ROOT/test_URL")

        with self.assertRaises(Exception) as e:
            vcs_git.push_to_remote(remote_name="test_remote", branch_name="test_branch")
        self.assertEqual(str(e.exception), comp_message)

    def test_given_is_repo_path_true_then_exception_raised_with_correct_message(self):

        mock_remote = MagicMock()

        self.mock_is_git_root_dir.return_value = True
        branches_list = [self.BranchEntry("test_branch")]
        remotes_list = [self.RemoteEntry("test_remote")]
        mock_repo = self.StubGitRepo(branches_list, remotes_list, mock_remote, "test_remote", "ssh://GIT_SSH_ROOT/test_URL")
        self.mock_git.Repo.return_value = mock_repo

        self.mock_is_repo_path.return_value = False

        comp_message = "Server repo path {s_repo_path:s} does not currently exist".format(s_repo_path="test_URL")

        with self.assertRaises(Exception) as e:
            vcs_git.push_to_remote(remote_name="test_remote", branch_name="test_branch")
        self.assertEqual(str(e.exception), comp_message)

        self.mock_is_repo_path.assert_called_once_with("test_URL")

    def test_given_all_checks_pass_then_function_runs_correctly(self):

        mock_remote = MagicMock()

        self.mock_is_git_root_dir.return_value = True
        branches_list = [self.BranchEntry("test_branch")]
        remotes_list = [self.RemoteEntry("test_remote")]
        mock_repo = self.StubGitRepo(branches_list, remotes_list, mock_remote, "test_remote", "ssh://GIT_SSH_ROOT/test_URL")
        self.mock_git.Repo.return_value = mock_repo

        self.mock_is_repo_path.return_value = True

        vcs_git.push_to_remote(remote_name="test_remote", branch_name="test_branch")

        mock_remote.push.assert_called_once_with("test_branch")

    def test_given_no_input_then_sensible_defaults_applied(self):

        mock_remote = MagicMock()

        self.mock_is_git_root_dir.return_value = True
        branches_list = [self.BranchEntry("master")]  # Set these to the function's default values
        remotes_list = [self.RemoteEntry("origin")]
        mock_repo = self.StubGitRepo(branches_list, remotes_list, mock_remote, "origin", "ssh://GIT_SSH_ROOT/test_URL")
        self.mock_git.Repo.return_value = mock_repo

        vcs_git.push_to_remote()

        self.mock_is_git_root_dir.assert_called_once_with("./")
        mock_remote.push.assert_called_once_with("master")


class CloneTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.is_repo_path', return_value=False)
    @patch('git.Repo.clone_from')
    def test_given_invalid_source_then_error_raised(self, mock_clone_from, mock_is_repo_path):
        source = "does/not/exist"
        module = "test_module"

        with self.assertRaises(Exception):
            vcs_git.clone(source, module)

    @patch('dls_ade.vcs_git.is_repo_path', return_value=True)
    @patch('git.Repo.clone_from')
    def test_given_valid_source_then_no_error_raised(self, mock_clone_from, mock_is_repo_path):
        source = "does/exist"
        module = "test_module"

        vcs_git.clone(source, module)

    @patch('os.path.isdir', return_value=True)
    @patch('dls_ade.vcs_git.is_repo_path', return_value=True)
    @patch('git.Repo.clone_from')
    def test_given_existing_module_name_then_error_raised(self, mock_clone_from, mock_is_repo_path, mock_isdir):
        source = "test/source"
        module = "already_exists"

        with self.assertRaises(Exception):
            vcs_git.clone(source, module)

    @patch('os.path.isdir', return_value=False)
    @patch('dls_ade.vcs_git.is_repo_path', return_value=True)
    @patch('git.Repo.clone_from')
    def test_given_valid_module_name_then_no_error_raised(self, mock_clone_from, mock_is_repo_path, mock_isdir):
        source = "test/source"
        module = "test_module"

        vcs_git.clone(source, module)

    @patch('dls_ade.vcs_git.is_repo_path', return_value=True)
    @patch('dls_ade.vcs_git.os.path.isdir', return_value=False)
    @patch('git.Repo.clone_from')
    def test_given_valid_inputs_then_clone_from_function_called(self, mock_clone_from,
                                                              mock_is_repo_path, mock_clone):
        source = "test/source"
        module = "test_module"

        vcs_git.clone(source, module)

        mock_clone.assert_called_once_with(ANY)


class TempCloneTest(unittest.TestCase):

    def setUp(self):
        self.patch_mkdtemp = patch('dls_ade.vcs_git.tempfile.mkdtemp')
        self.addCleanup(self.patch_mkdtemp.stop)
        self.mock_mkdtemp = self.patch_mkdtemp.start()

        self.mock_mkdtemp.return_value = "tempdir"

    @patch('dls_ade.vcs_git.is_repo_path', return_value=False)
    @patch('git.Repo.clone_from')
    def test_given_invalid_source_then_error_raised(self, mock_clone_from, mock_is_repo_path):
        source = "/does/not/exist"

        with self.assertRaises(Exception):
            vcs_git.temp_clone(source)

    @patch('dls_ade.vcs_git.is_repo_path', return_value=True)
    @patch('git.Repo.clone_from')
    def test_given_valid_source_then_no_error_raised(self, mock_clone_from, mock_is_repo_path):
        source = "/does/exist"

        vcs_git.temp_clone(source)

    @patch('dls_ade.vcs_git.is_repo_path', return_value=True)
    @patch('git.Repo.clone_from')
    def test_given_valid_inputs_then_clone_from_function_called(self, mock_clone_from,
                                                              mock_is_repo_path):
        root = "ssh://GIT_SSH_ROOT/"
        source = "test/source"

        vcs_git.temp_clone(source)

        mock_clone_from.assert_called_once_with(root + source, "tempdir")


class CloneMultiTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.is_repo_path', return_value=False)
    @patch('git.Repo.clone_from')
    def test_given_invalid_source_then_error_raised(self, mock_clone_from, mock_is_repo_path):
        source = "/does/not/exist"

        with self.assertRaises(Exception):
            vcs_git.clone_multi(source)

    @patch('dls_ade.vcs_git.get_repository_list')
    @patch('dls_ade.vcs_git.is_repo_path', return_value=True)
    @patch('git.Repo.clone_from')
    def test_given_valid_source_then_no_error_raised(self, mock_clone_from, mock_is_repo_path, _1):
        source = "/does/exist"

        vcs_git.clone_multi(source)

    @patch('dls_ade.vcs_git.get_repository_list', return_value=["controls/area/test_module"])
    @patch('os.listdir', return_value=["test_module"])
    @patch('dls_ade.vcs_git.is_repo_path', return_value=True)
    @patch('git.Repo.clone_from')
    def test_given_existing_module_name_then_not_cloned(self, mock_clone_from, mock_is_repo_path, _1, _2):
        source = "area/test_module"

        vcs_git.clone_multi(source)

        self.assertFalse(mock_clone_from.call_count)

    @patch('dls_ade.vcs_git.get_repository_list', return_value=["controls/area/test_module"])
    @patch('os.listdir', return_value=["not_test_module"])
    @patch('dls_ade.vcs_git.is_repo_path', return_value=True)
    @patch('git.Repo.clone_from')
    def test_given_valid_module_name_then_clone(self, mock_clone_from, mock_is_repo_path, _1, _2):
        source = "area/test_module"

        vcs_git.clone_multi(source)

        mock_clone_from.assert_called_once_with(vcs_git.GIT_SSH_ROOT + "controls/" + source, "./test_module")


class ListRemoteBranchesTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.os.chdir')
    @patch('dls_ade.vcs_git.git')
    def test_given_module_with_invalid_entries_then_removed(self, mock_git, _2):

        repo_inst = MagicMock()
        repo_inst.references = ["origin/HEAD", "origin/master",
                                "origin/1-5-8fixes", "master",
                                "waveforms", "1-0, 2-1"]
        repo_inst.branches = ["master", "waveforms"]
        repo_inst.tags = ["1-0, 2-1"]

        branches = vcs_git.list_remote_branches(repo_inst)

        self.assertNotIn('->', branches)
        self.assertNotIn('HEAD', branches)
        self.assertIn('master', branches)
        self.assertNotIn('1-0', branches)
        self.assertNotIn('2-1', branches)

    @patch('dls_ade.vcs_git.os.chdir')
    @patch('dls_ade.vcs_git.git')
    def test_given_module_with_valid_entries_then_not_removed(self, mock_git, _2):

        repo = MagicMock()
        mock_git.Repo = repo
        repo.references = ["origin/1-5-8fixes", "origin/3-x-branch",
                                        "origin/3104_rev14000a_support"]


        branches = vcs_git.list_remote_branches(repo)

        self.assertIn('1-5-8fixes', branches)
        self.assertIn('3-x-branch', branches)
        self.assertIn('3104_rev14000a_support', branches)


class CheckoutRemoteBranchTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.list_remote_branches', return_value=['test_module'])
    @patch('dls_ade.vcs_git.git')
    def test_given_valid_branch_then_checkout_called(self, mock_git, _2):
        branch = "test_module"

        repo = MagicMock()
        mock_git.Repo = repo

        vcs_git.checkout_remote_branch(branch, repo)

        repo.git.checkout.assert_called_once_with("-b", branch, "origin/" + branch)

    @patch('dls_ade.vcs_git.list_remote_branches', return_value=['test_module'])
    @patch('dls_ade.vcs_git.git')
    def test_given_invalid_branch_then_checkout_not_called(self, mock_git, _2):
        branch = "not_a_module"

        repo = MagicMock()
        mock_git.Repo = repo

        vcs_git.checkout_remote_branch(branch, repo)

        self.assertFalse(repo.git.checkout.call_count)


class GitClassInitTest(unittest.TestCase):

    def setUp(self):

        self.patch_is_repo_path = patch('dls_ade.vcs_git.is_repo_path')
        self.addCleanup(self.patch_is_repo_path.stop)
        self.mock_is_repo_path = self.patch_is_repo_path.start()

    def test_given_nonsense_module_options_args_then_class_instance_should_fail(self):

        with self.assertRaises(Exception):
            vcs_git.Git(1, 2)


    @patch('dls_ade.vcs_git.tempfile.mkdtemp')
    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    def test_given_args_for_real_repo_then_do_not_raise_exception(self, _1, _2):

        self.mock_is_repo_path.return_value = True

        try:
            vcs_git.Git('dummy', FakeOptions())
        except Exception, e:
            self.fail(e)

    @patch('dls_ade.vcs_git.tempfile.mkdtemp')
    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    def test_given_repo_exists_then_create_temp_dir_to_clone_into(self, mock_clone, mock_temp):

        self.mock_is_repo_path.return_value = True

        module = "dummy"
        options = FakeOptions()

        vcs_git.Git(module, options)

        mock_temp.assert_called_once_with(suffix="_dummy")

    @patch('dls_ade.vcs_git.tempfile.mkdtemp')
    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    def test_given_repo_does_not_exist_then_git_clone_should_not_be_called(self, mock_clone, mock_temp):

        self.mock_is_repo_path.return_value = False

        module = "dummy"
        options = FakeOptions()

        with self.assertRaises(Exception):
            vcs_git.Git(module, options)

        n_clone_calls = mock_clone.call_count
        n_temp_calls = mock_temp.call_count

        self.assertEqual(0, n_clone_calls)
        self.assertEqual(0, n_temp_calls)

    @patch('dls_ade.vcs_git.tempfile.mkdtemp')
    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    def test_given_repo_exists_then_git_clone_called(self, mock_clone, _):

        self.mock_is_repo_path.return_value = True

        repo_url = "ssh://GIT_SSH_ROOT/controls/support/dummy"
        module = "dummy"
        options = FakeOptions()

        vcs = vcs_git.Git(module, options)

        n_clone_calls = mock_clone.call_count

        self.assertEqual(1, n_clone_calls)

    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    def test_given_repo_exists_then_git_clone_called_with_remote_url_and_tempdir_args(self, mock_clone):

        self.mock_is_repo_path.return_value = True

        repo_url = "ssh://GIT_SSH_ROOT/controls/support/dummy"
        module = "dummy"
        options = FakeOptions()

        vcs = vcs_git.Git(module, options)

        args, kwargs = mock_clone.call_args
        target_dir = args[1]
        remote_repo_called = args[0]

        os.rmdir(target_dir)

        self.assertTrue(target_dir.startswith("/tmp/tmp"))
        self.assertTrue(target_dir.endswith("_" + module))
        self.assertGreater(len(target_dir), len(module)+9)

    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    def test_given_repo_with_domain_code_then_tempdir_arg_has_forwardslash_removed(self, mock_clone):

        self.mock_is_repo_path.return_value = True

        repo_url = "ssh://GIT_SSH_ROOT/controls/ioc/domain/mod"
        module = "domain/mod"
        options = FakeOptions(area="ioc")

        vcs = vcs_git.Git(module, options)

        args, kwargs = mock_clone.call_args
        target_dir = args[1]

        os.rmdir(target_dir)

        self.assertTrue(target_dir.startswith("/tmp/tmp"))
        self.assertTrue(target_dir.endswith("_" + module.replace("/","_")))


class GitCatTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.git.Repo.clone_from', return_value=vcs_git.git.Repo)  # @UndefinedVariable
    @patch('dls_ade.vcs_git.tempfile.mkdtemp')
    def setUp(self, mtemp, mclone):

        self.patch_is_repo_path = patch('dls_ade.vcs_git.is_repo_path')
        self.addCleanup(self.patch_is_repo_path.stop)
        self.mock_is_repo_path = self.patch_is_repo_path.start()

        self.mock_is_repo_path.return_value = True

        client_cat_patch = patch('dls_ade.vcs_git.git.Repo.git')
        self.addCleanup(client_cat_patch.stop)
        self.mgit = client_cat_patch.start()
        self.mgit.cat_file = MagicMock(return_value=1)

        self.module = 'dummy'
        self.options = FakeOptions()
        self.vcs = vcs_git.Git(self.module, self.options)

    def test_given_version_not_set_when_called_then_second_argument_to_catfile_starts_with_master(self):

        filename = 'configure/RELEASE'
        expected_arg = 'master:' + filename

        self.vcs.cat(filename)

        self.mgit.cat_file.assert_called_once_with(ANY, expected_arg)

    def test_when_called_then_first_arg_is_dash_p(self):

        dash_p_arg = '-p'

        self.vcs.cat('file')

        self.mgit.cat_file.assert_called_once_with(dash_p_arg, ANY)

    @patch('dls_ade.vcs_git.Git.list_releases',return_value='0-2')
    def test_given_version_is_set_when_called_then_second_argument_to_catfile_starts_with_version(self, mlist):

        version = '0-2'
        filename = 'configure/RELEASE'
        expected_arg = version + ':' + filename

        self.vcs.set_version(version)
        self.vcs.cat(filename)

        self.mgit.cat_file.assert_called_once_with(ANY, expected_arg)

    @patch('dls_ade.vcs_git.Git.list_releases',return_value='0-2')
    def test_given_version_is_set_but_non_existent_then_version_used_for_cat_is_master(self, mlist):

        version = '0-3'
        filename = 'configure/RELEASE'
        expected_arg = 'master:' + filename

        self.vcs._version = version
        self.vcs.cat(filename)

        self.mgit.cat_file.assert_called_once_with(ANY, expected_arg)


class GitListReleasesTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    @patch('dls_ade.vcs_git.tempfile.mkdtemp')
    def setUp(self, mtemp, mclone):

        self.patch_is_repo_path = patch('dls_ade.vcs_git.is_repo_path')
        self.addCleanup(self.patch_is_repo_path.stop)
        self.mock_is_repo_path = self.patch_is_repo_path.start()

        self.mock_is_repo_path.return_value = True

        self.module = 'dummy'
        self.options = FakeOptions()

        self.vcs = vcs_git.Git(self.module, self.options)
        self.vcs.client.tags = [FakeTag("1-0"), FakeTag("1-0-1"), FakeTag("2-0")]

    def test_given_repo_with_no_tags_then_return_empty_list(self):

        self.vcs.client.tags = []
        releases = self.vcs.list_releases()

        self.assertListEqual([], releases)

    def test_given_repo_with_some_tags_then_return_list_inc_version_1_0(self):

        releases = self.vcs.list_releases()

        self.assertTrue('1-0' in releases)

    def test_given_repo_with_some_tags_then_return_all_version_tag_names(self):

        releases = self.vcs.list_releases()

        self.assertListEqual(['1-0', '1-0-1', '2-0'], releases)


class GitSetLogMessageTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    @patch('dls_ade.vcs_git.tempfile.mkdtemp')
    def setUp(self, mtemp, mclone):

        self.patch_is_repo_path = patch('dls_ade.vcs_git.is_repo_path')
        self.addCleanup(self.patch_is_repo_path.stop)
        self.mock_is_repo_path = self.patch_is_repo_path.start()

        self.mock_is_repo_path.return_value = True

        self.module = 'dummy'
        self.options = FakeOptions()

        self.vcs = vcs_git.Git(self.module, self.options)

    def test_given_message_arg_when_method_invoked_then_return_None(self):

        result = self.vcs.set_log_message('reason for commit')

        self.assertIsNone(result)


class GitCheckVersionTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    @patch('dls_ade.vcs_git.tempfile.mkdtemp')
    def setUp(self, mtemp, mclone):

        self.patch_is_repo_path = patch('dls_ade.vcs_git.is_repo_path')
        self.addCleanup(self.patch_is_repo_path.stop)
        self.mock_is_repo_path = self.patch_is_repo_path.start()

        self.mock_is_repo_path.return_value = True

        self.module = 'dummy'
        self.options = FakeOptions()

        self.vcs = vcs_git.Git(self.module, self.options)

    @patch('dls_ade.vcs_git.Git.list_releases')
    def test_given_version_in_list_of_releases_then_return_true(self, mlist):
        
        version = '1-5'
        mlist.return_value = ['1-4','1-5','1-6']

        self.assertTrue(self.vcs.check_version_exists(version))

    @patch('dls_ade.vcs_git.Git.list_releases')
    def test_given_version_not_in_list_of_releases_then_return_false(self, mlist):
        
        version = '1-5'
        mlist.return_value = ['1-4','2-5','1-6']

        self.assertFalse(self.vcs.check_version_exists(version))


class ApiInterrogateTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    @patch('dls_ade.vcs_git.tempfile.mkdtemp')
    def setUp(self, _1, _2):

        self.patch_is_repo_path = patch('dls_ade.vcs_git.is_repo_path')
        self.addCleanup(self.patch_is_repo_path.stop)
        self.mock_is_repo_path = self.patch_is_repo_path.start()

        self.mock_is_repo_path.return_value = True

        self.module = 'dummy'
        self.options = FakeOptions()
        self.vcs = vcs_git.Git(self.module, self.options)

    def test_when_asking_object_for_vcs_type_then_return_git_in_string(self):

        vcs_type = self.vcs.vcs_type

        self.assertEqual(vcs_type, 'git')

    def test_when_calling_source_repo_then_return_url_of_gitolite_repo(self):

        expected_source_repo = 'ssh://GIT_SSH_ROOT/'
        expected_source_repo += 'controlstest/'+self.options.area+'/'+self.module

        source_repo = self.vcs.source_repo

        self.assertEqual(source_repo, expected_source_repo)


class GitSettersTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    @patch('dls_ade.vcs_git.tempfile.mkdtemp')
    def setUp(self, mtemp, mclone):

        self.patch_is_repo_path = patch('dls_ade.vcs_git.is_repo_path')
        self.addCleanup(self.patch_is_repo_path.stop)
        self.mock_is_repo_path = self.patch_is_repo_path.start()

        self.mock_is_repo_path.return_value = True

        self.module = 'dummy'
        self.options = FakeOptions()

        self.vcs = vcs_git.Git(self.module, self.options)

    def test_when_set_branch_called_then_raise_notimplementederror(self):

        with self.assertRaises(NotImplementedError):
            self.vcs.set_branch('some_branch')

    def test_given_vcs_when_version_not_set_then_get_version_raise_error(self):

        with self.assertRaises(Exception):
            self.vcs.version

    @patch('dls_ade.vcs_git.Git.check_version_exists', return_value=True)
    def test_given_vcs_when_version_set_return_version(self, mcheck):

        version = '0-1'

        self.vcs.set_version(version)

        self.assertEqual(self.vcs.version, version)

    @patch('dls_ade.vcs_git.Git.check_version_exists', return_value=False)
    def test_given_nonexistent_version_when_version_set_then_raise_error(self, mcheck):

        version = '0-2'

        with self.assertRaises(Exception):
            self.vcs.set_version(version);


class GitReleaseVersionTest(unittest.TestCase):

    @patch('dls_ade.vcs_git.git.Repo.clone_from')
    @patch('dls_ade.vcs_git.tempfile.mkdtemp')
    def setUp(self, mtemp, mclone):

        self.patch_is_repo_path = patch('dls_ade.vcs_git.is_repo_path')
        self.addCleanup(self.patch_is_repo_path.stop)
        self.mock_is_repo_path = self.patch_is_repo_path.start()

        self.mock_is_repo_path.return_value = True

        self.module = 'dummy'
        self.options = FakeOptions()

        self.vcs = vcs_git.Git(self.module, self.options)

    def test_method_is_not_implemented(self):

        with self.assertRaises(NotImplementedError):
            self.vcs.release_version('some-version')


class FakeTag(object):
    def __init__(self, name):
        self.name = name


class FakeOptions(object):
    def __init__(self, **kwargs):
        self.area = kwargs.get('area', 'support')


if __name__ == '__main__':

    # buffer option suppresses stdout generated from tested code
    unittest.main(buffer=True)
