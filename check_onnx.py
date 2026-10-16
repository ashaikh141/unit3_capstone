"""Confirm onnx_embed.py produces the same vectors as sentence-transformers (which built your index)."""
import numpy as np
from sentence_transformers import SentenceTransformer

from onnx_embed import get_embedding

model = SentenceTransformer("all-MiniLM-L6-v2")
for sentence in ["What is our onboarding process?",
                 "How many active projects do we have?",
                 "What happens when a client pays late?"]:
    a = np.array(get_embedding(sentence))
    b = model.encode(sentence)
    cosine = float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
    print(f"{sentence:<42} cosine={cosine:.7f}  max_diff={np.abs(a - b).max():.1e}")
print("\nMatch if every cosine is 0.9999999 or higher.")