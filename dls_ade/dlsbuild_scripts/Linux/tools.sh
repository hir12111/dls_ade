#!/bin/bash

# ******************************************************************************
#
# Script to build a Diamond tools module.
#
# This is a partial script which builds a module in for the dls-release system.
# The script is prepended with a list of variables before invocation by the
# dls-release mechanism. These variables are:
#
#   _email     : The email address of the user who initiated the build
#   _user      : The username (fed ID) of the user who initiated the build
#   _epics     : The DLS_EPICS_RELEASE to use
#   _build_dir : The parent directory in the file system in which to build the
#                module. This does not include module or version directories.
#   _git_dir   : The Git URL to clone
#   _module    : The module name
#   _version   : The module version
#   _area      : The build area
#   _force     : Force the build (i.e. rebuild even if already exists)
#   _build_name: The base name to use for log files etc.

# don't let standard input block the script execution
exec 0</dev/null

# Set up environment
DLS_EPICS_RELEASE=${_epics}
source /dls_sw/etc/profile

work_tar_dir=/dls_sw/work/targetOS/tar-files
prod_tar_dir=/dls_sw/prod/targetOS/tar-files
if [ ! -z "$(ls $work_tar_dir/)" -a -w $prod_tar_dir ]; then
    mv $work_tar_dir/* $prod_tar_dir || ReportFailure "Can not move tar files"
fi

# Ensure there is a architecture dependent build directory available
OS_VERSION=$(lsb_release -sr | cut -d. -f1)  # e.g. 7
RHEL=RHEL${OS_VERSION}-$(uname -m)  # e.g. RHEL7-x86_64

TOOLS_BUILD=/dls_sw/prod/etc/build/tools_build
TOOLS_ROOT=/dls_sw/prod/tools/$RHEL
build_dir=$_build_dir

mkdir -p $build_dir/${_module} || ReportFailure "Can not mkdir $build_dir/${_module}"
cd $build_dir/${_module} || ReportFailure "Can not cd to $build_dir/${_module}"
export is_test=true # if is_test - can clone the entire repository; may be requesting an SHA hash

if  [[ "$_build_dir" =~ "/prod/" ]] ; then
    is_test=false
fi

SysLog debug "version dir: " ${PWD}/$_version

# If force, remove existing version directory (whether or not it exists)
if [ "$_force" == "true" ]; then
    SysLog info "Force: removing previous version: " ${PWD}/$_version
    rm -rf $_version || ReportFailure "Can not rm $_version"
fi

if [ ! -d $_version ]; then
    CloneRepo
elif (( $(git status -uno --porcelain | grep -Ev "M.*configure/RELEASE$" | wc -l) != 0)) ; then
    ReportFailure "Directory $build_dir/$_version not up to date with $_git_dir"
fi

# Add the ROOT definition to the RELEASE file
release_file="$_version"/configure/RELEASE

# The following is for short term compatibility purposes
[ ! -f "$release_file" ] && release_file="$_version"/RELEASE

if [ -f "$release_file" ] ; then
    if (( ! $(grep -c '^( *ROOT| *TOOLS_SUPPORT)' "$release_file") )) ; then
        sed -i "1i\
TOOLS_SUPPORT=$TOOLS_ROOT" "$release_file"
    else
        sed -i \
            -e 's,^ *ROOT *=.*$,ROOT='"$TOOLS_ROOT," \
            -e 's,^ *TOOLS_SUPPORT *=.*$,TOOLS_SUPPORT='"$TOOLS_ROOT," \
            "$release_file"
    fi
fi

# Build
SysLog info "Starting build. Build log: ${PWD}/${_version}/${_build_name}.log"
build_program_log=${PWD}/${_version}/build_program_${_build_name}.log
$TOOLS_BUILD/build_program -n $_build_name ${_version} > ${build_program_log} 2>&1 \
  || ReportFailure "Build aborted. Failed command: build_program -n ${_build_name} ${_version} " $(cat ${build_program_log})

if (( $(cat ${_version}/${_build_name}.sta) != 0 )) ; then
    ReportFailure ${PWD}/${_version}/${_build_name}.log
fi

SysLog info "make-defaults: $build_dir $TOOLS_BUILD/RELEASE.$RHEL $OS_VERSION $(uname -m)"
$TOOLS_BUILD/make-defaults $build_dir $TOOLS_BUILD/RELEASE.$RHEL $OS_VERSION $(uname -m)

SysLog info "Build complete"
