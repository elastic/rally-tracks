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

SHELL := /bin/bash

VIRTUAL_ENV := $(or $(VIRTUAL_ENV),.venv$(if $(PY_VERSION),-$(PY_VERSION)))
VENV_ACTIVATE_FILE := $(VIRTUAL_ENV)/bin/activate
VENV_ACTIVATE := source $(VENV_ACTIVATE_FILE)

PY_VERSION ?= 3.13.7
export UV_PYTHON := $(PY_VERSION)
export UV_PROJECT_ENVIRONMENT := $(VIRTUAL_ENV)

.PHONY: \
	uv \
	uv-add \
	uv-lock \
	venv \
	clean-venv \
	install \
	reinstall \
	lint \
	format \
	precommit \
	pre-commit \
	test \
	test-3.10 \
	test-3.11 \
	test-3.12 \
	test-3.13 \
	it \
	it-serverless \
	it_serverless \
	sdist \
	clean \
	shell \
	sh

uv:
	@if [[ ! -x $$(command -v uv) ]]; then \
		printf "Please install uv: https://docs.astral.sh/uv/getting-started/installation/\n"; \
		exit 1; \
	fi

uv-add:
ifndef ARGS
	$(error Missing arguments. Use make uv-add ARGS="...")
endif
	uv add $(ARGS)

uv-lock:
	uv lock

venv: uv $(VENV_ACTIVATE_FILE)
	uv sync --locked --group develop --group unit

$(VENV_ACTIVATE_FILE):
	uv venv --allow-existing --seed

clean-venv:
	rm -rf '$(VIRTUAL_ENV)'

install: venv
	uv sync --locked --group develop --group unit

reinstall: clean-venv
	$(MAKE) venv

lint: venv
	uv run --locked --group develop -- pre-commit run --all-files

format: lint

precommit pre-commit: venv
	uv run --locked --group develop -- pre-commit run

test: venv
	uv run --locked --group unit -- pytest $(ARGS)

test-3.10:
	$(MAKE) test PY_VERSION=3.10

test-3.11:
	$(MAKE) test PY_VERSION=3.11

test-3.12:
	$(MAKE) test PY_VERSION=3.12

test-3.13:
	$(MAKE) test PY_VERSION=3.13

it: venv
	uv run --locked --group it -- pytest it_tracks --log-cli-level=INFO $(ARGS)

it-serverless it_serverless: venv
	uv run --locked --group it-serverless -- pytest -s it_tracks_serverless --log-cli-level=INFO $(ARGS)

sdist: venv
	uv build --sdist

clean:
	rm -rf .pytest_cache build dist rally_tracks.egg-info

shell sh: venv
	$(VENV_ACTIVATE); $(SHELL)
