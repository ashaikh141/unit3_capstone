"""Switch agents/retrieval_agent.py from sentence-transformers to onnx_embed. Safe to run twice."""
import re

path = "agents/retrieval_agent.py"
code = open(path).read()

if "from onnx_embed import get_embedding" in code:
    print("Already using onnx_embed - nothing to change")
else:
    code = code.replace("from sentence_transformers import SentenceTransformer\n",
                        "from onnx_embed import get_embedding\n")
    code, n = re.subn(
        r"_embed_model = None\n\n\ndef get_embedding\(text: str\) -> list\[float\]:\n"
        r"    global _embed_model\n    if _embed_model is None:\n"
        r"        _embed_model = SentenceTransformer\(\"all-MiniLM-L6-v2\"\)\n"
        r"    return _embed_model\.encode\(text\)\.tolist\(\)\n",
        "",
        code,
    )
    if n != 1 or "SentenceTransformer" in code:
        raise SystemExit("Could not find the sentence-transformers get_embedding block - paste me agents/retrieval_agent.py")
    open(path, "w").write(code)
    print("agents/retrieval_agent.py now uses onnx_embed.get_embedding")