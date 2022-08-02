#!/bin/bash
# At $HOME directory of wasian tools on toolforge server: https://toolsadmin.wikimedia.org/tools/id/wasian

# define paths
export PROJECT_PATH=$HOME/wasian
export SCRIPT_PATH=$HOME/wasian/wasian/sparqlwrapper/surname

# define script name
export SCRIPT_NAME=import_papers_from_ads.py

# cd to project path
cd $PROJECT_PATH

# create the venv
make virtualenv

# activate it
source .venv/bin/activate

# install the project
make install

# cd to script path
cd $SCRIPT_PATH

# run script
$PROJECT_PATH/.venv/bin/python3 $SCRIPT_NAME