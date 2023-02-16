# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

SHELL = /bin/bash
# We assume an active virtualenv for development
PYENV_REGEX = .pyenv/shims
PY_BIN = python3
# https://github.com/pypa/pip/issues/5599
PIP_WRAPPER = $(PY_BIN) -m pip
export PY38 = "3.8.13"
VIRTUAL_ENV ?= .venv
VENV_ACTIVATE_FILE = $(VIRTUAL_ENV)/bin/activate
VENV_ACTIVATE = . $(VENV_ACTIVATE_FILE)
VEPYTHON = $(VIRTUAL_ENV)/bin/$(PY_BIN)
PYENV_ERROR = "\033[0;31mIMPORTANT\033[0m: Please install pyenv.\n"
PYENV_PREREQ_HELP = "\033[0;31mIMPORTANT\033[0m: please type \033[0;31mpyenv init\033[0m, follow the instructions there and restart your terminal before proceeding any further.\n"
VE_MISSING_HELP = "\033[0;31mIMPORTANT\033[0m: Couldn't find $(PWD)/$(VIRTUAL_ENV); have you executed make venv-create?\033[0m\n"

prereq:
	pyenv install --skip-existing $(PY38)
	pyenv local $(PY38)

venv-create:
	@if [[ ! -x $$(command -v pyenv) ]]; then \
		printf $(PYENV_ERROR); \
		exit 1; \
	fi;
	@if [[ ! -f $(VENV_ACTIVATE_FILE) ]]; then \
		eval "$$(pyenv init -)" && eval "$$(pyenv init --path)" && $(PY_BIN) -mvenv $(VIRTUAL_ENV); \
		printf "Created python3 venv under $(PWD)/$(VIRTUAL_ENV).\n"; \
	fi;

check-venv:
	@if [[ ! -f $(VENV_ACTIVATE_FILE) ]]; then \
	printf $(VE_MISSING_HELP); \
	fi

install: venv-create
	. $(VENV_ACTIVATE_FILE); $(PIP_WRAPPER) install .[develop]

shell: check-venv
	. $(VENV_ACTIVATE_FILE); hatch -v shell

test: check-venv
	. $(VENV_ACTIVATE_FILE); hatch -v -e unit run test

it: check-venv
	. $(VENV_ACTIVATE_FILE); hatch -v -e it run test

sdist: check-venv
	. $(VENV_ACTIVATE_FILE); hatch -v build -t sdist -c

precommit: check-venv
	@. $(VENV_ACTIVATE_FILE); pre-commit run --all-files

clean:
	rm -rf .pytest_cache
	. $(VENV_ACTIVATE_FILE); hatch -v clean

.PHONY: prereq venv-create check-venv install shell test it sdist clean
