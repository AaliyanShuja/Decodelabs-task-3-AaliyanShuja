"""
Content-based Recommendation Engine — from scratch.

Core concepts:
  1. Items are described by attributes (genres, tags, era, popularity)
  2. A user profile is built from their ratings / preferences
  3. Each candidate item is scored by weighted similarity to the profile
  4. Top-N items are recommended with explanations
"""

import math
from dataclasses import dataclass, field


# ─── Data structures ────────────────────────────────────────

@dataclass
class Item:
    """A recommendable item (movie, book, etc.)."""
    id: int
    title: str
    year: int
    genres: list[str]          # e.g. ["Action", "Sci-Fi"]
    tags: list[str]            # e.g. ["time-travel", "mind-bending"]
    avg_rating: float          # community rating 1.0 – 10.0
    description: str = ""

    def __hash__(self) -> int:
        return self.id


@dataclass
class UserProfile:
    """
    A user's preference profile built from their ratings.
    """
    rated_items: dict[int, float] = field(default_factory=dict)
    # genre affinities built from ratings
    genre_weights: dict[str, float] = field(default_factory=dict)
    # tag affinities
    tag_weights: dict[str, float] = field(default_factory=dict)
    # preferred era bias (-1 = old, 0 = any, +1 = recent)
    era_bias: float = 0.0
    # popularity preference (-1 = underground, 0 = any, +1 = mainstream)
    pop_bias: float = 0.0


# ─── Catalogue ──────────────────────────────────────────────

