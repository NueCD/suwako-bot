#!/bin/bash

# Check python version
PVERSION=$(python -c "import sys; print(sys.version_info[0])")
PYTHON='python'

if ! [[ $PVERSION = '3' ]]; then
	if [[ $PVERSION = '2' ]]; then
		if [[ $(command -v python3) ]]; then
			PYTHON='python3'
		elif [[ $(command -v python3.6) ]]; then
			PYTHON='python3.6'
		else
			echo 'Python 3 is not installed.'
		fi
	fi
fi

if [[ $* = *'-h'* || $* = *'--help'* ]]; then
	echo "Usage: $(tput bold)run.sh$(tput sgr0) [-v|--virtualenv] [--setup]"
	echo "    $(tput bold)-v, --virtualenv$(tput sgr0) Run bot inside virtualenvironment."
	echo "             $(tput bold)--setup$(tput sgr0) Install dependencies."
	echo "          $(tput bold)-h, --help$(tput sgr0) Show this message."
	exit
fi

if [[ $* = *'-v'* || $* = *'--virtualenv'* ]]; then
	# Check if virtualenv is installed
	if ! [[ $(command -v virtualenv) ]]; then
		echo 'Virtualenv is not installed. Exiting...'
		exit
	fi
	
	# Prepare virtualenv
	if [[ $* = *'--setup'* ]]; then
		virtualenv .
		source bin/activate
		pip3.6 install -r requirements.txt
		deactivate
		echo 'Virtualenv is done.'
		exit
	fi
	
	# Run virtualenv
	if ! [[ -f "bin/activate" ]]; then
		echo 'Virtualenv is not set up. Run "suwkao.sh -v --setup" to set up.'
		exit
	fi
	source bin/activate

elif [[ $* = *'--setup'* ]]; then
	if ! [[ $(command -v pip) ]]; then
		echo 'Pip is not installed. Exiting...'
		exit
	fi
	
	pip install -r requirements.txt
fi

eval $PYTHON suwako.py
