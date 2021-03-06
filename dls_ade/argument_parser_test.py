#!/bin/env dls-python

import unittest
from dls_ade.argument_parser import ArgParser
from argparse import _StoreAction
from argparse import _StoreTrueAction


class ArgParserInitTest(unittest.TestCase):

    def setUp(self):
        self.parser = ArgParser("")

    def test_area_argument_has_correct_attributes(self):
        option = self.parser._option_string_actions['-a']
        self.assertIsInstance(option, _StoreAction)
        self.assertEqual(option.type, str)
        self.assertEqual(option.dest, "area")
        self.assertIn("--area", option.option_strings)

    def test_python_argument_has_correct_attributes(self):
        option = self.parser._option_string_actions['-p']
        self.assertIsInstance(option, _StoreTrueAction)
        self.assertEqual(option.dest, "python")
        self.assertIn("--python", option.option_strings)

    def test_ioc_argument_has_correct_attributes(self):
        option = self.parser._option_string_actions['-i']
        self.assertIsInstance(option, _StoreTrueAction)
        self.assertEqual(option.dest, "ioc")
        self.assertIn("--ioc", option.option_strings)


class ArgParserParseArgsTest(unittest.TestCase):

    def setUp(self):
        self.parser = ArgParser("")

    def test_given_dash_i_in_args_then_area_is_ioc(self):
        args = self.parser.parse_args("-i".split())

        self.assertEqual(args.area, "ioc")

    def test_given_double_dash_ioc_in_args_then_area_is_ioc(self):
        args = self.parser.parse_args("--ioc".split())

        self.assertEqual(args.area, "ioc")

    def test_given_dash_p_in_args_then_area_is_python(self):
        args = self.parser.parse_args("-p".split())

        self.assertEqual(args.area, "python")

    def test_given_double_dash_python_in_args_then_area_is_python(self):
        args = self.parser.parse_args("--python".split())

        self.assertEqual(args.area, "python")

    def test_given_double_dash_python3_in_args_then_area_is_python3(self):
        args = self.parser.parse_args("--python3".split())

        self.assertEqual(args.area, "python3")


class AddModuleNameTest(unittest.TestCase):

    def setUp(self):
        self.parser = ArgParser("")

    def test_arg_parser_quits_if_module_name_not_added_and_module_name_provided(self):
        try:
            self.parser.parse_args("-p module1".split())
            self.fail("Parser should have quit.")
        except SystemExit:
            pass

    def test_arg_parser_parses_module_name_correctly(self):
        self.parser.add_module_name_arg()
        args = self.parser.parse_args("-p module1".split())
        self.assertEqual(args.module_name, "module1")


class AddReleaseTest(unittest.TestCase):

    def setUp(self):
        self.parser = ArgParser("")

    def test_arg_parser_quits_if_release_not_added_and_release_provided(self):
        try:
            self.parser.parse_args("-p 0-1".split())
            self.fail("Parser should have quit.")
        except SystemExit:
            pass

    def test_arg_parser_parses_release_correctly(self):
        self.parser.add_release_arg()
        args = self.parser.parse_args("-p 0-1".split())
        self.assertEqual(args.release, "0-1")


class AddBranchTest(unittest.TestCase):

    def setUp(self):
        self.parser = ArgParser("")
        self.parser.add_branch_flag()

    def test_branch_argument_has_correct_attributes(self):
        option = self.parser._option_string_actions['-b']
        self.assertIsInstance(option, _StoreAction)
        self.assertEqual(option.type, str)
        self.assertEqual(option.dest, "branch")
        self.assertIn("--branch", option.option_strings)


class AddGitTest(unittest.TestCase):

    def setUp(self):
        self.parser = ArgParser("")
        self.parser.add_git_flag()

    def test_git_option_has_correct_attributes(self):
        option = self.parser._option_string_actions['-g']
        self.assertIsInstance(option, _StoreTrueAction)
        self.assertEqual(option.dest, "git")
        self.assertIn("--git", option.option_strings)


class AddEpicsVersionTest(unittest.TestCase):

    def setUp(self):
        self.parser = ArgParser("")
        self.parser.add_epics_version_flag()

    def test_epics_argument_has_correct_attributes(self):
        option = self.parser._option_string_actions['-e']
        self.assertIsInstance(option, _StoreAction)
        self.assertEqual(option.dest, "epics_version")
        self.assertIn("--epics_version", option.option_strings)


if __name__ == '__main__':

    # buffer option suppresses stdout generated from tested code
    unittest.main(buffer=True)
