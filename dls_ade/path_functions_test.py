import path_functions
import unittest

GIT_SSH_ROOT = "ssh://dascgitolite@dasc-git.diamond.ac.uk/"


class RootTest(unittest.TestCase):

    def test_return_value(self):
        self.assertEqual(path_functions.root(), GIT_SSH_ROOT)


class AreaTest(unittest.TestCase):

    def test_given_area_etc_then_path_to_prod(self):
        typev = "branches"
        area = "etc"

        path = path_functions.area(typev, area)

        self.assertEqual(path, GIT_SSH_ROOT + area + "/" + typev + "/prod")

    def test_given_area_epics_then_path_to_type(self):
        typev = "branches"
        area = "epics"

        path = path_functions.area(typev, area)

        self.assertEqual(path, GIT_SSH_ROOT + area + "/" + typev)

    def test_given_area_tools_then_path_to_build_scripts(self):
        typev = "branches"
        area = "tools"

        path = path_functions.area(typev, area)

        self.assertEqual(path, GIT_SSH_ROOT + "diamond/" + typev + "/build_scripts")

    def test_given_area_tools_then_path_to_area(self):
        typev = "branches"
        area = "other"

        path = path_functions.area(typev, area)

        self.assertEqual(path, GIT_SSH_ROOT + "diamond/" + typev + "/" + area)


class ModuleAreaTests(unittest.TestCase):

    def test_devModule(self):

        area = "etc"
        module = "test_module"

        path = path_functions.devModule(module, area)

        self.assertEqual(path, GIT_SSH_ROOT + area + "/trunk/prod/" + module)

    def test_prodModule(self):

        area = "epics"
        module = "test_module"

        path = path_functions.prodModule(module, area)

        self.assertEqual(path, GIT_SSH_ROOT + area + "/release/" + module)

    def test_branchModule(self):

        area = "tools"
        module = "test_module"

        path = path_functions.branchModule(module, area)

        self.assertEqual(path, GIT_SSH_ROOT + "diamond/branches/build_scripts/" + module)

    def test_vendorModule(self):

        area = "other"
        module = "test_module"

        path = path_functions.vendorModule(module, area)

        self.assertEqual(path, GIT_SSH_ROOT + "diamond/vendor/" + area + "/" + module)

