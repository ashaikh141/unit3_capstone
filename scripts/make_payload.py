import json
import sys

import questions

key, out_path = sys.argv[1], sys.argv[2]
payload = {"question": getattr(questions, key), "history": []}
if len(sys.argv) > 3:
    with open(sys.argv[3], encoding="utf-8") as f:
        payload["history"] = json.load(f).get("history", [])
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
print(json.dumps(payload, indent=2))