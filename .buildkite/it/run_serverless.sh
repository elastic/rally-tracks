#!/usr/bin/env bash

set -eo pipefail

source .buildkite/retry.sh

export TERM=dumb
export LC_ALL=en_US.UTF-8
export TZ=Etc/UTC
export DEBIAN_FRONTEND=noninteractive
# https://askubuntu.com/questions/1367139/apt-get-upgrade-auto-restart-services
sudo mkdir -p /etc/needrestart
echo "\$nrconf{restart} = 'a';" | sudo tee -a /etc/needrestart/needrestart.conf > /dev/null

PYTHON_VERSION="$1"
TEST_NAME="$2"
IFS=',' read -ra RUN_FULL_CI_WHEN_CHANGED <<< "$3"

function annotate_serverless_logs {
    local test_name="$1"
    local start_time="$2"
    local end_time="$3"
    local exit_status="$4"
    local output_file="$5"

    if ! command -v buildkite-agent >/dev/null 2>&1; then
        return
    fi

    local project_id
    project_id=$(grep -Eo 'SERVERLESS_PROJECT_ID=[A-Za-z0-9-]+' "$output_file" | tail -1 | cut -d= -f2)
    if [[ -z "$project_id" ]]; then
        return
    fi

    local serverless_url_prefix="https://overview.qa.cld.elstc.co"
    local serverless_log_path="/app/dashboards#/view/serverless-es-project-logs?_g=(time:(from:'%s',to:'%s'))&_a=(query:(language:kuery,query:'serverless.project.id:%s'))"
    local serverless_log_url
    # shellcheck disable=SC2059
    serverless_log_url=$(printf "${serverless_url_prefix}${serverless_log_path}" "$start_time" "$end_time" "$project_id")

    local style="info"
    local priority="3"
    if [[ $exit_status -ne 0 ]]; then
        style="error"
        priority="10"
    fi

    echo "$test_name #${BUILDKITE_RETRY_COUNT:-0} | Serverless ES Project Logs: [click]($serverless_log_url)" | \
        buildkite-agent annotate --style "$style" --context "serverless-es-project-logs-${test_name}-${BUILDKITE_RETRY_COUNT:-0}" --priority "$priority"
}

echo "--- System dependencies"

retry 5 sudo add-apt-repository --yes ppa:deadsnakes/ppa
retry 5 sudo apt-get update
retry 5 sudo apt-get install -y \
    "python${PYTHON_VERSION}" "python${PYTHON_VERSION}-dev" "python${PYTHON_VERSION}-venv" \
    dnsutils  # provides nslookup

echo "--- Python modules"

"python${PYTHON_VERSION}" -m venv .venv
source .venv/bin/activate
python -m pip install .[develop]

echo "--- Track filter modification"

CHANGED_FILES=$(git diff --name-only origin/master...HEAD)

if [[ -z "$CHANGED_FILES" ]]; then
    echo "No changed files detected between origin/master and HEAD. Running full CI"
    TRACK_FILTER_ARG=""
else
    readarray -t changed_files_arr <<< "$CHANGED_FILES"
    CHANGED_TOP_LEVEL_DIRS=$(printf '%s\n' "$CHANGED_FILES" | awk -F/ '/\//{print $1}' | sort -u | paste -sd, -)
    CHANGED_TOP_LEVEL_DIRS=${CHANGED_TOP_LEVEL_DIRS%,}
    IFS=',' read -ra changed_dirs_arr <<< "$CHANGED_TOP_LEVEL_DIRS"

    all_changed_arr=("${changed_files_arr[@]}" "${changed_dirs_arr[@]}")

    TRACK_FILTER_ARG=" --track-filter=${CHANGED_TOP_LEVEL_DIRS}"
    
    # If any changes match one of the RUN_FULL_CI_WHEN_CHANGED paths, run full CI
    for static_path in "${RUN_FULL_CI_WHEN_CHANGED[@]}"; do
        for changed in "${all_changed_arr[@]}"; do
            if [[ "$static_path" == "$changed" ]]; then
                echo "Matched '$static_path' in changed files/dirs. Running full CI."
                TRACK_FILTER_ARG=""
                break 2
            fi
        done
    done
fi


echo "--- Run IT serverless test \"$TEST_NAME\"$TRACK_FILTER_ARG :pytest:"

START_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OUTPUT_FILE="run_serverless_${TEST_NAME}.log"
set +e
hatch -v -e it_serverless run $TEST_NAME$TRACK_FILTER_ARG 2>&1 | tee "$OUTPUT_FILE"
EXIT_STATUS=${PIPESTATUS[0]}
set -e
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)

annotate_serverless_logs "$TEST_NAME" "$START_TIME" "$END_TIME" "$EXIT_STATUS" "$OUTPUT_FILE"

exit $EXIT_STATUS
