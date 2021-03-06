#!/usr/bin/env dls-python
# Author: Diamond Light Source, Copyright 2008
#
# License: This file is part of 'dls.environment'
#
# 'dls.environment' is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'dls.environment' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with 'dls.environment'.  If not, see <http://www.gnu.org/licenses/>.

import distro
import logging
import os
import re
from subprocess import Popen, PIPE, STDOUT
try:
    from ConfigParser import SafeConfigParser
except ImportError:  # Python 3
    from configparser import SafeConfigParser

log = logging.getLogger(__name__)


class environment(object):
    """
    A class representing the epics environment of a site.

    If you modify this to suit your site environment, you will be able to use
    any of the dls modules without modification. This module has the idea of
    areas. An area is simply an  argument that can be passed to devArea or
    prodArea. support and ioc must exist to use modules like the dependency
    checker, others may be added. For example the dls support devArea contains
    all support modules, and is located at ``/dls_sw/work/R3.14.12.3/support``.
    This is the area for testing modules. There is a similar prodArea at
    ``/dls_sw/prod/R3.14.12.3/support`` for releases. These are then used to
    locate the root of a particular module.

    Variables
        * epics(str): the version of epics - e.g R3.14.12.3
        * epics_ver_re(:class:`re.RegexObject`): a useful regex for matching
          the version of epics
        * areas(list): the areas that can be passed to devArea() or prodArea()
        * rhel(str): the rhel version e.g. 7

    """

    def __init__(self, epics=None, rhel=None):
        self.epics = None
        self.epics_ver_re = re.compile(r"R\d(\.\d+)+")
        self.rhel = None
        self.areas = [
            "support", "ioc", "matlab", "python",  "python3",
            "python3ext", "etc", "tools", "epics"
        ]
        if epics:
            self.setEpics(epics)
        if rhel:
            self.setRhel(rhel)

    def check_epics_version(self, epics_version):
        """
        Checks if epics version is provided. If it is, checks that it starts
        with 'R' and if not appends an 'R'.
        Then checks if the epics version matches the reg ex.
        Then sets environment epics version.

        Args:
            epics_version(str): Epics version to check

        Raises:
            :class:`exception.Exception`: Expected epics version
            like R3.14.8.2, got <epics_version>

        """
        if epics_version:
            if not epics_version.startswith("R"):
                epics_version = "R{0}".format(epics_version)
            if self.epics_ver_re.match(epics_version):
                self.setEpics(epics_version)
            else:
                raise Exception("Expected epics version like R3.14.8.2, got: "
                                + epics_version)

    def check_rhel_version(self, rhel):
        """
        Checks if rhel version is provided.
        Then sets environment rhel version.

        Args:
            rhel(str): rhel

        """
        if rhel:
            self.setRhel(rhel)

    def setEpicsFromEnv(self):
        """
        Get epics version from the environment, and set self.epics. Set default
        'R3.14.12.3' if environment epics version is inaccessible.

        """
        default_epics = 'R3.14.12.3'
        self.epics = os.environ.get('DLS_EPICS_RELEASE',
                                    os.environ.get('EPICS_RELEASE',
                                                   default_epics))

    def setRhelFromPlatform(self):
        """
        Get rhel version from the platform, and set self.rhel.
        Set default '6' if platform
        version access fails.

        """
        default_rhel = '6'

        self.rhel = default_rhel

        platform_dist = distro.linux_distribution()
        if len(platform_dist) == 3:
            version = platform_dist[1].split(".")
            self.rhel = version[0]

    def copy(self):
        """
        Return a copy of self.

        Returns:
            :class:`~dls_ade.dls_environment.environment`:
             A copy of the environment instance

        """
        return environment(self.epicsVer())

    def setEpics(self, epics):
        """
        Force the version of epics in self.

        Args:
            epics(str): EPICS version
        """
        self.epics = epics

    def setRhel(self, rhel):
        """
        Force the version of rhel in self.

        Args:
            rhel(str): rhel linux version
        """
        self.rhel = rhel

    def epicsDir(self):
        """
        Return the root directory of the epics installation.

        Returns:
            str:
                * `epicsVer` < R3.14: /home/epics
                * `epicsVer` > R3.14: /dls_sw/epics

        """
        if self.epicsVer() < "R3.14":
            return os.path.join("/home", "epics", self.epicsVerDir())
        else:
            return os.path.join("/dls_sw", "epics", self.epicsVerDir())

    def epicsVer(self):
        """
        Return the version of epics from self. If it not set, try and get it
        from the environment.
        This may have a _64 suffix for 64 bit architectures.

        Returns:
            str: Epics version

        """
        if not self.epics:
            self.setEpicsFromEnv()
        return self.epics

    def rhelVer(self):
        """
        Return the version of rhel from self. If it not set, try and get it
        from the platform.

        Returns:
            str: Rhel version

        """
        if not self.rhel:
            self.setRhelFromPlatform()
        return self.rhel

    def epicsVerDir(self):
        """
        Return the directory version of epics from self. If it not set, try and
        get it from the environment.
        This will not have a _64 suffix for 64 bit architectures.

        Returns:
            str: Epics directory version

        """
        if not self.epics:
            self.setEpicsFromEnv()
        return self.epics.split("_")[0]

    def rhelVerDir(self):
        """
        Return the distribution directory from self. If it not set, return a
        default.

        Returns:
            str: Distribution directory

        """
        if not self.rhel:
            self.setRhelFromPlatform()
        return "RHEL"+self.rhel+"-x86_64"

    def devArea(self, area="support"):
        """
        Return the development directory for a particular area and epics
        version.

        Args:
            area(str): Area to generate path for

        Returns:
            str: the appropriate work directory

        """
        if area not in self.areas:
            raise Exception("Only the following areas are supported: " +
                            ", ".join(self.areas))

        if area in ["support", "ioc"]:
            return os.path.join("/dls_sw/work", self.epicsVerDir(), area)
        elif area in ["epics", "etc"]:
            return os.path.join("/dls_sw/work", area)
        elif area in ["tools"]:
            return os.path.join("/dls_sw/work", area, self.rhelVerDir())
        elif area in ["python3", "python3ext"]:  # These use the same area
            return os.path.join("/dls_sw/work/python3", self.rhelVerDir())
        elif area == "python":
            return os.path.join("/dls_sw/work/common", area, self.rhelVerDir())
        elif area == "matlab":
            return os.path.join("/dls_sw/work/common", area)
        else:
            raise Exception("Area {} has no dev area".format(area))

    def prodArea(self, area="support"):
        """
        Return the production directory for a particular area.

        Args:
            area: Area to generate path for

        Returns:
            str:
            * `area` is epics: /dls_sw/<area>
            * Else: devArea(`area`) path with 'work' replaced by 'prod' -
              see devArea() doc string

        """
        if area in ["epics"]:
            return os.path.join("/dls_sw", area)
        else:
            return self.devArea(area).replace("work", "prod")

    def normaliseRelease(self, release):
        """
        Format release tag into a sortable list of components.

        Example: 4-5beta2dls1-3 => [4,'z',5,'beta2z',0,'',1,'z',3,'z',0,'']
        Note: The z allows us to sort alpha, beta and release candidates before
        release numbers without a text suffix

        Args:
            release(str): Area to generate path for

        Returns:
            list: Component parts of release tag

        """
        components = []
        # first split by dls: 4-5beta2dls1-3 --> 4-5beta2 and 1-3
        for part in release.split("dls", 1):
            # rejig separators
            part = part.replace(".", "-").replace("_", "-")
            # allow up to 3 -'s: 4-5beta2 --> 4, 5 and beta2
            for subpart in part.split("-", 3):
                match = re.match("\d+", subpart)
                if match:
                    # turn the digit to an int so it sorts properly
                    components.append(int(match.group()))
                    suffix = subpart[match.start() + len(match.group()):]
                    if suffix == '':
                        components.append('z')
                    else:
                        components.append(suffix)
                else:
                    # just add the string part
                    components.append(0)
                    components.append(subpart)
            # pad to 6 elements
            components += [0, ''] * int((6-len(components))/2)
        # pad to 12 elements
        components += [0, ''] * int((12-len(components))/2)
        # log.debug(components)
        return components

    def sortReleases(self, paths):
        """
        Sort a list of paths by their release numbers. Assume that the
        paths end in a release number.

        Args:
            paths(list of str and/or tuple): Paths to sort

        Returns:
            str: Sorted list of release tags

        """
        releases = []
        for path in paths:
            if type(path) == tuple:
                release = os.path.split(os.path.normpath(path[0]))[1]
            else:
                release = os.path.split(os.path.normpath(path))[1]
            releases.append((self.normaliseRelease(release), path))

        sorted_releases = []
        for entry in sorted(releases):
            sorted_releases.append(entry[1])
        log.debug(sorted_releases)

        return sorted_releases

    def classifyArea(self, path):
        """
        Classify the area of a path, returning
        (area, work/prod/invalid, epicsVer).

        Args:
            path(str): Path to a module or area

        Returns:
            tuple: A tuple of <area>, <epics version> where <area> can be
            "work", "prod", or "invalid"

        """
        for a in self.areas:
            if path.startswith(self.devArea(a)):
                return a, "work", self.epicsVer()
            elif path.startswith(self.prodArea(a)):
                return a, "prod", self.epicsVer()

        # not found, so strip epicsVer out and try again
        match = self.epics_ver_re.search(path)
        if match and match.group() != self.epicsVer():
            return self.__class__(match.group()).classifyArea(path)
        else:
            return "invalid", "invalid", self.epicsVer()

    def getNameFromIni(self, ini):
        parser = SafeConfigParser()
        parser.read(ini)
        module = parser.get("general", "name")
        return module

    def classifyPath(self, path):
        """
        Return a (module, version) tuple for the path, where
        version is "invalid", "work", or a version number.

        Args:
            path(str): Path to a module or area

        Returns:
            tuple: A tuple of <module>, <version>

        """
        # classify the area
        area, domain, epics_ver = self.classifyArea(path)
        e = self
        module = None
        if epics_ver != self.epicsVer:
            e = self.__class__(epics_ver)
        if os.path.isfile(os.path.join(path, "etc", "module.ini")):
            # try and find name from etc/module.ini
            module = self.getNameFromIni(
                os.path.join(path, "etc", "module.ini"))
        elif os.path.isfile(os.path.join(path, "configure", "module.ini")):
            # try and find name from configure/module.ini
            module = self.getNameFromIni(
                os.path.join(path, "configure", "module.ini"))
        # deal with valid domains
        if domain == "work":
            root = e.devArea(area)
        elif domain == "prod":
            root = e.prodArea(area)
        else:
            root = ""
        assert path.startswith(root), \
            "'%s' should start with '%s'" % (path, root)
        sections = os.path.normpath(path[len(root):]).strip(os.sep).\
            split(os.sep)

        # strip off a prefix suffix
        if sections[-1] == "prefix" and area in ["python", "tools"]:
            sections = sections[:-1]

        # check they are the right length
        if domain == "work":
            if len(sections) == 1 or area in ["ioc", "tools", "python"] and \
                    len(sections) == 2:
                version = "work"
            else:
                version = "invalid"
        elif domain == "prod":
            if len(sections) == 2 or area in ["ioc", "tools", "python"] and \
                    len(sections) == 3:
                version = sections[-1]
                module = os.sep.join(sections[:-1])
                if area in ["tools", "python"]:
                    module = sections[-2]
            else:
                version = "invalid"
                sections = sections[:-1]
        else:
            version = "invalid"
        if module is None:
            if area == "ioc":
                module = os.sep.join(sections[-2:])
            elif len(sections) > 1:
                module = sections[-1]
        return module, version
