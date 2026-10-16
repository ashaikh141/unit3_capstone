#!/bin/bash
set -euo pipefail

SRC=~/bootcamp/deployment
PKG=~/deployment-package
ZIP=~/orchestrator_function.zip
RUNTIME_SIM=~/lambda-runtime-sim

echo "== Building with $(python3 --version) - the Lambda --runtime must match this"
rm -rf "$PKG"
mkdir -p "$PKG"
cd "$PKG"

echo "== Installing dependencies into the package (takes a few minutes)"
pip install --quiet -t . langgraph psycopg2-binary opensearch-py requests-aws4auth python-dotenv \
    onnxruntime tokenizers numpy

echo "== Trimming files never used at runtime"
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -type d -name "tests" -prune -exec rm -rf {} +
rm -rf bin huggingface_hub hf_xet numpy/f2py onnxruntime/datasets
rm -rf sympy sympy-*.dist-info mpmath mpmath-*.dist-info onnxruntime/tools onnxruntime/transformers
rm -rf zstandard zstandard-*.dist-info grpc grpcio-*.dist-info google protobuf-*.dist-info
find . -name "*.pyi" -delete
rm -rf numpy/_core/include numpy/random/_examples

echo "== Adding your code and the embedding model"
cp "$SRC"/{lambda_handler.py,orchestrator.py,tools.py,registry.py,validator.py,adapters.py,llm.py,conversation.py} .
cp "$SRC"/{onnx_embed.py,bedrock_client.py,tokenomics_logger.py,schema_context.py,sql_validator.py} .
cp "$SRC"/{model.onnx,tokenizer.json} .
cp -r "$SRC/agents" .
find agents -type d -name "__pycache__" -prune -exec rm -rf {} +

echo "== 15 biggest items in the package (MB):"
du -sm --apparent-size * | sort -rn | head -15

SIZE=$(du -sm --apparent-size . | cut -f1)
echo "== Unzipped size: ${SIZE} MB of actual file data (Lambda limit: 250 MB)"
if [ "$SIZE" -ge 250 ]; then
    echo "!! Too big for Lambda"
    exit 1
fi

echo "== Verifying the package works ON ITS OWN with a real question"
[ -d "$RUNTIME_SIM/boto3" ] || pip install --quiet -t "$RUNTIME_SIM" boto3
set -a; . "$SRC/.env"; set +a
(
    cd "$(mktemp -d)"
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PKG:$RUNTIME_SIM" python3 -S -c "
from lambda_handler import handler
r = handler({'question': 'How many active projects do we have?', 'history': []}, None)
print('   route:', r.get('route'), '| sql_validation:', r.get('sql_validation'))
print('   answer:', str(r.get('answer'))[:200])
assert 'error' not in r and r.get('answer'), r
"
)

echo "== Zipping"
rm -f "$ZIP"
python3 -c "import shutil, os; shutil.make_archive(os.path.expanduser('~/orchestrator_function'), 'zip', os.path.expanduser('~/deployment-package'))"
ls -lh "$ZIP"
echo "== Package ready: $ZIP"