MOVIE_CATALOGUE: list[Item] = [
    # ── Sci-Fi / Fantasy ──────────────────────────────────
    Item(1,  "The Matrix",         1999, ["Action", "Sci-Fi"],       ["virtual-reality", "dystopian", "martial-arts"],   8.7, "A hacker discovers reality is a simulation."),
    Item(2,  "Inception",          2010, ["Action", "Sci-Fi", "Thriller"], ["dreams", "heist", "mind-bending"],          8.8, "A thief enters people's dreams to steal secrets."),
    Item(3,  "Interstellar",       2014, ["Sci-Fi", "Drama"],        ["space-travel", "time-dilation", "father-daughter"], 8.7, "Astronauts search for a new home for humanity."),
    Item(4,  "Blade Runner 2049",  2017, ["Sci-Fi", "Drama"],        ["android", "dystopian", "neo-noir"],               8.0, "A new blade runner uncovers a long-buried secret."),
    Item(5,  "Dune",               2021, ["Sci-Fi", "Adventure"],    ["space-opera", "politics", "sandworm"],             8.0, "A young noble must protect his planet."),
    Item(6,  "Arrival",            2016, ["Sci-Fi", "Drama"],        ["aliens", "linguistics", "nonlinear-time"],         7.9, "A linguist races to communicate with alien visitors."),
    Item(7,  "Mad Max: Fury Road", 2015, ["Action", "Sci-Fi"],      ["post-apocalyptic", "car-chase", "survival"],        8.1, "A road warrior helps rebels escape a tyrant."),
    Item(8,  "The Martian",        2015, ["Sci-Fi", "Adventure"],    ["mars", "survival", "solo-stranded"],               8.0, "An astronaut is left behind on Mars."),
    Item(9,  "Looper",             2012, ["Action", "Sci-Fi"],       ["time-travel", "assassin", "paradox"],              7.4, "A hitman from the future is sent back in time."),
    Item(10, "Ex Machina",         2014, ["Sci-Fi", "Thriller"],     ["AI", "android", "isolation"],                     7.7, "A programmer tests an AI's consciousness."),
    # ── Action / Thriller ──────────────────────────────────
    Item(11, "The Dark Knight",    2008, ["Action", "Drama", "Thriller"], ["superhero", "chaos", "moral-dilemma"],       9.0, "Batman faces the Joker's reign of chaos."),
    Item(12, "John Wick",          2014, ["Action", "Thriller"],     ["assassin", "vengeance", "gun-fu"],                7.4, "A retired hitman seeks revenge for his dog."),
    Item(13, "Heat",               1995, ["Action", "Crime", "Drama"],["heist", "cat-and-mouse", "los-angeles"],         8.2, "A detective tracks a master thief."),
    Item(14, "Die Hard",           1988, ["Action", "Thriller"],     ["hostage", "christmas", "one-man-army"],            8.2, "A cop takes on terrorists in a high-rise."),
    Item(15, "Gladiator",          2000, ["Action", "Drama"],        ["ancient-rome", "revenge", "arena"],               8.5, "A betrayed general fights as a gladiator."),
    Item(16, "The Bourne Identity",2002, ["Action", "Thriller"],     ["amnesia", "spy", "on-the-run"],                   7.9, "An amnesiac assassin uncovers his past."),
    Item(17, "Fury Road",          2015, ["Action", "Sci-Fi"],       ["post-apocalyptic", "car-chase", "survival"],        8.1, "A war rig races across the wasteland."),
    Item(18, "Casino Royale",      2006, ["Action", "Adventure"],    ["spy", "poker", "reboot"],                         8.0, "James Bond takes on a terrorist financier."),
    # ── Drama / Emotional ──────────────────────────────────
    Item(19, "The Shawshank Redemption", 1994, ["Drama"],            ["prison", "friendship", "hope"],                   9.3, "A wrongfully convicted man finds hope in prison."),
    Item(20, "Forrest Gump",       1994, ["Drama", "Comedy"],        ["historical", "love-story", "destiny"],             8.8, "A simple man shapes the 20th century."),
    Item(21, "The Pursuit of Happyness",2006,["Drama","Biography"],  ["rags-to-riches", "father-son", "perseverance"],    8.0, "A struggling salesman becomes a stockbroker."),
    Item(22, "Good Will Hunting",  1997, ["Drama"],                   ["genius", "therapy", "self-discovery"],             8.3, "A janitor with a gift for mathematics."),
    Item(23, "The Green Mile",     1999, ["Drama", "Fantasy"],       ["death-row", "supernatural", "compassion"],         8.6, "A prison guard discovers a convict's gift."),
    Item(24, "A Beautiful Mind",   2001, ["Drama", "Biography"],     ["mathematics", "schizophrenia", "nobel"],           8.2, "A mathematician battles mental illness."),
    Item(25, "The Social Network", 2010, ["Drama", "Biography"],     ["facebook", "startup", "betrayal"],                7.8, "The founding story of Facebook."),
    # ── Comedy ─────────────────────────────────────────────
    Item(26, "The Grand Budapest Hotel", 2014, ["Comedy", "Drama"],  ["hotel", "heist", "whimsical"],                    8.1, "A hotel concierge is framed for murder."),
    Item(27, "Superbad",           2007, ["Comedy"],                  ["high-school", "friendship", "party"],              7.6, "Two teens try to buy alcohol for a party."),
    Item(28, "The Hangover",       2009, ["Comedy"],                  ["las-vegas", "bachelor-party", "mystery"],          7.7, "Three friends lose the groom in Vegas."),
    Item(29, "Knives Out",         2019, ["Comedy", "Crime"],        ["whodunit", "detective", "family"],                 7.9, "A detective investigates a family death."),
    Item(30, "Jojo Rabbit",        2019, ["Comedy", "Drama", "War"], ["wwii", "satire", "friendship"],                   7.9, "A Nazi boy discovers his mother is hiding a Jew."),
    # ── Horror / Mystery ───────────────────────────────────
    Item(31, "Get Out",            2017, ["Horror", "Thriller"],     ["social-commentary", "suspense", "twist"],          7.7, "A black man visits his white girlfriend's family."),
    Item(32, "A Quiet Place",      2018, ["Horror", "Drama"],        ["monsters", "silence", "family"],                   7.5, "A family must stay silent to survive."),
    Item(33, "The Sixth Sense",    1999, ["Thriller", "Drama"],      ["ghosts", "twist-ending", "psychology"],            8.1, "A boy who sees dead people."),
    Item(34, "Shutter Island",     2010, ["Thriller", "Mystery"],    ["asylum", "mind-bending", "twist"],                 8.2, "A marshal investigates a disappearance at an asylum."),
    Item(35, "Parasite",           2019, ["Thriller", "Drama", "Comedy"], ["class-struggle", "satire", "twist"],          8.5, "A poor family infiltrates a rich household."),
    # ── Animation / Family ─────────────────────────────────
    Item(36, "Spirited Away",      2001, ["Animation", "Fantasy"],   ["spirit-world", "coming-of-age", "whimsical"],      8.6, "A girl enters a spirit world to save her parents."),
    Item(37, "The Lion King",      1994, ["Animation", "Drama"],     ["coming-of-age", "africa", "family"],               8.5, "A lion cub reclaims his kingdom."),
    Item(38, "Up",                 2009, ["Animation", "Adventure"],  ["old-age", "adventure", "balloons"],                8.3, "An old man flies his house to South America."),
    Item(39, "Coco",               2017, ["Animation", "Music"],     ["day-of-the-dead", "family", "music"],              8.4, "A boy travels to the land of the dead."),
    Item(40, "Into the Spider-Verse", 2018, ["Animation", "Action", "Sci-Fi"], ["superhero", "multiverse", "coming-of-age"], 8.4, "Miles Morales becomes Spider-Man."),
]

# Build lookups
ITEMS_BY_ID: dict[int, Item] = {item.id: item for item in MOVIE_CATALOGUE}
ALL_GENRES: list[str] = sorted({g for item in MOVIE_CATALOGUE for g in item.genres})
ALL_TAGS: list[str] = sorted({t for item in MOVIE_CATALOGUE for t in item.tags})


