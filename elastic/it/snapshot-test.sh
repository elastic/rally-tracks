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

# This test is designed to test snapshot restore and assumes the user has permission to access the s3 bucket used.
# Ensure you have the aws client installed, or okta equivalent.

# fail this script immediately if any command fails with a non-zero exit code
set -e
# Treat unset env variables as an error
set -u
# fail on pipeline errors, e.g. when grepping
set -o pipefail

readonly RACE_ID=$(uuidgen | tr "[:upper:]" "[:lower:]")
readonly ES_VERSION=${ES_VERSION:-7.17.1}
SNAPSHOT_BUCKET=$1

INSTALL_ID=-1

export THESPLOG_FILE="${THESPLOG_FILE:-${HOME}/.rally/logs/actor-system-internal.log}"
# this value is in bytes, the default is 50kB. We increase it to 200kiB.
export THESPLOG_FILE_MAXSIZE=${THESPLOG_FILE_MAXSIZE:-204800}
# adjust the default log level from WARNING
export THESPLOG_THRESHOLD="DEBUG"

if [[ -z "$AWS_PROFILE" ]]; then
    echo "Must provide AWS_PROFILE in environment to run this test" 1>&2
    exit 1
fi

function log {
    local ts=$(date -u "+%Y-%m-%dT%H:%M:%SZ")
    echo "[${ts}] [${1}] ${2}"
}

function info {
    log "INFO" "${1}"
}

function delete_snapshot {
  info "deleting \"${1}\" snapshot"
  success=$(curl -s -o /dev/null -w "%{http_code}" -XDELETE "http://127.0.0.1:39200/_snapshot/logging/${1}")
  if [ "$success" != 200 ]; then
    echo "Unable to delete snapshot ${1} - received ${success}"
    exit 1
  fi
}

function set_up {
  info "preparing cluster using ${AWS_PROFILE} profile"
  # we need these to test snapshot restore and assume the user has access to our test bucket
  AWS_ACCESS_KEY_ID=$(./get-aws-profile.sh --profile="${AWS_PROFILE}" --key)
  AWS_SECRET_ACCESS_KEY=$(./get-aws-profile.sh --profile="${AWS_PROFILE}" --secret)
  AWS_SESSION_TOKEN=$(./get-aws-profile.sh --profile="${AWS_PROFILE}" --session-token)

  INSTALL_ID=$(esrally install --quiet --distribution-version="${ES_VERSION}" --car="defaults,basic-license" --elasticsearch-plugins="repository-s3" --plugin-params="s3_client_name:default,s3_access_key:${AWS_ACCESS_KEY_ID},s3_secret_key:${AWS_SECRET_ACCESS_KEY},s3_session_token:${AWS_SESSION_TOKEN}" --runtime-jdk="bundled" --node-name="rally-node-0" --network-host="127.0.0.1" --http-port=39200 --master-nodes="rally-node-0" --seed-hosts="127.0.0.1:39300" | jq --raw-output '.["installation-id"]')
  esrally start --installation-id="${INSTALL_ID}" --race-id="${RACE_ID}" --runtime-jdk="bundled"
}

function run_test {
  echo "**************************************** Race Id - ${RACE_ID} *************************************************"
  echo "**************************************** TESTING SNAPSHOT RESTORE ***************************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --track-params="number_of_replicas:0,snapshot_bucket:${SNAPSHOT_BUCKET},snapshot_name:logging-test,snapshot_base_path:observability/logging-integration-tests" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-snapshot-restore" --track-path="${PWD}/../logs" --on-error=abort
  doc_count=$(curl -s http://127.0.0.1:39200/logs-*/_count | jq -r ".count")
  echo "**************************************** TESTING SNAPSHOT ***************************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --track-params="snapshot_name:logging-test-${RACE_ID},snapshot_bucket:${SNAPSHOT_BUCKET},snapshot_base_path:observability/logging-integration-tests" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-snapshot" --exclude-tasks="force-merge-data-streams" --track-path="${PWD}/../logs" --on-error=abort
  echo "**************************************** TESTING SNAPSHOT RESTORE WITH RENAME ***************************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --track-params="number_of_replicas:0,snapshot_name:logging-test,snapshot_bucket:${SNAPSHOT_BUCKET},snapshot_base_path:observability/logging-integration-tests,snapshot_rename_suffix:-1" --exclude-tasks="tag:setup" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-snapshot-restore" --track-path="${PWD}/../logs" --on-error=abort
  new_doc_count=$(curl -s http://127.0.0.1:39200/logs-*/_count | jq -r ".count")
  expected_doc_count=$((2*$doc_count))
  if [ "$new_doc_count" != "$expected_doc_count" ]; then
    echo "Unexpected doc count after restoring snapshots. Expected ${expected_doc_count}, Got ${new_doc_count}" 1>&2
    exit 1
  fi
  # delete the snapshot before re-taking
  delete_snapshot "logging-test-${RACE_ID}"
  echo "**************************************** TESTING SNAPSHOT WITH FORCED MERGE ***************************************************"
  esrally race --kill-running-processes --race-id="${RACE_ID}" --track-params="snapshot_name:logging-test-${RACE_ID},snapshot_bucket:${SNAPSHOT_BUCKET},snapshot_base_path:observability/logging-integration-tests" --test-mode --pipeline=benchmark-only --target-host=127.0.0.1:39200 --challenge="logging-snapshot" --track-path="${PWD}/../logs" --on-error=abort
  delete_snapshot "logging-test-${RACE_ID}"
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
