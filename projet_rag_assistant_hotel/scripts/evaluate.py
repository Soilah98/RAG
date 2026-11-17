import json

import numpy as np

from hotel_rag import config
from hotel_rag.store import search

EVAL_PATH = config.ROOT / "eval" / "eval_set.json"


import numpy as np

def evaluate(items: list[dict], k_values=(1, 2, 3, 5)) -> dict:
    ranks = []
    margins = []
    dcg_list = []
    idcg_list = []
    ap_list = []
    
    for item in items:
        hits = search(item["question"], top_k=1000)
        titles = [h.title for h in hits]
        # Dédoublonnage en gardant l'ordre
        unique_titles = list(dict.fromkeys(titles))
        
        # Gestion si expected est une liste (multi-chunks) ou un string unique
        expected = item["expected"]
        if isinstance(expected, str):
            expected = [expected]
            
        # Trouver les rangs (1-indexed) de tous les documents pertinents
        item_ranks = [unique_titles.index(exp) + 1 for exp in expected if exp in unique_titles]
        
        if not item_ranks:
            # Aucun bon doc trouvé dans les résultats
            ranks.append(999999)
            margins.append(0.0)
            dcg_list.append(0.0)
            idcg_list.append(sum(1 / np.log2(i + 2) for i in range(len(expected))))
            ap_list.append(0.0)
            continue
            
        best_rank = min(item_ranks)
        ranks.append(best_rank)
        
        # Correction de la marge : Score du meilleur bon doc vs Score du pire faux positif du top
        good_scores = [h.similarity for h in hits if h.title in expected]
        bad_scores = [h.similarity for h in hits if h.title not in expected]
        if good_scores and bad_scores:
            margins.append(max(good_scores) - max(bad_scores))
        else:
            margins.append(0.0)
            
        # Calcul NDCG@5 simplifié
        dcg = sum(1 / np.log2(r + 1) for r in item_ranks if r <= 5)
        idcg = sum(1 / np.log2(i + 2) for i in range(min(len(expected), 5)))
        dcg_list.append(dcg / idcg if idcg > 0 else 0)
        
        # Calcul AP (Average Precision) pour le multi-label
        # ...
        
    ranks = np.array(ranks)
    metrics = {
        "n_questions": len(items),
        "MRR": float((1 / np.where(ranks <= len(hits), ranks, 0)).mean()),
        "marge_moyenne": float(np.mean(margins)),
        "NDCG@5": float(np.mean(dcg_list)),
    }
    
        # Ajout dynamique des Recall@K
    for k in k_values:
        metrics[f"recall@{k}"] = float((ranks <= k).mean())
        
    return metrics


if __name__ == "__main__":
    items = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    for name, value in evaluate(items).items():
        print(f"{name:15s} {value:.3f}" if isinstance(value, float) else f"{name:15s} {value}")