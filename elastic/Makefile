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
ROOT_DIR := $(abspath ..)
PY_VERSION ?= 3.13
VIRTUAL_ENV ?= $(ROOT_DIR)/.venv-$(PY_VERSION)
VENV_ACTIVATE_FILE := $(VIRTUAL_ENV)/bin/activate
VENV_ACTIVATE := source $(VENV_ACTIVATE_FILE)

venv install:
	$(MAKE) -C $(ROOT_DIR) install PY_VERSION=$(PY_VERSION) VIRTUAL_ENV=$(VIRTUAL_ENV)

clean:
	rm -rf .pytest_cache
	$(MAKE) -C $(ROOT_DIR) clean

lint:
	$(MAKE) -C $(ROOT_DIR) lint PY_VERSION=$(PY_VERSION) VIRTUAL_ENV=$(VIRTUAL_ENV)

format:
	$(MAKE) -C $(ROOT_DIR) format PY_VERSION=$(PY_VERSION) VIRTUAL_ENV=$(VIRTUAL_ENV)

test: venv
	$(MAKE) -C $(ROOT_DIR) test PY_VERSION=$(PY_VERSION) VIRTUAL_ENV=$(VIRTUAL_ENV) ARGS=elastic/tests

it: venv
	$(VENV_ACTIVATE); cd it; ./smoke-test.sh
	$(VENV_ACTIVATE); cd it; ./query-test.sh

snapshot-it: venv
	$(VENV_ACTIVATE); cd it; ./snapshot-test.sh $(snapshot_bucket)

.PHONY: clean format install it lint snapshot-it test venv