# ─── Similarity scoring ────────────────────────────────────

def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    all_keys = set(vec_a) | set(vec_b)
    dot = sum(vec_a.get(k, 0.0) * vec_b.get(k, 0.0) for k in all_keys)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _item_genre_vector(item: Item) -> dict[str, float]:
    """One-hot vector: which genres does this item belong to?"""
    return {g: 1.0 for g in item.genres}


def _item_tag_vector(item: Item) -> dict[str, float]:
    """One-hot vector: which tags does this item have?"""
    return {t: 1.0 for t in item.tags}


# ─── Weighted scoring ──────────────────────────────────────

# How much each dimension matters
WEIGHT_GENRE = 0.40
WEIGHT_TAG = 0.30
WEIGHT_ERA = 0.15
WEIGHT_POP = 0.15


def _era_score(item_year: int, user_era_bias: float) -> float:
    """
    Score 0.0 – 1.0 for era fit.
    user_era_bias: -1 = prefers older films, 0 = neutral, +1 = prefers recent
    """
    # Normalise year to 0..1 across the catalogue range (1988 – 2021)
    min_year = 1988
    max_year = 2021
    norm = (item_year - min_year) / (max_year - min_year)  # 0 = oldest, 1 = newest

    if user_era_bias >= 0:
        # Prefers recent or neutral: 0..1 scale, bias shifts threshold
        return 1.0 - abs(norm - user_era_bias)
    else:
        # Prefers older: map negative bias to lower end
        target = 1.0 + user_era_bias  # -1 → 0, -0.5 → 0.5
        return 1.0 - abs(norm - target)


def _pop_score(item_rating: float, user_pop_bias: float) -> float:
    """
    Score 0.0 – 1.0 for popularity fit.
    user_pop_bias: -1 = prefers hidden gems, 0 = neutral, +1 = mainstream hits
    """
    # Normalise rating to 0..1 (assuming ratings 5.0 – 10.0 range)
    norm = max(0.0, min(1.0, (item_rating - 5.0) / 5.0))

    if user_pop_bias >= 0:
        return 1.0 - abs(norm - user_pop_bias)
    else:
        target = 1.0 + user_pop_bias
        return 1.0 - abs(norm - target)


def compute_score(item: Item, profile: UserProfile) -> float:
    """
    Compute a weighted similarity score (0.0 – 1.0) between an item
    and a user profile. Higher = better match.
    """
    if not profile.genre_weights and not profile.tag_weights:
        return 0.0

    score = 0.0

    # Genre similarity
    if profile.genre_weights and WEIGHT_GENRE > 0:
        iv = _item_genre_vector(item)
        genre_sim = cosine_similarity(iv, profile.genre_weights)
        score += WEIGHT_GENRE * genre_sim

    # Tag similarity
    if profile.tag_weights and WEIGHT_TAG > 0:
        tv = _item_tag_vector(item)
        tag_sim = cosine_similarity(tv, profile.tag_weights)
        score += WEIGHT_TAG * tag_sim

    # Era fit
    if WEIGHT_ERA > 0:
        score += WEIGHT_ERA * _era_score(item.year, profile.era_bias)

    # Popularity fit
    if WEIGHT_POP > 0:
        score += WEIGHT_POP * _pop_score(item.avg_rating, profile.pop_bias)

    return round(score, 4)


# ─── Explanation generation ────────────────────────────────

def generate_explanation(
    item: Item, profile: UserProfile, score: float
) -> list[str]:
    """Generate human-readable reasons why this item was recommended."""
    reasons = []

    # Genre match
    matching_genres = [g for g in item.genres if profile.genre_weights.get(g, 0) > 0]
    if matching_genres:
        reasons.append(
            f"You like {matching_genres[0].lower()} "
            f"(and {len(matching_genres) - 1} more)" if len(matching_genres) > 1
            else f"You like {matching_genres[0].lower()}"
        )

    # Tag match
    matching_tags = [t for t in item.tags if profile.tag_weights.get(t, 0) > 0]
    if matching_tags:
        reasons.append(
            f"Tag match: {matching_tags[0]}"
            f" (+{len(matching_tags) - 1} more)" if len(matching_tags) > 1
            else f"Tag match: {matching_tags[0]}"
        )

    # Era explanation
    if profile.era_bias != 0:
        if profile.era_bias > 0 and item.year >= 2015:
            reasons.append("Recent release (you seem to prefer newer films)")
        elif profile.era_bias < 0 and item.year <= 2005:
            reasons.append("Classic film (you seem to prefer older films)")

    # Rating note
    if item.avg_rating >= 8.5:
        reasons.append("Critically acclaimed (avg rating {:.1f})".format(item.avg_rating))

    return reasons if reasons else ["General fit"]


