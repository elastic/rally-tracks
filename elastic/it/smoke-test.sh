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
  INSTALL_ID=$(esrally install --quiet --distribution-version="${ES_VERSION}" --car="defaults,basic-license" --runtime-jdk="bundled" --node-name="rally-node-0" --network-host="127.0.0.1" --http-port=39200 --master-nodes="rally-node-0" --seed-hosts="127.0.0.1:39300" | jq --raw-output '.["installation-id"]')
  esrally start --installation-id="${INSTALL_ID}" --race-id="${RACE_ID}" --runtime-jdk="bundled"
}

function run_test {
  echo "**************************************** Race Id - ${RACE_ID} *************************************************"

  echo "======================================== BEGIN LOGS =========================================================="
  echo "**************************************** TESTING LIST TRACKS***************************************************"
  esrally list tracks --track-path="${PWD}/../logs"
  echo "**************************************** TESTING INFO *********************************************************"
  esrally info --track-path="${PWD}/../logs"
  echo "**************************************** TESTING DEFAULT CHALLENGE ********************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --track-path="${PWD}/../logs" --on-error=abort --track-params="number_of_replicas:0"
  # deliberately limit each test to 2m so any throttled tests dont take forever. We ask for 72GB per day (0.1gb in 2 mins)
  # this 0.1GB will expand due to raw-json expansion by around 10x
  echo "**************************************** TESTING logging-disk-usage using ${ES_VERSION} *******************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-disk-usage" --track-path="${PWD}/../logs" --track-params="start_date:2021-01-01T00-00-00Z,end_date:2021-01-01T00-00-02Z,max_total_download_gb:18,raw_data_volume_per_day:72GB,max_generated_corpus_size:1GB,wait_for_status:green,force_data_generation:true,number_of_shards:4,number_of_replicas:0" --on-error=abort
  echo "**************************************** TESTING logging-indexing un-throttled using ${ES_VERSION} ********************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing" --track-path="${PWD}/../logs" --track-params="start_date:2021-01-01T00-00-00Z,end_date:2021-01-01T00-00-02Z,max_total_download_gb:18,raw_data_volume_per_day:72GB,max_generated_corpus_size:1GB,wait_for_status:green,force_data_generation:true,number_of_shards:2,number_of_replicas:0" --on-error=abort
  echo "**************************************** TESTING logging-querying using ${ES_VERSION}*********************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-querying" --track-path="${PWD}/../logs" --exclude-tasks="tag:setup" --track-params="start_date:2021-01-01T00-00-00Z,end_date:2021-01-01T00-00-02Z,max_total_download_gb:18,raw_data_volume_per_day:72GB,max_generated_corpus_size:1GB,wait_for_status:green,force_data_generation:true,query_warmup_time_period:60,query_time_period:120,number_of_shards:2,number_of_replicas:0" --on-error=abort
  echo "**************************************** TESTING logging-indexing-querying un-throttled using ${ES_VERSION}************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing-querying" --track-path="${PWD}/../logs" --exclude-tasks="tag:setup" --track-params="start_date:2021-01-01T00-00-02Z,end_date:2021-01-01T00-00-04Z,max_total_download_gb:18,raw_data_volume_per_day:72GB,max_generated_corpus_size:1GB,wait_for_status:green,force_data_generation:true,query_warmup_time_period:60,number_of_shards:2,number_of_replicas:0" --on-error=abort
  echo "**************************************** TESTING logging-indexing throttled using ${ES_VERSION}***********************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing" --track-path="${PWD}/../logs" --exclude-tasks="tag:setup" --track-params="throttle_indexing:true,start_date:2021-01-01T00-00-04Z,end_date:2021-01-01T00-00-06Z,max_total_download_gb:18,raw_data_volume_per_day:72GB,max_generated_corpus_size:1GB,wait_for_status:green,force_data_generation:true,number_of_shards:2,number_of_replicas:0" --on-error=abort
  echo "**************************************** TESTING logging-indexing-querying throttled using ${ES_VERSION}***************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing-querying" --exclude-tasks="tag:setup" --track-path="${PWD}/../logs" --track-params="throttle_indexing:true,start_date:2021-01-01T00-00-06Z,end_date:2021-01-01T00-00-08Z,max_total_download_gb:18,raw_data_volume_per_day:72GB,max_generated_corpus_size:1GB,wait_for_status:green,force_data_generation:true,query_warmup_time_period:60,number_of_shards:2,number_of_replicas:0" --on-error=abort
  # testing undocumented features activated through the use of bulk_start_date and bulk_end_date
  echo "**************************************** TESTING logging-querying - with pre-loaded data (undocumented) using ${ES_VERSION}*******"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-querying" --track-path="${PWD}/../logs" --track-params="bulk_start_date:2020-09-30T00-00-00Z,bulk_end_date:2020-09-30T00-00-02Z,start_date:2020-09-30T00-00-00Z,end_date:2020-09-30T00-00-02Z,max_total_download_gb:18,raw_data_volume_per_day:72GB,max_generated_corpus_size:1GB,wait_for_status:green,force_data_generation:true,query_warmup_time_period:60,query_time_period:120,number_of_shards:2,number_of_replicas:0" --on-error=abort
  echo "**************************************** TESTING logging-indexing-querying throttled - with pre-loaded data (undocumented) using ${ES_VERSION}*******"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing-querying"  --track-path="${PWD}/../logs" --track-params="throttle_indexing:true,bulk_start_date:2020-09-30T00-00-00Z,bulk_end_date:2020-09-30T00-00-02Z,start_date:2020-09-30T00-00-00Z,end_date:2020-09-30T00-00-02Z,max_total_download_gb:18,raw_data_volume_per_day:72GB,max_generated_corpus_size:1GB,wait_for_status:green,force_data_generation:true,query_warmup_time_period:60,number_of_shards:2,number_of_replicas:0" --on-error=abort

  echo "======================================== BEGIN SECURITY =========================================================="
  echo "**************************************** TESTING LIST TRACKS***************************************************"
  esrally list tracks --track-path="${PWD}/../security"
  echo "**************************************** TESTING INFO *********************************************************"
  esrally info --track-path="${PWD}/../security"
  echo "**************************************** CLEANING elastic/logs specific indices ************************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-indexing" --track-path="${PWD}/../logs" --include-tasks="delete-all-datastreams,delete-all-composable-templates,delete-all-component-templates" --on-error=abort
  echo "**************************************** TESTING security-indexing-querying using ${ES_VERSION}*******"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="security-indexing-querying"  --track-path="${PWD}/../security" --track-params="number_of_replicas:0" --on-error=abort


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
