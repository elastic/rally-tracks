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
RALLY_VARS_URL = "https://raw.githubusercontent.com/elastic/rally/master/.ci/variables.json"
PYENV_REGEX = .pyenv/shims
PY38 = $(shell curl -L -s $(RALLY_VARS_URL) | jq -r '.python_versions.PY38')
VIRTUAL_ENV ?= .venv
VENV_ACTIVATE_FILE = $(VIRTUAL_ENV)/bin/activate
VENV_ACTIVATE = . $(VENV_ACTIVATE_FILE)
VEPYTHON = $(VIRTUAL_ENV)/bin/python3
PYENV_ERROR = "\033[0;31mIMPORTANT\033[0m: Please install pyenv.\n"
PYENV_PATH_ERROR = "\033[0;31mIMPORTANT\033[0m: Please add $(HOME)/$(PYENV_REGEX) to your PATH env.\n"
PYENV_PREREQ_HELP = "\033[0;31mIMPORTANT\033[0m: please add \033[0;31meval \"\$$(pyenv init -)\"\033[0m to your bash profile and restart your terminal before proceeding any further.\n"
VE_MISSING_HELP = "\033[0;31mIMPORTANT\033[0m: Couldn't find $(PWD)/$(VIRTUAL_ENV); have you executed make venv-create?\033[0m\n"

prereq:
	pyenv install --skip-existing $(PY38)
	pyenv local $(PY38)
	@# Ensure all Python versions are registered for this project
	echo "$(PY38)" > .python-version
	-@ printf $(PYENV_PREREQ_HELP)

venv-create:
	@if [[ ! -x $$(command -v pyenv) ]]; then \
		printf $(PYENV_ERROR); \
		exit 1; \
	fi;
	@if [[ ! "$(PATH)" =~ $(PYENV_REGEX) ]]; then \
		printf $(PYENV_PATH_ERROR); \
		exit 1; \
	fi;
	@if [[ ! -f $(VENV_ACTIVATE_FILE) ]]; then \
		eval "$$(pyenv init -)" && python3 -mvenv $(VIRTUAL_ENV); \
		printf "Created python3 venv under $(PWD)/$(VIRTUAL_ENV).\n"; \
	fi;

check-venv:
	@if [[ ! -f $(VENV_ACTIVATE_FILE) ]]; then \
	printf $(VE_MISSING_HELP); \
	fi

install: venv-create
	. $(VENV_ACTIVATE_FILE); pip install --upgrade pip
	# install pytest for tests
	. $(VENV_ACTIVATE_FILE); pip3 install pytest==6.2.5 pytest-benchmark==3.2.2
	# install dependencies for tests
	. $(VENV_ACTIVATE_FILE); pip3 install geneve==0.3.0 pytest-asyncio==0.18.1 git+https://github.com/elastic/package-assets.git
	# install (latest) Rally for smoke tests
	. $(VENV_ACTIVATE_FILE); pip3 install git+ssh://git@github.com/elastic/rally.git --use-feature=2020-resolver

clean:
	rm -rf .pytest_cache

test: check-venv
	# PYTHONDONTWRITEBYTECODE=1 ensures that we always see warnings (not just the first time)
	. $(VENV_ACTIVATE_FILE); PYTHONDONTWRITEBYTECODE=1; pytest

it: check-venv
	. $(VENV_ACTIVATE_FILE); cd it; ./smoke-test.sh
	. $(VENV_ACTIVATE_FILE); cd it; ./query-test.sh

snapshot-it: check-venv
	. $(VENV_ACTIVATE_FILE); cd it; ./snapshot-test.sh $(snapshot_bucket)


.PHONY: clean test it prereq venv-create check-env snapshot-it
