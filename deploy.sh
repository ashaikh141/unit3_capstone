#!/bin/bash
# Parts 3-5: IAM role, access to your existing RDS + OpenSearch, upload, create or update the function.
# Safe to re-run: it updates what already exists.
set -euo pipefail

NAME=ashaikh
REGION=us-east-1
DB=bootcamp-db-ashaikh
DOMAIN=vector-search-ashaikh
FUNCTION=multi-agent-orchestrator-$NAME
ROLE=orchestrator-lambda-role-$NAME
SRC=~/bootcamp/deployment
ZIP=~/orchestrator_function.zip

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
BUCKET=lambda-deploy-$ACCOUNT-$NAME
RUNTIME=python$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
WORK=$(mktemp -d)

echo "== Part 3: IAM role $ROLE"
NEW_ROLE=0
if aws iam get-role --role-name "$ROLE" >/dev/null 2>&1; then
    echo "   Role already exists"
else
    cat > "$WORK/trust.json" << EOF
{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
EOF
    aws iam create-role --role-name "$ROLE" --assume-role-policy-document "file://$WORK/trust.json" >/dev/null
    aws iam attach-role-policy --role-name "$ROLE" \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    echo "   Created role + attached AWSLambdaBasicExecutionRole (CloudWatch logs)"
    NEW_ROLE=1
fi

cat > "$WORK/scoped-policy.json" << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": ["arn:aws:bedrock:*::foundation-model/*", "arn:aws:bedrock:*:$ACCOUNT:inference-profile/*"]
    },
    {
      "Effect": "Allow",
      "Action": ["es:ESHttpGet", "es:ESHttpPost", "es:ESHttpPut", "es:ESHttpHead"],
      "Resource": "arn:aws:es:$REGION:$ACCOUNT:domain/$DOMAIN/*"
    }
  ]
}
EOF
aws iam put-role-policy --role-name "$ROLE" --policy-name orchestrator-inline-policy \
    --policy-document "file://$WORK/scoped-policy.json"
echo "   Inline policy: Bedrock invoke + read/search on $DOMAIN only"

echo "== Part 4: let Lambda reach your existing RDS ($DB)"
SG=$(aws rds describe-db-instances --db-instance-identifier "$DB" \
    --query "DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId" --output text)
if aws ec2 authorize-security-group-ingress --group-id "$SG" --protocol tcp --port 5432 \
    --cidr 0.0.0.0/0 >/dev/null 2>&1; then
    echo "   Opened port 5432 (Lambda has no fixed IP address)"
else
    echo "   Port 5432 already open"
fi

echo "== Environment variables for the function (read from $SRC/.env)"
python3 - "$SRC/.env" > "$WORK/env.json" << 'PY'
import json, sys
keep = ["RDS_HOST", "RDS_PORT", "RDS_DATABASE", "RDS_USER", "RDS_PASSWORD", "OPENSEARCH_ENDPOINT"]
values = {}
for line in open(sys.argv[1]):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
missing = [k for k in keep if not values.get(k)]
if missing:
    sys.exit(f"Missing from .env: {missing}")
print(json.dumps({"Variables": {k: values[k] for k in keep}}))
PY
echo "   Set: RDS_HOST, RDS_PORT, RDS_DATABASE, RDS_USER, RDS_PASSWORD, OPENSEARCH_ENDPOINT"

echo "== Part 5: upload the package through S3 ($BUCKET)"
aws s3 mb "s3://$BUCKET" --region "$REGION" >/dev/null 2>&1 || true
aws s3 cp "$ZIP" "s3://$BUCKET/orchestrator_function.zip"

if aws lambda get-function --function-name "$FUNCTION" >/dev/null 2>&1; then
    echo "== Updating existing function $FUNCTION"
    aws lambda update-function-code --function-name "$FUNCTION" \
        --s3-bucket "$BUCKET" --s3-key orchestrator_function.zip >/dev/null
    aws lambda wait function-updated-v2 --function-name "$FUNCTION"
    aws lambda update-function-configuration --function-name "$FUNCTION" --runtime "$RUNTIME" \
        --timeout 120 --memory-size 1024 --environment "file://$WORK/env.json" >/dev/null
else
    echo "== Creating function $FUNCTION (runtime $RUNTIME)"
    [ "$NEW_ROLE" = 1 ] && { echo "   Waiting 15s for the new role to propagate"; sleep 15; }
    for attempt in 1 2 3 4 5; do
        if aws lambda create-function --function-name "$FUNCTION" --runtime "$RUNTIME" \
            --handler lambda_handler.handler \
            --code "S3Bucket=$BUCKET,S3Key=orchestrator_function.zip" \
            --role "arn:aws:iam::$ACCOUNT:role/$ROLE" \
            --timeout 120 --memory-size 1024 \
            --environment "file://$WORK/env.json" >/dev/null 2> "$WORK/err.txt"; then
            break
        fi
        if grep -q "cannot be assumed" "$WORK/err.txt" && [ "$attempt" -lt 5 ]; then
            echo "   Role not ready yet, retrying in 10s ($attempt/5)"; sleep 10
        else
            cat "$WORK/err.txt"; exit 1
        fi
    done
fi

echo "== Waiting until the function is fully updated (function-updated-v2)"
aws lambda wait function-updated-v2 --function-name "$FUNCTION"
echo "== Deployed: $FUNCTION"