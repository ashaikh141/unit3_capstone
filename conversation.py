
import os


MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", "3"))

MAX_ANSWER_CHARS = 400


def trim_history(history):
    clean = []
    for turn in history or []:
        if isinstance(turn, dict) and turn.get("question"):
            clean.append({
                "question": str(turn["question"]),
                "answer": str(turn.get("answer", "")),
            })
    return clean[-MAX_HISTORY_TURNS:]


def history_block(history):
    turns = trim_history(history)
    if not turns:
        return ""
    lines = ["Earlier in this conversation (most recent last):"]
    for t in turns:
        lines.append(f"User: {t['question']}")
        lines.append(f"Assistant: {t['answer'][:MAX_ANSWER_CHARS]}")
    return "\n".join(lines) + "\n\n"