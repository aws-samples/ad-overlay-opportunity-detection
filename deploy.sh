#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd ${DIR}

STACK_NAME=$1
ARTIFACT_BUCKET=${ARTIFACT_BUCKET:=$2}
REGION=${AWS_DEFAULT_REGION:=$3}

echo "
###############################
# Building and deploying Stack
###############################

STACK_NAME = ${STACK_NAME}
ARTIFACT_BUCKET = ${ARTIFACT_BUCKET}
REGION = ${REGION}
"
sam build -t cloudformation.yml

sam deploy \
    --stack-name ${STACK_NAME} \
    --s3-bucket ${ARTIFACT_BUCKET} \
    --capabilities CAPABILITY_IAM \
    --region ${REGION} \
    --no-fail-on-empty-changeset
