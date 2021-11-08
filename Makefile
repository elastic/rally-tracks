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
RALLY_SUBMODULE = rally
VENV_ACTIVATE_FILE = $(RALLY_SUBMODULE)/.venv/bin/activate
VENV_ACTIVATE = . $(VENV_ACTIVATE)
export TRACK_DIRS = $(shell find -E . -regex ".*/track\.json"|sed -r 's|/[^/]+$$||' | sort -u)
# Compatible distribution for this branch
IT_DISTRIBUTION = 7.15.1

checkout-rally:
	@if [[ ! -d $(RALLY_SUBMODULE) ]]; then \
	printf "Initializing Rally submodule...\n"; \
    git submodule update --init; \
	fi

init-venv: checkout-rally
	@if [[ ! -f $(VENV_ACTIVATE_FILE) ]]; then \
	printf "Initializing virtual environment for Rally submodule...\n"; \
    cd rally && make venv-create; \
	fi

# keep development dependencies in sync with Rally
install: init-venv
	cd rally && make install

lint: install
	@. $(VENV_ACTIVATE_FILE); find $(TRACK_DIRS) -name "*.py" -exec pylint -j0 -rn --rcfile=$(CURDIR)/.pylintrc \{\} +
	@. $(VENV_ACTIVATE_FILE); black --config=black.toml --check **
	@. $(VENV_ACTIVATE_FILE); isort --check **

format: install
	@. $(VENV_ACTIVATE_FILE); black --config=black.toml **
	@. $(VENV_ACTIVATE_FILE); isort **

precommit: lint

it: install
	. $(VENV_ACTIVATE_FILE); \
    for track_path in $(TRACK_DIRS); \
        do esrally race --track-path="$$track_path" --test-mode --kill-running-processes --distribution-version=$(IT_DISTRIBUTION) \
        || exit 1;\
	done

.PHONY: init-venv install lint format precommit it