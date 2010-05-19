#!/bin/env dls-python
# This script comes from the dls_scripts python module

usage = """%prog [options]

Create the etc directory for the support module or ioc. Must be run in the root
of the module.
This will create the following structure:
 ./
   etc/
     Makefile
     builder.py -- includes template builder objects for everything in ./db
     makeIocs/ -- this is where any examples or iocs are made
       Makefile
       example.xml -- this is an example ioc
     makeDocumentation/ -- this is where doxygen documentation is made
       Makefile
       config.src
       manual.src
       images/
     simulations/ -- this is where python simulations go
       Makefile
       myDevice_sim.py -- this is a simulation for a streamDevice template
     test/ -- this is where any test scripts go
    iocs/ -- This is where generated IOCs go
      Makefile
    documentation/ -- This is where the documentation goes
      index.html -- A redirect html page
"""
import os, sys, re, glob

def create_file(filename, text):
    print "Creating", filename
    open(filename, "w").write(text)

def create_dir(dirname):
    print "Creating directory", dirname
    os.mkdir(dirname)

def make_etc_dir():
    from optparse import OptionParser
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    if len(args) != 0:
        parser.error("Incorrect number of arguments.")

    # first check we are in the root of the module
    assert "configure" in os.listdir("."), \
        "This doesn't look like the root of a support or ioc module, doesn't have a configure directory"

    # First make the top level directory
    module = os.path.basename(os.path.abspath("."))
    create_dir("etc")
    create_file("etc/Makefile","""TOP = ..
include $(TOP)/configure/CONFIG
DIRS := $(DIRS) $(filter-out $(DIRS), $(wildcard makeIocs))
DIRS := $(DIRS) $(filter-out $(DIRS), $(wildcard makeDocumentation))
DIRS := $(DIRS) $(filter-out $(DIRS), $(wildcard simulations))
include $(TOP)/configure/RULES_DIRS
""")

    # now make builder files
    imports = []
    text = ""
    extext = '<?xml version="1.0" ?>\n<components arch="linux-x86">\n'
    if not os.path.isdir("db"):
        print "Making the module"
        os.system("make > /dev/null")
    all_protos = set()
    if os.path.isdir("db"):
        dbfiles = os.listdir("db")
        for dbf in dbfiles:
            print "Parsing", dbf
            filename = "db/"+dbf

            # get the template text
            ft = open(filename).read()
            basename = os.path.basename(filename)
            clsname = basename.split(".")[0]
            modname = os.path.basename(os.path.abspath("."))

            # find all protocol files
            protos = set(re.findall(r"@(.*\.proto[^ ]*)",ft))
            all_protos.update(protos)

            i = ["from iocbuilder import AutoSubstitution"]
            if protos:
                deps = "AutoSubstitution, AutoProtocol"
                i.append("from iocbuilder.modules.streamDevice import AutoProtocol")
            else:
                deps = "AutoSubstitution"
            text += "class %s(%s):\n" % (clsname, deps)
            text += "    # Substitution attributes\n"
            text += "    TemplateFile = '%s'\n"%basename
            text += "\n"
            if protos:
                text += "    # AutoProtocol attributes\n"
                text += "    ProtocolFiles = %s\n" % (list(protos).__repr__())
                text += "\n"
            text += "\n"
            l = "\t<%s.%s" % (modname, clsname)
            if protos:
                p = list(protos)[0].split(".")[0]
                extext += '\t<asyn.AsynIP name="%sAsyn" port="172.23.111.180:7001" simulation="localhost:9001"/>\n' %(clsname)
                l += ' PORT="%sAsyn"' % p
            extext += l + "/>\n"
            for imp in i:
                if imp not in imports:
                    imports.append(imp)
    create_file("etc/builder.py", "%s\n\n%s" % ("\n".join(imports), text))

    # now write the ioc makefile
    create_dir("etc/makeIocs")
    create_file("etc/makeIocs/Makefile", """TOP = ../..
include $(TOP)/configure/CONFIG

# this is the dls-xml-iocbuilder.py file
XMLBUILDER := dls-xml-iocbuilder.py

# set to -d to get debugging
DEBUG :=

# Create an IOC from all .xml files and all .py files
IOCS := $(patsubst %.xml, %, $(wildcard *.xml)) $(patsubst %.py, %, $(wildcard *.py))

# These are the IOCS we don't want to make simulations out of
NO_SIMS :=

# Make simulations from all IOCS not in NO_SIMS
SIMS := $(patsubst %, %_sim, $(filter-out $(NO_SIMS), $(IOCS)))

# These are the IOC dirs to make
IOC_DIRS := $(patsubst %, $(TOP)/iocs/%, $(IOCS) $(SIMS))

# Add the created iocs and sims to the install target
install: $(IOC_DIRS)

# General rule for building a Standard IOC from an XML file
$(TOP)/iocs/%: %.xml
\t$(XMLBUILDER) $(DEBUG) $<

# General rule for building a Simulation IOC from an XML file
$(TOP)/iocs/%_sim: %.xml
\t$(XMLBUILDER) $(DEBUG) --sim=linux-x86 $<

# Alternate rule for building a Standard IOC from a python file
$(TOP)/iocs/%: %.py
\t./$< $(DEBUG) $*

# Alternate rule for building a Simulation IOC from a python file
$(TOP)/iocs/%_sim: %.py
\t./$< $(DEBUG) --sim=linux-x86 $*

# Remove the generated iocs on clean
clean:
\trm -rf $(IOC_DIRS)
""")

    # and an example ioc
    create_file("etc/makeIocs/example.xml", extext + "</components>\n")
    create_file("etc/makeIocs/example_RELEASE", "# Place any example specific dependencies here\n")

    # create a simulations directory
    if all_protos:
        sims = [ x.split(".")[0] for x in all_protos ]
        create_dir("etc/simulations")
        create_file("etc/simulations/Makefile","""TOP = ../..
include $(TOP)/configure/CONFIG
%s
include $(TOP)/configure/RULES
""" % ("\n".join([ "DATA += %s_sim.py" % x for x in sims ])))
        for sim in sims:
            create_file("etc/simulations/%s_sim.py" % sim, """#!/dls_sw/tools/bin/python2.4

from pkg_resources import require
require("dls_serial_sim==1.7")

from dls_serial_sim import serial_device

class %s(serial_device):

    Terminator = "\\n"

    def __init__(self):
        # place your initialisation code here
        serial_device.__init__(self)

    def reply(self,command):
        # reply to commands here
        return command

if __name__=="__main__":
    # run our simulation on the command line. Run this file with -h for help
    CreateSimulation(%s)
    raw_input()
""" % (sim, sim))

    # now write the documentation template
    if not os.path.isdir("documentation"):
        create_dir("documentation")
    if not os.path.isfile("documentation/index.html"):
        create_file("documentation/index.html", """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
<head>
<title>Documentation</title>
<!-- This tag redirects to the doxygen index -->
<meta http-equiv="REFRESH" content="0;url=doxygen/index.html"></HEAD>
<body/>
</html>""")

    create_dir("etc/makeDocumentation")
    create_dir("etc/makeDocumentation/images")
    create_file("etc/makeDocumentation/Makefile", """TOP = ../..
include $(TOP)/configure/CONFIG

# set to -d to get debugging
DEBUG :=

# this is the doxygen output dir
DOCDIR := $(TOP)/documentation/doxygen

# add the documentation files to the install target
install: $(DOCDIR)

# rule for creating the doxygen documentation
$(DOCDIR): config.src manual.src $(DOCDIR)/build_instructions_example
\tmkdir -p $(DOCDIR)
\tdls-make-doxygen-documentation.py -o $(DOCDIR) config.src manual.src

# rule for generating build instructions from an xml file
$(DOCDIR)/build_instructions_%: $(TOP)/etc/makeIocs/%.xml
\tmkdir -p $(DOCDIR)
\tdls-xml-iocbuilder.py --doc=$@ $(DEBUG) $^

# rule for generating build instructions from a py file
$(DOCDIR)/build_instructions_%: $(TOP)/etc/makeIocs/%.py
\tmkdir -p $(DOCDIR)
\t$^ --doc=$@ $(DEBUG) example

# Remove entire documentation/doxygen dir on clean
clean:
\trm -rf $(DOCDIR)
""")
    create_file("etc/makeDocumentation/config.src", "# Include override doxygen config values here\n")
    vdbs = glob.glob("*App/Db/*.vdb") + glob.glob("*App/Db/*.db") + glob.glob("*App/Db/*.template")
    if vdbs:
        vdb = vdbs[0]
    else:
        vdb = "thing.vdb"
    create_file("etc/makeDocumentation/manual.src", r"""/**
\mainpage %s EPICS Support Module
\section intro_sec Introduction
I'm going to describe the module here, possibly with a <a href="http://www.google.co.uk">web link to the manufacturers webpage</a>. \n
You can also link to \ref %s "internally generated documentation" with alternate text, or by just by mentioning its name, e.g. %s

\section bugs_sec Known Bugs
- I'm going to describe any known bugs here

\section user_sec User Manual
The \subpage user_manual page contains instructions for the end user

\section build_sec Build Instructions 
- \subpage build_instructions_example

IOCs build using these build instructions are available in iocs/
**/

/* Build instructions page will be generated from the xml file given to dls-xml-iocbuilder.py --doc */

/**
\page user_manual User Manual
This needs to be hand generated. You can link directly to this page from the edm screen if you want
**/
""" % (module, vdb, vdb))
    # make the test directory
    create_dir("etc/test")
    # then the iocs directory
    if not os.path.isdir("iocs"):
        create_dir("iocs")
        create_file("iocs/Makefile", """TOP = ..
include $(TOP)/configure/CONFIG
DIRS := $(DIRS) $(filter-out Makefile, $(wildcard *))
include $(TOP)/configure/RULES_DIRS
""")
    # finally add it to the makefile
    mtext = open("Makefile").read()
    line = "DIRS := $(DIRS) $(filter-out $(DIRS), $(wildcard etc))\n"
    if line not in mtext:
        print "Adding etc and iocs dirs to Makefile"
        iline =  "# Comment out the following line to creation of example iocs and documentation\n"
        iline += line
        iline += "# Comment out the following line to disable building of example iocs\n"
        iline += "DIRS := $(DIRS) $(filter-out $(DIRS), $(wildcard iocs))\n"
        srch = "include $(TOP)/configure/RULES_TOP"
        open("Makefile", "w").write(mtext.replace(srch, iline + srch))
    print "*** Incomplete example.xml created, run xeb etc/makeIocs/example.xml to fix"
if __name__=="__main__":
    sys.exit(make_etc_dir())
