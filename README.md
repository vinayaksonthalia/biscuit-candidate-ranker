# Biscuit — Intelligent Candidate Ranking System

A deterministic, CPU-only candidate ranking engine for the India Runs Data & AI Challenge. Processes 100K candidates in <10 seconds, producing a top-100 shortlist with fact-grounded reasoning.

## Architecture

```
candidates.jsonl (100K)
        │
        ▼
┌────────────────────┐
│  loader.py          │  Stream JSONL line-by-line
└────────────────────┘
        │
        ▼
┌────────────────────┐
│  filters.py         │  Hard-eliminate honeypots (42 confirmed)
│                     │  Compute suspicion score for borderline profiles
└────────────────────┘
        │ (~99,958 remain)
        ▼
┌────────────────────┐
│  scorer.py          │  6-dimension weighted scoring
│                     │  Career (30%) + Skills (25%) + Experience (15%)
│                     │  + Behavioral (15%) + Location (10%) + Education (5%)
└────────────────────┘
        │
        ▼
┌────────────────────┐
│  ranker.py          │  Sort, top-100, deterministic fact-first reasoning
└────────────────────┘
        │
        ▼
   submission.csv
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run on sample data
python rank.py --candidates ./data/sample_candidates.json --out ./sample_out.csv --top-n 50

# Run on full dataset
python rank.py --candidates ./candidates.jsonl --out ./submission.csv

# Validate output
python validate_submission.py submission.csv
```

## Docker

```bash
docker build -t biscuit .
docker run -v $(pwd)/data:/app/data biscuit
```

## Reproduce Command (per spec)

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

## Design Decisions

- **Streaming loader**: Line-by-line JSONL parsing keeps RAM under 500MB for 100K candidates.
- **Skills gate**: Candidates with zero relevant ML/NLP skills are capped regardless of other dimensions, preventing non-technical profiles from ranking highly on location/engagement alone.
- **Consulting penalty, not filter**: Pure services-company careers receive a heavy scoring penalty rather than hard elimination. Mixed careers (e.g., TCS → startup) get proportional credit.
- **Per-candidate deterministic reasoning**: Uses `hashlib.md5(candidate_id)` for seeding, not Python's `hash()` (which is randomized across processes since 3.3). Identical CSV output across runs guaranteed.
- **Honeypot detection**: Three rules catching 42 definitively impossible profiles (expert skills with zero duration, job duration exceeding career span, calendar date impossibilities). Borderline profiles receive scoring penalties.

## Team

- **Team Name**: Biscuit
- **Submission for**: India Runs Data & AI Challenge – Stage 3
