#!/usr/bin/env bash
# this is a comment
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

echo "--- Run IT serverless test \"$TEST_NAME\" :pytest:"

hatch -v -e it_serverless run $TEST_NAME

