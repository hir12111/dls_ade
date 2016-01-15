#!/bin/env dls-python

from dls_ade import dls_list_releases
import unittest
from argparse import _StoreAction
from argparse import _StoreTrueAction

from pkg_resources import require
require("mock")
from mock import patch, ANY, MagicMock


class GetRhelVersionTest(unittest.TestCase):

    @patch('dls_ade.dls_list_releases.platform.system', return_value='Linux')
    @patch('dls_ade.dls_list_releases.platform.dist', return_value=['redhat', 'test_release_str.test', 'test_name'])
    def test_given_Linux_Redhat_then_return_release(self, _1, _2):
        release = dls_list_releases.get_rhel_version()

        self.assertEqual(release, 'test_release_str')

    @patch('dls_ade.dls_list_releases.platform.system', return_value='Linux')
    @patch('dls_ade.dls_list_releases.platform.dist', return_value=['not_redhat', 'test_release_str.test', 'test_name'])
    def test_given_Linux_not_Redhat_then_return_default(self, _1, _2):
        release = dls_list_releases.get_rhel_version()

        self.assertEqual(release, '6')

    @patch('dls_ade.dls_list_releases.platform.system', return_value='not_Linux')
    @patch('dls_ade.dls_list_releases.platform.dist', return_value=['redhat', 'test_release_str.test', 'test_name'])
    def test_given_not_Linux_then_return_default(self, _1, _2):
        release = dls_list_releases.get_rhel_version()

        self.assertEqual(release, '6')


class MakeParserTest(unittest.TestCase):

    def setUp(self):
        self.parser = dls_list_releases.make_parser()

    def test_module_name_has_correct_attributes(self):
        arguments = self.parser._positionals._actions[4]
        self.assertEqual(arguments.type, str)
        self.assertEqual(arguments.dest, 'module_name')

    def test_force_argument_has_correct_attributes(self):
        option = self.parser._option_string_actions['-l']
        self.assertIsInstance(option, _StoreTrueAction)
        self.assertEqual(option.dest, "latest")
        self.assertIn("--latest", option.option_strings)

    def test_git_argument_has_correct_attributes(self):
        option = self.parser._option_string_actions['-g']
        self.assertIsInstance(option, _StoreTrueAction)
        self.assertEqual(option.dest, "git")
        self.assertIn("--git", option.option_strings)

    def test_epics_argument_has_correct_attributes(self):
        option = self.parser._option_string_actions['-e']
        self.assertIsInstance(option, _StoreAction)
        self.assertEqual(option.dest, "epics_version")
        self.assertIn("--epics_version", option.option_strings)

    def test_rhel_argument_has_correct_attributes(self):
        option = self.parser._option_string_actions['-r']
        self.assertIsInstance(option, _StoreAction)
        self.assertEqual(option.dest, "rhel_version")
        self.assertIn("--rhel_version", option.option_strings)


class CheckEpicsVersionTest(unittest.TestCase):

    @patch('dls_ade.dls_list_releases.environment.setEpics')
    def test_given_epics_version_with_R_and_match_then_set(self, mock_set_epics):
        epics_version = "R3.14.8.2"

        dls_list_releases.check_epics_version(epics_version)

        mock_set_epics.assert_called_once_with(epics_version)

    @patch('dls_ade.dls_list_releases.environment.setEpics')
    def test_given_epics_version_without_R_and_match_then_set(self, mock_set_epics):
        epics_version = "3.14.8.2"

        dls_list_releases.check_epics_version(epics_version)

        mock_set_epics.assert_called_once_with("R" + epics_version)

    @patch('dls_ade.dls_list_releases.environment.setEpics')
    def test_given_epics_version_with_R_and_not_match_then_raise_error(self, mock_set_epics):
        epics_version = "R3"
        expected_error_message = "Expected epics version like R3.14.8.2, got: " + epics_version

        try:
            dls_list_releases.check_epics_version(epics_version)
        except Exception as error:
            self.assertEqual(error.message, expected_error_message)


class CheckTechnicalAreaTest(unittest.TestCase):

    def test_given_area_not_ioc_then_no_error_raised(self):
        area = "support"
        module = "test_module"

        dls_list_releases.check_technical_area(area, module)

    def test_given_area_ioc_module_split_two_then_no_error_raised(self):
        area = "ioc"
        module = "modules/test_module"

        dls_list_releases.check_technical_area(area, module)

    def test_given_area_ioc_module_split_less_than_two_then_no_error_raised(self):
        area = "ioc"
        module = "test_module"
        expected_error_msg = "Missing Technical Area under Beamline"

        try:
            dls_list_releases.check_technical_area(area, module)
        except Exception as error:
            self.assertEqual(error.message, expected_error_msg)