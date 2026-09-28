"""Backtracking quota solver, grouped by subject/source/difficulty, bounded search.
The small number of groups makes this independent of bank size; selection prefers unseen concepts.
"""

from collections import defaultdict, Counter
import random
from fastapi import HTTPException


def solve(pool, subjects, sources, difficulties, recent):
    groups = defaultdict(list)
    for q in pool:
        if (
            subjects.get(q.subject, 0)
            and sources.get(q.source_type, 0)
            and difficulties.get(q.difficulty, 0)
        ):
            groups[(q.subject, q.source_type, q.difficulty)].append(q)
    for s, n in subjects.items():
        if sum(len(v) for k, v in groups.items() if k[0] == s) < n:
            raise HTTPException(
                409,
                f"Not enough eligible {s} questions. Adjust source/difficulty mix or approve more questions.",
            )
    keys = sorted(groups, key=lambda k: len(groups[k]))
    s = dict(subjects)
    r = dict(sources)
    d = dict(difficulties)
    alloc = {}
    nodes = 0

    def search(i):
        nonlocal nodes
        nodes += 1
        if nodes > 150000:
            return False
        if i == len(keys):
            return not any(s.values()) and not any(r.values()) and not any(d.values())
        key = keys[i]
        a, b, c = key
        for dimension, remaining in [(0, s), (1, r), (2, d)]:
            for label, need in remaining.items():
                if need > sum(
                    len(groups[k]) for k in keys[i:] if k[dimension] == label
                ):
                    return False
        high = min(len(groups[key]), s[a], r[b], d[c])
        for n in range(high, -1, -1):
            s[a] -= n
            r[b] -= n
            d[c] -= n
            alloc[key] = n
            if search(i + 1):
                return True
            s[a] += n
            r[b] += n
            d[c] += n
        return False

    if not search(0):
        raise HTTPException(
            409,
            "The bank cannot satisfy this exact subject/source/difficulty mix. Add approved questions or change the configuration.",
        )
    chosen = []
    concepts = Counter()
    rng = random.SystemRandom()
    for key, n in alloc.items():
        candidates = groups[key][:]
        rng.shuffle(candidates)
        for _ in range(n):
            q = min(
                candidates,
                key=lambda q: (q.id in recent, concepts[(q.topic, q.subtopic)]),
            )
            chosen.append(q)
            concepts[(q.topic, q.subtopic)] += 1
            candidates.remove(q)
    return chosen
