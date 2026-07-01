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

PY_VERSION="$1"
TEST_NAME="$2"
IFS=',' read -ra RUN_FULL_CI_WHEN_CHANGED <<< "$3"

echo "--- System dependencies"

retry 5 sudo apt-get update
retry 5 sudo apt-get install -y \
    make \
    dnsutils  # provides nslookup

echo "--- Install uv"

curl -LsSf https://astral.sh/uv/0.11.19/install.sh | env UV_UNMANAGED_INSTALL="${HOME}/.local/bin" sh
export PATH="${HOME}/.local/bin:${PATH}"

echo "--- Create virtual environment"

make venv PY_VERSION="$PY_VERSION"

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


echo "--- Run IT serverless test \"$TEST_NAME\"$TRACK_FILTER_ARG :pytest:"

case "$TEST_NAME" in
    "test_user"|"user")
        make -s it-serverless PY_VERSION="$PY_VERSION" "ARGS=$TRACK_FILTER_ARG"
        ;;
    "test_operator"|"operator")
        make -s it-serverless PY_VERSION="$PY_VERSION" "ARGS=--operator$TRACK_FILTER_ARG"
        ;;
    *)
        echo "Unknown test type: $TEST_NAME"
        exit 1
        ;;
esac
