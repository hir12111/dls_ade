"""Perform checks on the validity of a Python 3 module.
"""
from distutils.errors import DistutilsFileError
from setuptools.config import read_configuration
import sys

import git
from git.exc import InvalidGitRepositoryError
from pipfile import Pipfile


USAGE = '''{} [version]: check validity of Python 3 module.

Check that the version in setup.cfg matches a tag on the current commit.
If version is provided, check that it matches the version in setup.cfg.

Check that the dependencies in setup.cfg match those in Pipfile.
'''


def usage():
    print(USAGE.format(sys.argv[0]))


def compare_requirements(pipenv_reqs, setup_reqs):
    return sorted(list(pipenv_reqs.keys())) == sorted(list(setup_reqs))


def get_tags_on_head(repo):
    head = repo.head.commit
    matching_tags = []
    for tag in repo.tags:
        if tag.commit == head:
            matching_tags.append(tag.name)

    return matching_tags


def main():
    provided_version = None
    if len(sys.argv) > 1:
        if sys.argv[1] in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            provided_version = sys.argv[1]

    # Load data
    try:
        conf_dict = read_configuration('setup.cfg')
    except DistutilsFileError:
        print('WARNING: no setup.cfg file found; checks cannot be made')
        # We can't check but we must allow the build to continue.
        sys.exit()
    try:
        pipfile_data = Pipfile.load('Pipfile').data
    except FileNotFoundError:
        print('ERROR: no Pipfile found. Package is not valid')
        sys.exit(1)
    try:
        repo = git.Repo('.')
    except InvalidGitRepositoryError:
        print('ERROR: no Git repository found. Package is not valid')
        sys.exit(1)

    # Compare requirements
    pipenv_requirements = pipfile_data['default']
    setup_requirements = conf_dict['options'].get('install_requires', [])
    if not compare_requirements(pipenv_requirements, setup_requirements):
        print('setup.cfg requirements: {}'.format(setup_requirements))
        print('Pipfile requirements: {}'.format(pipenv_requirements))
        sys.exit('Requirements in setup.cfg and Pipfile do not match')
    # Compare versions
    head_tags = get_tags_on_head(repo)
    setup_version = conf_dict['metadata']['version']
    if setup_version not in head_tags:
        sys.exit('No tag on HEAD matches setup.cfg version {}'.format(
            setup_version
        ))
    if provided_version is not None:
        if not setup_version == provided_version:
            error = 'Release version {} does not match setup.cfg version {}.'
            sys.exit(error.format(provided_version, setup_version))
