import numpy as np

from movies.models import UserViewInteraction


def calculate_user_embedding(interactions_data):
    """
    interactions_data: list of objects/dicts with:
       - .show.embedding (or ['show']['embedding'])
       - .rating         (or ['rating'])
    """
    if not interactions_data:
        return None

    embs = []
    weights = []

    for i, inter in enumerate(interactions_data):
        # Handle both object attribute or dict access (flexible for tests)
        if isinstance(inter, dict):
            # For dict, we assume structure like {'show': {'embedding': ...}, 'rating': ...}
            rating = inter.get("rating")
            show_emb = inter.get("show", {}).get("embedding")
        else:
            rating = inter.rating
            show_emb = inter.show.embedding

        if show_emb is None:
            continue

        emb = np.array(show_emb, dtype=float)

        if rating == 2:  # way up (double thumbs up)
            r_weight = 5.0
        elif rating == 1:  # up (thumbs up)
            r_weight = 3.0
        elif rating == 0:  # down (thumbs down)
            r_weight = 0.0
        else:
            # Unrated / watched: lower confidence than explicit like
            r_weight = 0.5

        # Temporal weight: linearly increase from 0.5 to 1.0 based on position
        # We assume interactions_data is sorted by time (oldest -> newest)
        t_weight = 0.5 + (0.5 * (i / max(1, len(interactions_data) - 1)))

        # Combined weight
        w = r_weight * t_weight

        embs.append(emb)
        weights.append(w)

    if not embs:
        return None

    embs = np.stack(embs)  # shape (n, d)
    weights = np.array(weights)  # shape (n,)

    user_vec = np.average(embs, axis=0, weights=weights)
    # normalize
    norm = np.linalg.norm(user_vec)
    if norm == 0:
        return None
    user_vec = user_vec / norm

    return user_vec.tolist()


def get_user_embedding(user_id: int, min_items: int = 3):
    interactions = UserViewInteraction.objects.filter(user_id=user_id, show__embedding__isnull=False).select_related(
        "show"
    )

    if interactions.count() < min_items:
        return None  # not enough data – fall back to query-only

    return calculate_user_embedding(interactions)


def combine_query_and_user(q_vec, u_vec, alpha: float = 0.5):
    q = np.array(q_vec, dtype=float)
    u = np.array(u_vec, dtype=float)

    combo = alpha * q + (1 - alpha) * u
    norm = np.linalg.norm(combo)
    if norm == 0:
        return q_vec
    combo = combo / norm
    return combo.tolist()
