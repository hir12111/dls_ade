#!/bin/bash
# ******************************************************************************
#
# Script to build a Diamond production module for support, ioc or matlab areas
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
#

# Uncomment the following for tracing
# set -o xtrace

# don't let standard input block the script execution
exec 0</dev/null

# Set up DLS environment
DLS_EPICS_RELEASE=${_epics}
source /dls_sw/etc/profile
# Ensure CA Repeater is running (will close itself if already running)
EPICS_CA_SERVER_PORT=5064 EPICS_CA_REPEATER_PORT=5065 caRepeater &
EPICS_CA_SERVER_PORT=6064 EPICS_CA_REPEATER_PORT=6065 caRepeater &

OS_VERSION=RHEL$(lsb_release -sr | cut -d. -f1)-$(uname -m)
PYTHON=/dls_sw/prod/tools/${OS_VERSION}/Python3/3-7-2/prefix/bin/dls-python3
PIP=/dls_sw/prod/tools/${OS_VERSION}/Python3/3-7-2/prefix/bin/pip3
PYTHON_VERSION="python$($PYTHON -V | cut -d" " -f"2" | cut -d"." -f1-2)"

# Testing section, this will need correcting for the final version.
DLS_ADE_LOCATION=/dls_sw/work/python3/${OS_VERSION}/dls_ade
PFL_TO_VENV=${DLS_ADE_LOCATION}/prefix/bin/dls-pipfilelock-to-venv.py
export PYTHONPATH=${DLS_ADE_LOCATION}/prefix/lib/$PYTHON_VERSION/site-packages

WORK_DIST_DIR=/dls_sw/work/python3/${OS_VERSION}/distributions
PROD_DIST_DIR=/dls_sw/prod/python3/${OS_VERSION}/distributions

if  [[ "$build_dir" =~ "/prod/" ]] ; then
    is_test=false
else
    is_test=true
fi

# The same as the normalise_name function we use in Python.
function normalise_name() {
    name="$1"
    lower_name=${name,,}
    lower_dash_name=${lower_name//_/-}
    echo ${lower_dash_name}
}


distributions=()
normalised_module=$(normalise_name $_module)

# Check for existing release. Ignore if directory doesn't exist.
for released_module in $(ls "$_build_dir" 2> /dev/null); do
    normalised_released_module=$(normalise_name ${released_module})
    if [[ ${normalised_released_module} == ${normalised_module} ]]; then
        module_location="${_build_dir}/${released_module}"
        version_location="${module_location}/${_version}"
    fi
done

if [[ -d ${version_location} ]]; then
    if [[ ${_force} == true ]]; then
        SysLog info "Force: removing previous version: ${version_location}"
        rm -rf "${version_location}"
    else
        ReportFailure "${version_location} is already installed in prod"
    fi
else
    # Always install using the normalised name.
    version_location="${_build_dir}/${normalised_module}/${_version}"
fi

# First check if there is a matching distribution in prod.
for dist in $(ls "${PROD_DIST_DIR}"); do
    normalised_dist=$(normalise_name $dist)
    if [[ ${normalised_dist} == ${normalised_module}*${_version}* ]]; then
        distributions+=(${PROD_DIST_DIR}/${dist})
    fi
done

# If not, check if there is one in work.
if [[ ${#distributions[@]} -eq 0 ]]; then
    for dist in $(ls "${WORK_DIST_DIR}"); do
        normalised_dist=$(normalise_name $dist)

        if [[ ${normalised_dist} == ${normalised_module}*${_version}* ]]; then
            dist_file="${WORK_DIST_DIR}/${dist}"
            distributions+=(${dist_file})
            # If running on the build server, move file from work to prod.
            if [[ -w ${PROD_DIST_DIR} ]]; then
                mv "${dist_file}" "${PROD_DIST_DIR}" || ReportFailure "Cannot copy ${dist_file} to ${PROD_DIST_DIR}"
            fi
        fi
    done
fi

echo "Matching distributions ${distributions[@]}"

# Installation of dependency
if [[ ${#distributions[@]} -gt 0 ]]; then

    prefix_location="$version_location/prefix"
    site_packages_location="$prefix_location/lib/$PYTHON_VERSION/site-packages"
    specifier="$_module==$_version"

    ${PIP} install --ignore-installed --no-index --no-deps --find-links=$PROD_DIST_DIR --prefix=$prefix_location $specifier
    # If testing, fall back to installing from work.
    if [[ $? -ne 0 ]] && [[ ${is_test} == true ]]; then
        ${PIP} install --ignore-installed --no-index --no-deps --find-links=$WORK_DIST_DIR --prefix=$prefix_location $specifier
    fi
    # Check if there is Pipfile.lock to create venv
    if [[ -f $PROD_DIST_DIR/$_module-$_version.Pipfile.lock ]]; then
        pipfilelock=$_module-$_version.Pipfile.lock
        cd ${version_location}
        cp "$PROD_DIST_DIR/$pipfilelock" .
        "$PFL_TO_VENV" "$pipfilelock" || ReportFailure "Dependencies not installed."
        # Change header to the correct venv
        shebang='#!'
        new_header="${shebang}${version_location}/lightweight-venv/bin/python"
        for script in $(ls $prefix_location/bin); do
            sed -i "1 s|^.*$|$new_header|" $prefix_location/bin/$script
        done
    else
        echo "No Pipfile.lock is present"
    fi
else
    ReportFailure "No matching distribution was found for $_module-$_version"
fi
