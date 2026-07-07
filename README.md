# Project 3: AI Recommendation Logic

**DecodeLabs Industrial Training Kit -- Batch 2026**

## Goal

Build a content-based recommendation engine that learns what you like,
finds the best matches from a catalogue, and explains WHY each item was
recommended -- all with pure Python, no ML libraries.

## How to Run

```bash
python main.py
```

## Features

| Phase | What it does |
|-------|--------------|
| **Quick start** | Pick genres + era/popularity bias, get instant recommendations |
| **Rate movies** | Rate 5-10 movies from the catalogue to build a detailed profile |
| **Browse catalogue** | See all 40 movies grouped by genre |
| **Show recommendations** | Get top-10 ranked with scores and explanations |
| **Refine with feedback** | Rate the recommendations -- the engine re-learns and re-ranks |
| **Compare profiles** | Build two profiles side-by-side and cross-check |

## How It Works

### 1. Multi-dimensional similarity scoring

Every item is scored against the user's profile across four weighted dimensions:

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| **Genre** | 40% | Cosine similarity between profile genre affinities and item genres |
| **Tags** | 30% | Cosine similarity between profile tag affinities and item tags |
| **Era** | 15% | How well item year matches the user's era preference |
| **Popularity** | 15% | How well item rating matches user's mainstream/hidden-gem bias |

### 2. Profile building

Two ways to build a profile:

- **Genre picker**: Directly select genres + era/pop preference. Fast.
- **Rating-based**: Rate movies 1-5. Each rating adds weighted signals for
  genres, tags, era direction, and popularity direction. The formula maps
  ratings to continuous weights:
  - Rating 5 (love) => +1.0 weight
  - Rating 3 (neutral) => 0.0 (no signal)
  - Rating 1 (hate) => -1.0 weight

### 3. Feedback loop

Rate the recommendations themselves -- the profile rebuilds with the new
data, and recommendations update in real time.

### 4. Explanations

Every recommendation includes human-readable reasons:
- "You like action (and 2 more)"
- "Tag match: mind-bending (+1 more)"
- "Recent release (you seem to prefer newer films)"
- "Critically acclaimed (avg rating 9.0)"

## Files

| File | Purpose |
|------|---------|
| `main.py` | Interactive CLI -- menus, onboarding, feedback loop |
| `recommender.py` | Core engine -- Item/UserProfile, scoring, ranking, explanations |

## Key Skills Practiced

| Skill | Where |
|-------|-------|
| **Content-based filtering** | `recommender.py` -- weighted multi-dimensional scoring |
| **Vector similarity** | `cosine_similarity()` with sparse genre/tag vectors |
| **Profile building** | `build_profile_from_ratings()` -- weighted signal accumulation |
| **Explanations / transparency** | `generate_explanation()` -- why each item was chosen |
| **Feedback loops** | `main.py` -- phase_feedback_loop() |
| **Feature engineering** | Genre one-hot vectors, tag vectors, era/pop normalization |
| **Interactive UX** | `main.py` -- menu system with validation |

## Extensions to Try

- Save/load profiles to a JSON file so recommendations persist
- Add collaborative filtering ("people who liked X also liked Y")
- Weighted k-NN style: closer genre matches get exponentially higher scores
- Hybrid approach: blend content-based score with collaborative signal
- Add a "surprise me" mode that blends high-score with some diversity

---

*All 3 projects complete! Portfolio-ready.*
