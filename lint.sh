#!/bin/bash

COLOR_GREEN='\e[0;32m'
COLOR_RED='\e[0;31m'
NO_COLOR='\e[0;0m'

echo -e "${COLOR_GREEN}Isort linting...${NO_COLOR}"
isort --check --diff --color $1
isort_result=$?
echo

echo -e "${COLOR_GREEN}Flake8 linting...${NO_COLOR}"
flake8 -v --color always $1
flake8_result=$?
echo

echo -e "${COLOR_GREEN}MyPy linting...${NO_COLOR}"
mypy --color-output $1
mypy_result=$?
echo

if [[ isort_result -eq 0 && flake8_result -eq 0 && mypy_result -eq 0 ]]; then
    echo -e "${COLOR_GREEN}OK${NO_COLOR}"
    exit 0
else
    echo -e "${COLOR_RED}Fail${NO_COLOR}"
    exit 1
fi
