import json

import numpy as np

from hotel_rag import config
from hotel_rag.store import search


def top1(question: str) -> float:
    return search(question, top_k=1)[0].similarity


if __name__ == "__main__":
    in_scope = [it["question"] for it in json.loads(
        (config.ROOT / "eval" / "eval_set.json").read_text(encoding="utf-8"))]
    out_scope = json.loads(
        (config.ROOT / "eval" / "out_of_scope.json").read_text(encoding="utf-8"))

    s_in = np.array([top1(q) for q in in_scope])
    s_out = np.array([top1(q) for q in out_scope])

    print(f"Dans le périmètre  : n={len(s_in)}, min={s_in.min():.3f}, médiane={np.median(s_in):.3f}")
    print(f"Hors périmètre     : n={len(s_out)}, max={s_out.max():.3f}, médiane={np.median(s_out):.3f}\n")

    print("Hors périmètre, du plus proche au plus éloigné :")
    for s, q in sorted(zip(s_out, out_scope), reverse=True):
        print(f"  {s:.3f}  {q}")

    print(f"\n{'seuil':>6} | {'questions valides gardées':>26} | {'hors périmètre bloquées':>24}")
    for t in np.arange(0.10, 0.60, 0.05):
        print(f"{t:6.2f} | {(s_in >= t).mean():>26.0%} | {(s_out < t).mean():>24.0%}")

    safe = np.floor((s_in.min() - 0.02) * 100) / 100
    print(f"\nSeuil prudent suggéré : {safe:.2f}  "
          f"(garde 100 % des questions valides, bloque {(s_out < safe).mean():.0%} des hors périmètre)")
    if s_out.max() >= safe:
        print("⚠️ Chevauchement : au moins une question hors périmètre dépasse ce seuil. "
              "Le seuil seul ne suffit pas, le LLM reste le second filet.")