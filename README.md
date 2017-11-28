[![Build Status](https://travis-ci.org/dls-controls/dls_ade.svg)](https://travis-ci.org/dls-controls/dls_ade)
[![Coverage Status](https://coveralls.io/repos/github/dls-controls/dls_ade/badge.svg?branch=master)](https://coveralls.io/github/dls-controls/dls_ade?branch=master)
[![Code Health](https://landscape.io/github/dls-controls/dls_ade/master/landscape.svg?style=flat)](https://landscape.io/github/dls-controls/dls_ade/master)

# DLS Application Development Environment (ADE)

A collection of scripts used in the DLS Controls Group Application Development Environment.

## Development Environment

Setup a virtualenv in the root of the project and install the dependencies:

```
  virtualenv -p /path/to/your/python2.7 venv
  source venv/bin/activate
  pip install -r requirements.txt
  pip install sphinx nose
  
  # Build an egg for distribution
  python setup.py bdist_egg
  
  # Build the docs with sphinx
  python setup.py build_sphinx
  
  # Run the unittests with nose
  nosetests
```
