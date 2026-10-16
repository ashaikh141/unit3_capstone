import glob
import os
import re

print(".env keys (values hidden):")
if os.path.exists(".env"):
    for line in open(".env", encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            print("  " + line.split("=", 1)[0])
else:
    print("  (no .env found)")

pattern = re.compile(r"(^\s*(def|class) |psycopg2|pymysql|model_?id|index)", re.IGNORECASE)
files = ["onnx_embed.py", "bedrock_client.py", "tokenomics_logger.py",
         "orchestrator.py", "lambda_handler.py"] + glob.glob("agents/*.py")
for path in files:
    if os.path.exists(path):
        print(f"\n{path}")
        for i, line in enumerate(open(path, encoding="utf-8"), 1):
            if pattern.search(line):
                print(f"  {i}: {line.rstrip()}")