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
readarray -t changed_files_arr <<< "$CHANGED_FILES"

CHANGED_TOP_LEVEL_DIRS=$(echo "$CHANGED_FILES" | grep '/' | awk -F/ '{print $1}' | sort -u | paste -sd, -)
CHANGED_TOP_LEVEL_DIRS=${CHANGED_TOP_LEVEL_DIRS%,}
IFS=',' read -ra changed_dirs_arr <<< "$CHANGED_TOP_LEVEL_DIRS"

all_changed_arr=("${changed_files_arr[@]}" "${changed_dirs_arr[@]}")

TRACK_FILTER_ARG="--track-filter=${CHANGED_TOP_LEVEL_DIRS}"

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
echo "--- Run IT serverless test \"$TEST_NAME\" $TRACK_FILTER_ARG :pytest:"

hatch -v -e it_serverless run $TEST_NAME $TRACK_FILTER_ARG