# ─── Profile building ──────────────────────────────────────

def build_profile_from_ratings(
    ratings: dict[int, float]
) -> UserProfile:
    """
    Build a UserProfile from a dict of {item_id: rating} where
    rating is 1-5 (1=dislike, 5=love).
    """
    profile = UserProfile()
    # Deep-copy the ratings
    for item_id, rating in ratings.items():
        profile.rated_items[item_id] = rating

    if not ratings:
        return profile

    genre_scores: dict[str, float] = {}
    tag_scores: dict[str, float] = {}
    total_weight = 0.0
    era_sum = 0.0
    era_count = 0
    pop_sum = 0.0
    pop_count = 0

    for item_id, rating in ratings.items():
        item = ITEMS_BY_ID.get(item_id)
        if item is None:
            continue

        # Convert 1-5 rating to a weight centered at 0:
        #   1 -> -1.0, 2 -> -0.5, 3 -> 0.0, 4 -> +0.5, 5 -> +1.0
        weight = (rating - 3.0) / 2.0
        total_weight += abs(weight)

        # Accumulate genre affinities
        for genre in item.genres:
            genre_scores[genre] = genre_scores.get(genre, 0.0) + weight

        # Accumulate tag affinities
        for tag in item.tags:
            tag_scores[tag] = tag_scores.get(tag, 0.0) + weight

        # Era: positive weight for recent, negative for old
        if weight != 0:
            era_norm = (item.year - 1988) / (2021 - 1988)
            era_sum += (era_norm - 0.5) * 2 * weight  # scale to +/- range
            era_count += 1

        # Popularity: high rating liked = mainstream bias
        if weight != 0:
            pop_norm = (item.avg_rating - 5.0) / 5.0
            pop_sum += (pop_norm - 0.5) * 2 * weight
            pop_count += 1

    # Normalise genre/tag weights
    if total_weight > 0:
        for g in genre_scores:
            genre_scores[g] /= total_weight
        for t in tag_scores:
            tag_scores[t] /= total_weight

    profile.genre_weights = genre_scores
    profile.tag_weights = tag_scores

    if era_count > 0:
        profile.era_bias = max(-1.0, min(1.0, era_sum / era_count))

    if pop_count > 0:
        profile.pop_bias = max(-1.0, min(1.0, pop_sum / pop_count))

    return profile


def build_profile_from_genre_prefs(
    liked_genres: list[str],
    era_pref: str = "any",
    pop_pref: str = "any"
) -> UserProfile:
    """
    Quick profile from genre preferences without rating anything.
    """
    profile = UserProfile()
    for g in liked_genres:
        profile.genre_weights[g] = 1.0

    if era_pref == "classic":
        profile.era_bias = -0.7
    elif era_pref == "recent":
        profile.era_bias = 0.7
    else:
        profile.era_bias = 0.0

    if pop_pref == "hidden":
        profile.pop_bias = -0.7
    elif pop_pref == "mainstream":
        profile.pop_bias = 0.7
    else:
        profile.pop_bias = 0.0

    return profile


# ─── Recommendation engine ─────────────────────────────────

def recommend(
    profile: UserProfile,
    top_n: int = 10,
    exclude_ids: set[int] | None = None
) -> list[dict]:
    """
    Score all items against the profile, return top-N ranked results
    with scores and explanations.
    """
    exclude = exclude_ids or set()
    scored: list[dict] = []

    for item in MOVIE_CATALOGUE:
        if item.id in exclude:
            continue
        score = compute_score(item, profile)
        reasons = generate_explanation(item, profile, score)
        scored.append({
            "item": item,
            "score": score,
            "reasons": reasons,
        })

    # Sort descending by score
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_n]


# ─── Interactive helpers (used by main.py) ─────────────────

def format_item_preview(item: Item, show_id: bool = True) -> str:
    """One-line item summary."""
    genres_str = ", ".join(item.genres)
    prefix = f"[{item.id:>2}] " if show_id else ""
    return (
        f"{prefix}{item.title} ({item.year})  |  {genres_str}  "
        f"|  {item.avg_rating}/10"
    )


def list_all_items() -> None:
    """Print the catalogue grouped by genre."""
    grouped: dict[str, list[Item]] = {}
    for item in MOVIE_CATALOGUE:
        primary = item.genres[0]
        grouped.setdefault(primary, []).append(item)

    print(f"\n  {'=' * 55}")
    print(f"  Movie Catalogue ({len(MOVIE_CATALOGUE)} titles)")
    print(f"  {'=' * 55}")
    for genre in sorted(grouped):
        print(f"\n  [{genre}]")
        for item in grouped[genre]:
            print(f"    {format_item_preview(item)}")
    print()
