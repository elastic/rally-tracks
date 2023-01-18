#!/usr/bin/env bash

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

# This test is designed to test that all queries, which should have hits, do. This relies on assertions and the undocumented
# parameter 'detailed_results'

# fail this script immediately if any command fails with a non-zero exit code
set -e
# Treat unset env variables as an error
set -u
# fail on pipeline errors, e.g. when grepping
set -o pipefail

readonly RACE_ID=$(uuidgen)
readonly ES_VERSION=${ES_VERSION:-7.17.1}

INSTALL_ID=-1

export THESPLOG_FILE="${THESPLOG_FILE:-${HOME}/.rally/logs/actor-system-internal.log}"
# this value is in bytes, the default is 50kB. We increase it to 200kiB.
export THESPLOG_FILE_MAXSIZE=${THESPLOG_FILE_MAXSIZE:-204800}
# adjust the default log level from WARNING
export THESPLOG_THRESHOLD="DEBUG"

function log {
    local ts=$(date -u "+%Y-%m-%dT%H:%M:%SZ")
    echo "[${ts}] [${1}] ${2}"
}

function info {
    log "INFO" "${1}"
}

function set_up {
  info "preparing cluster"
  INSTALL_ID=$(esrally install --quiet --distribution-version="${ES_VERSION}" --car="defaults,basic-license" --runtime-jdk="bundled" --node-name="rally-node-0" --network-host="127.0.0.1" --http-port=39200 --master-nodes="rally-node-0" --seed-hosts="127.0.0.1:39300" | jq --raw-output '.["installation-id"]')
  esrally start --installation-id="${INSTALL_ID}" --race-id="${RACE_ID}" --runtime-jdk="bundled"
}

function run_test {
  echo "**************************************** Race Id - ${RACE_ID} ****************************************************************************"
  echo "**************************************** TESTING QUERIES *********************************************************************************"

  echo "**************************************** Indexing kafka data for later queries using ${ES_VERSION} ***************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing" --track-path="${PWD}/../logs" --track-params="./query-tests/kafka.json" --on-error=abort
  echo "**************************************** TESTING kafka queries using ${ES_VERSION} assertions ********************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --enable-assertions --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-querying" --exclude-tasks="tag:setup" --track-path="${PWD}/../logs" --track-params='./query-tests/kafka.json' --on-error=abort
  echo "**************************************** TESTING kafka queries using ${ES_VERSION}, query_average_interval and with no query cache ****************************"
  # minimum interval is 15 minutes, so the configured average interval gets overridden and assertions should pass
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --enable-assertions --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-querying" --exclude-tasks="tag:setup" --track-path="${PWD}/../logs" --track-params='./query-tests/query-avg-interval.json' --on-error=abort

  echo "**************************************** Indexing apache data for later queries using ${ES_VERSION} **************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing" --track-path="${PWD}/../logs" --track-params="./query-tests/apache.json" --on-error=abort
  echo "**************************************** TESTING apache queries using ${ES_VERSION} assertions *******************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --enable-assertions --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-querying" --exclude-tasks="tag:setup" --track-path="${PWD}/../logs" --track-params='./query-tests/apache.json' --on-error=abort
  echo "**************************************** TESTING apache queries using ${ES_VERSION} and query_max_date_start *****************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --enable-assertions --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-querying" --exclude-tasks="tag:setup" --track-path="${PWD}/../logs" --track-params='./query-tests/query-moving-window.json' --on-error=abort

  echo "**************************************** Indexing nginx data for later queries using ${ES_VERSION} ***************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing" --track-path="${PWD}/../logs" --track-params="./query-tests/nginx.json" --on-error=abort
  echo "**************************************** TESTING nginx queries using ${ES_VERSION} assertions ********************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --enable-assertions --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-querying" --exclude-tasks="tag:setup" --track-path="${PWD}/../logs" --track-params='./query-tests/nginx.json' --on-error=abort
  echo "**************************************** TESTING nginx concurrent query and indexing using ${ES_VERSION}***********************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --enable-assertions --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing-querying" --exclude-tasks="tag:setup" --track-path="${PWD}/../logs"  --track-params='./query-tests/nginx-concurrent.json' --on-error=abort

  echo "**************************************** Indexing application data for later discover queries using ${ES_VERSION} ***************************************"

  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing" --track-path="${PWD}/../logs" --track-params="./query-tests/discover.json" --on-error=abort
  echo "**************************************** TESTING discover queries using ${ES_VERSION} assertions ********************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --enable-assertions --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-querying" --exclude-tasks="tag:setup" --track-path="${PWD}/../logs" --track-params='./query-tests/discover.json' --on-error=abort
  echo "**************************************** TESTING discover concurrent query and indexing using ${ES_VERSION}***********************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --enable-assertions --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing-querying" --exclude-tasks="tag:setup" --track-path="${PWD}/../logs"  --track-params='./query-tests/discover.json' --on-error=abort

  echo "**************************************** Indexing mysql data for later queries using ${ES_VERSION} **************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing" --track-path="${PWD}/../logs" --track-params="./query-tests/mysql.json" --on-error=abort
  echo "**************************************** TESTING mysql queries using ${ES_VERSION} assertions *******************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --client-options="timeout:180" --enable-assertions --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-querying" --exclude-tasks="tag:setup" --track-path="${PWD}/../logs" --track-params='./query-tests/mysql.json' --on-error=abort

}

function tear_down {
    info "tearing down"
    set +e
    esrally stop --installation-id="${INSTALL_ID}"
    set -e
}

function main {
    set_up
    run_test
}

trap "tear_down" EXIT

main
