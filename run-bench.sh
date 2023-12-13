#!/bin/bash
set -euox pipefail

source ~/rally/.venv/bin/activate

export ESS_PUBLIC_URL=""
export API_KEY=""

esrally race --pipeline=benchmark-only --target-host=$ESS_PUBLIC_URL \
   --track-path=/home/alex-spies/rally-tracks/nyc_taxis \
   --race-id="$1" \
   --client-options="api_key:'$API_KEY'" \
   --kill-running-processes \
   --challenge=esql-serverless-concurrent-ingest \
   #--challenge=esql-serverless \
   #--challenge=esql-serverless-parallel \
   #--track-params=ingest_percentage:5
   #--exclude-tasks="tag:setup"
