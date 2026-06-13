#!/usr/bin/env python3
"""
rank.py — Main entry point for the Biscuit candidate ranking system.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Produces a CSV with the top 100 ranked candidates from the input file.
"""

import argparse
import csv
import random
import sys
import time

from src.loader import load_candidates
from src.filters import is_honeypot, compute_suspicion
from src.scorer import score_candidate
from src.ranker import rank_candidates


def main():
    parser = argparse.ArgumentParser(
        description="Biscuit — Intelligent Candidate Ranking System"
    )
    parser.add_argument(
        "--candidates",
        required=True,
        help="Path to candidates file (.jsonl or .json)",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Path to output CSV file",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=100,
        help="Number of top candidates to include (default: 100)",
    )
    args = parser.parse_args()

    # Deterministic seed for reproducibility in Docker sandbox
    random.seed(42)

    print("=" * 60)
    print("  Biscuit — Intelligent Candidate Ranking System")
    print("=" * 60)

    start_time = time.time()

    # ─── Stage 0: Load ───────────────────────────────────────────
    print("\n[Stage 0] Loading candidates...")
    load_start = time.time()

    total_loaded = 0
    honeypots_removed = 0
    scored_candidates = []

    for cand in load_candidates(args.candidates):
        total_loaded += 1

        # ─── Stage 1: Filter ────────────────────────────────────
        if is_honeypot(cand):
            honeypots_removed += 1
            continue

        # ─── Stage 2: Score ─────────────────────────────────────
        suspicion = compute_suspicion(cand)
        score_result = score_candidate(cand, suspicion)
        scored_candidates.append((cand, score_result))

        if total_loaded % 20000 == 0:
            elapsed = time.time() - load_start
            print(f"  ... processed {total_loaded:,} candidates ({elapsed:.1f}s)")

    load_elapsed = time.time() - load_start
    print(f"  Loaded: {total_loaded:,} candidates in {load_elapsed:.1f}s")
    print(f"  Honeypots removed: {honeypots_removed}")
    print(f"  Candidates scored: {len(scored_candidates):,}")

    # ─── Stage 3: Rank ──────────────────────────────────────────
    print(f"\n[Stage 3] Ranking top {args.top_n}...")
    rank_start = time.time()
    results = rank_candidates(scored_candidates, top_n=args.top_n)
    rank_elapsed = time.time() - rank_start
    print(f"  Ranking complete in {rank_elapsed:.2f}s")

    # ─── Stage 4: Write CSV ─────────────────────────────────────
    print(f"\n[Stage 4] Writing {len(results)} results to {args.out}...")
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["candidate_id", "rank", "score", "reasoning"],
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        for row in results:
            writer.writerow({
                "candidate_id": row["candidate_id"],
                "rank": row["rank"],
                "score": round(row["score"], 6),
                "reasoning": row["reasoning"],
            })

    total_elapsed = time.time() - start_time

    # ─── Summary ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    print(f"  Total candidates loaded:   {total_loaded:,}")
    print(f"  Honeypots eliminated:      {honeypots_removed}")
    print(f"  Candidates scored:         {len(scored_candidates):,}")
    print(f"  Top-{args.top_n} output:           {len(results)}")
    print(f"  Total runtime:             {total_elapsed:.2f}s")
    print(f"  Output file:               {args.out}")

    if results:
        print(f"  Score range:               {results[-1]['score']:.4f} — {results[0]['score']:.4f}")
        print(f"  Top-1:  {results[0]['candidate_id']} (score={results[0]['score']:.4f})")
        if len(results) >= 10:
            print(f"  Top-10: {results[9]['candidate_id']} (score={results[9]['score']:.4f})")
        print(f"  Top-{len(results)}: {results[-1]['candidate_id']} (score={results[-1]['score']:.4f})")

    print("=" * 60)
    print("Done.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
