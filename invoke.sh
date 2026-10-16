#!/bin/bash
# Part 5: invoke the deployed function. Usage: bash invoke.sh "your question"
set -euo pipefail

FUNCTION=multi-agent-orchestrator-ashaikh
QUESTION=${1:-"How many active projects do we have, and what's our onboarding process?"}

python3 -c "import json, sys; print(json.dumps({'body': json.dumps({'question': sys.argv[1]})}))" \
    "$QUESTION" > event.json

aws lambda invoke --function-name "$FUNCTION" --payload file://event.json \
    --cli-binary-format raw-in-base64-out response.json >/dev/null

echo "== response.json (raw):"
cat response.json
echo
echo
echo "== response body, readable:"
python3 -c "
import json
r = json.load(open('response.json'))
body = json.loads(r['body']) if isinstance(r.get('body'), str) else r
print(json.dumps(body, indent=2))
"