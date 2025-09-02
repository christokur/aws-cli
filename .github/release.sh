#!/usr/bin/env bash

export GITHUB_WORKSPACE=${GITHUB_WORKSPACE:-$PWD}

rm -fr build dist
python scripts/ci/install
pip install wheel twine

[ type setup_netrc_from_pipconffile 2>/dev/null ] || . $GITHUB_WORKSPACE/cicd/rc/configure_aws_codeartifact.rc
setup_netrc_from_pipconffile

cat ~/.pypirc
twine upload --repository gitlab dist/* --verbose
