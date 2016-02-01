#!/bin/env dls-python
# This script comes from the dls_scripts python module
"""
This script removes all O.* directories from a release of a module and tars it up before deleting the release directory.
<module_name>/<module_release> will be stored as <module_name>/<module_release>.tar.gz.
Running the script with the -u flag will untar the module and remove the archive (reversing the original process)
"""

import os
import sys
import vcs_git
import path_functions as pathf
from dls_environment import environment
from argument_parser import ArgParser
import dlsbuild

env = environment()

usage = """
Default <area> is 'support'.
This script removes all O.* directories from a release of a module and
tars it up before deleting the release directory. <module_name>/<module_release>
will be stored as <module_name>/<module_release>.tar.gz. Running the script with
a -u flag will untar the module and remove the archive (reversing the original process)
"""


def make_parser():
    """
    Takes ArgParse instance with default arguments and adds

    Positional Arguments:
        * module_name
        * release

    Flags:
        * -u: untar
        * -e: epics_version

    Returns:
        An ArgumentParser instance with the relevant arguments

    """

    parser = ArgParser(usage)
    parser.add_module_name_arg()
    parser.add_release_arg()
    parser.add_epics_version_flag()

    parser.add_argument(
        "-u", "--untar", action="store_true", dest="untar",
        help="Untar archive created with dls-archive-module.py")

    return parser


def check_area_archivable(area):
    """
    Checks parsed area is a valid option and returns a parser error if not

    Args:
        area: Area to check

    Raises:
        ValueError: Modules in area <args.area> cannot be archived

    """
    if area not in ["support", "ioc", "python", "matlab"]:
        raise ValueError("Modules in area " + area + " cannot be archived")


def check_file_paths(release_dir, archive, untar):
    """
    Checks if the file to untar exists and the directory to build it a does not (if untar is True), or
    checks if the opposite is true (if untar is False)

    Args:
        release_dir: Directory to build to or to tar from
        archive: File to build from or to tar into
        untar: True if building, False if archiving

    Raises:
        IOError: Source does not exist or target already exists

    """
    if untar:
        if not os.path.isfile(archive):
            raise IOError("Archive '{0}' doesn't exist".format(archive))
        if os.path.isdir(release_dir):
            raise IOError("Path '{0}' already exists".format(release_dir))
    else:
        if not os.path.isdir(release_dir):
            raise IOError("Path '{0}' doesn't exist".format(release_dir))
        if os.path.isfile(archive):
            raise IOError("Archive '{0}' already exists".format(archive))


def main():

    parser = make_parser()
    args = parser.parse_args()

    check_area_archivable(args.area)
    env.check_epics_version(args.epics_version)
    pathf.check_technical_area_valid(args.area, args.module_name)
    
    # Check for the existence of release of this module/IOC    
    w_dir = os.path.join(env.prodArea(args.area), args.module_name)
    release_dir = os.path.join(w_dir, args.release)
    archive = release_dir + ".tar.gz"
    check_file_paths(release_dir, archive, args.untar)
    
    # Create build object for release
    build = dlsbuild.ArchiveBuild(args.untar)
    
    if args.epics_version:
        build.set_epics(args.epics_version)
    
    build.set_area(args.area)

    git = vcs_git.Git(args.module_name, args)
    git.set_version(args.release)

    build.submit(git)


if __name__ == "__main__":
    sys.exit(main())
