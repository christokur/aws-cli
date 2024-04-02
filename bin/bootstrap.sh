#!/usr/bin/env bash

in_venv=-1
[ -z "$0" ] && ROOT_DIR=${ROOT_DIR:-.} || ROOT_DIR=${ROOT_DIR:-$(dirname $(dirname $(realpath $0)))}

PYENV_DIR=${PYENV_DIR:-''}
if test -d ~/.pyenv/bin ; then
    PYENV_DIR=~/.pyenv
else
  if test -d /usr/local/pyenv/bin ; then
      PYENV_DIR=/usr/local/pyenv
  else
    for pyenv_path in $(ls -ad /usr/local/Cellar/pyenv/*/bin /opt/local/Cellar/pyenv/*/bin /opt/homebrew/Cellar/pyenv/*/bin 2>/dev/null) ; do
      if test -d $pyenv_path ; then
          PYENV_DIR=$(dirname $(dirname $pyenv_path))
      fi
    done
  fi
fi

if [ ! -z "$PYENV_DIR" ] ; then
  echo "You have pyenv."
  eval "$(pyenv init --path)"
  eval "$(pyenv init -)"
  eval "$(pyenv virtualenv-init -)"
  . deactivate 2>/dev/null || true
  [ -f $ROOT_DIR/.python-version ] && pyenv activate $(cat $ROOT_DIR/.python-version) || pyenv activate
  in_venv=1
fi

if [ -z "${VIRTUAL_ENV}" -a $in_venv -le 0 ]; then
  in_venv=0
  ts=$(date +%s)
  #echo $ts

  edir=~/.venv/$ts
  echo "Creating virtual environment at $edir"

  mkdir -p $edir
  virtualenv $edir
  source $edir/bin/activate
else
  echo "You are in a virtual environment. Good."
fi

RC=0
pip install poetry || RC=$?
. $ROOT_DIR/bin/poetry-2-codeartifact.sh || true
[ $RC -eq 0 ] || { pip install poetry || true; . $ROOT_DIR/bin/poetry-2-codeartifact.sh || true; }
export INIT_WITH_POETRY="yes"
poetry install
poe deps

if [[ $in_venv -eq 0 ]]; then
  echo "RUN these commands next to enter virtual environment:"
  echo "export INIT_WITH_POETRY=\"yes\""
  echo "source $VIRTUAL_ENV/bin/activate"
fi
