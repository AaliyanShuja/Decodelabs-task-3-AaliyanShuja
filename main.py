"""
Project 3: AI Recommendation Logic
DecodeLabs Industrial Training Kit -- Batch 2026

A content-based recommendation engine that:
  * Builds a preference profile from user input
  * Scores items by multi-dimensional similarity (genres, tags, era, popularity)
  * Explains WHY each item was recommended
  * Learns from feedback and re-ranks

Key Skills: Logic building, pattern matching, recommendation concepts
"""

from recommender import (
    MOVIE_CATALOGUE,
    ITEMS_BY_ID,
    build_profile_from_ratings,
    build_profile_from_genre_prefs,
    recommend,
    format_item_preview,
    list_all_items,
    UserProfile,
)

HR = "=" * 60
DASH = "-" * 60


# ─── Menu helpers ──────────────────────────────────────────

def print_header(title: str) -> None:
    print(f"\n{HR}")
    print(f"  {title}")
    print(HR)


def print_step(step: str) -> None:
    print(f"\n  >> {step}")
    print(f"  {DASH}")


def get_choice(prompt: str, valid: set[str], default: str | None = None) -> str:
    """Get a validated input from the user."""
    while True:
        try:
            raw = input(f"  {prompt} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "q"
        if not raw and default is not None:
            return default
        if raw in valid:
            return raw
        print(f"  [!] Please enter one of: {', '.join(sorted(valid))}")


def get_int(prompt: str, min_v: int, max_v: int) -> int | None:
    """Get an integer input within range, or None if quit."""
    while True:
        try:
            raw = input(f"  {prompt} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if raw.lower() in ("q", "quit", "exit"):
            return None
        try:
            val = int(raw)
            if min_v <= val <= max_v:
                return val
            print(f"  [!] Enter a number between {min_v} and {max_v}")
        except ValueError:
            print(f"  [!] Enter a number, please")


# ─── Phase 1: Preference Onboarding ───────────────────────

def phase_explore_catalogue() -> None:
    """Show the full catalogue so the user knows what's available."""
    list_all_items()
    input("  Press Enter to continue...")


def phase_rate_items() -> dict[int, float]:
    """
    Let the user rate some movies to build their profile.
    Returns {item_id: rating}.
    """
    ratings: dict[int, float] = {}

    print_step("Rate some movies to build your preference profile")
    print("  Rate from 1 (hate) to 5 (love), or 0 to skip.")
    print("  Type 'q' at any prompt to finish.\n")

    shown = 0
    for item in MOVIE_CATALOGUE:
        if shown >= 8:
            extra = input("  Rate more? (y/n): ").strip().lower()
            if extra != "y":
                break
            shown = 0

        print(f"  {format_item_preview(item)}")
        val = get_int(f"Your rating (1-5, 0=skip, q=done):", 0, 5)
        if val is None:
            break
        if val > 0:
            ratings[item.id] = float(val)

        shown += 1

    print(f"\n  You rated {len(ratings)} movies.")
    return ratings


def phase_genre_pick() -> UserProfile:
    """Quick profile from genre preferences (faster onboarding)."""
    print_step("Pick your favourite genres")

    # Show available genres
    from recommender import ALL_GENRES
    for i, g in enumerate(ALL_GENRES, 1):
        print(f"    {i:>2}. {g}")

    print("  Enter genre numbers separated by spaces (e.g. '1 3 5'),")
    print("  or 'all' to include everything.")

    raw = input("  Your choice: ").strip()
    if raw.lower() == "all":
        liked = ALL_GENRES
    else:
        indices = [int(x) for x in raw.split() if x.isdigit()]
        liked = [ALL_GENRES[i - 1] for i in indices if 1 <= i <= len(ALL_GENRES)]

    if not liked:
        print("  No genres selected. Using 'Sci-Fi' as default.")
        liked = ["Sci-Fi"]

    # Era preference
    era = get_choice(
        "Era preference? (c)lassic, (r)ecent, or (a)ny [a]:",
        {"c", "r", "a", "classic", "recent", "any"},
        "a",
    )
    era_map = {"c": "classic", "classic": "classic",
               "r": "recent", "recent": "recent"}

    # Popularity preference
    pop = get_choice(
        "Popularity? (h)idden-gems, (m)ainstream, or (a)ny [a]:",
        {"h", "m", "a", "hidden", "mainstream", "any"},
        "a",
    )
    pop_map = {"h": "hidden", "hidden": "hidden",
               "m": "mainstream", "mainstream": "mainstream"}

    era_val = era_map.get(era, "any")
    pop_val = pop_map.get(pop, "any")

    profile = build_profile_from_genre_prefs(liked, era_val, pop_val)

    print(f"\n  Profile built! Liked genres: {', '.join(liked)}")
    if era_val != "any":
        print(f"  Era bias: {era_val}")
    if pop_val != "any":
        print(f"  Popularity bias: {pop_val}")

    return profile


# ─── Phase 2: Show Recommendations ────────────────────────

def show_recommendations(
    profile: UserProfile,
    top_n: int = 8,
    exclude: set[int] | None = None
) -> list[dict]:
    """Display ranked recommendations. Returns the result list."""
    results = recommend(profile, top_n=top_n, exclude_ids=exclude)

    if not results:
        print("  No recommendations available. Try rating more items!")
        return []

    print_step(f"Top {len(results)} Recommendations for You")

    for i, r in enumerate(results, 1):
        item = r["item"]
        score_pct = r["score"] * 100
        print(f"\n  {i:>2}. {item.title} ({item.year})")
        print(f"      Score:  {score_pct:.1f}%  |  Rating: {item.avg_rating}/10")
        print(f"      Genre:  {', '.join(item.genres)}")
        if r["reasons"]:
            for reason in r["reasons"][:3]:
                print(f"      Why:    {reason}")
        print(f"      {item.description}")

    return results


# ─── Phase 3: Feedback & Refine ───────────────────────────

def phase_feedback_loop(profile: UserProfile) -> UserProfile:
    """
    Let the user rate recommendations, rebuild profile, and re-rank.
    """
    seen: set[int] = set(profile.rated_items.keys())
    rounds = 0

    while rounds < 3:
        results = recommend(profile, top_n=6, exclude_ids=seen)
        if not results:
            break

        print_step(f"Refinement Round {rounds + 1}")

        for i, r in enumerate(results, 1):
            item = r["item"]
            print(f"\n  {i}. {item.title} ({item.year})  [score: {r['score']*100:.0f}%]")

        print("\n  Rate these recommendations (1-5, 0=skip, q=done):")
        new_ratings: dict[int, float] = {}
        for r in results:
            item = r["item"]
            val = get_int(f"    {item.title[:40]:<40} rating:", 0, 5)
            if val is None:
                break
            if val > 0:
                new_ratings[item.id] = float(val)
                seen.add(item.id)

        if not new_ratings:
            print("  No new ratings. Done refining.")
            break

        # Merge into profile and rebuild
        merged = dict(profile.rated_items)
        merged.update(new_ratings)
        profile = build_profile_from_ratings(merged)

        # Show updated recommendations
        print_step("Updated recommendations based on your feedback")
        updated = recommend(profile, top_n=5, exclude_ids=seen)
        for r in updated:
            item = r["item"]
            print(f"    {item.title:<45} score: {r['score']*100:.1f}%")

        rounds += 1

    return profile


# ─── Phase 4: Compare Profiles ────────────────────────────

def phase_compare() -> None:
    """Build two different profiles and compare their recommendations."""
    print_step("Profile Comparison")
    print("  First, build Profile A:\n")
    profile_a = phase_genre_pick()

    print("\n  Now build Profile B:\n")
    profile_b = phase_genre_pick()

    print_step("Comparing recommendations")

    recs_a = recommend(profile_a, top_n=5)
    recs_b = recommend(profile_b, top_n=5)

    print(f"\n  {'Profile A':<50} {'Profile B':<50}")
    print(f"  {'-'*49} {'-'*49}")

    for i in range(5):
        title_a = recs_a[i]["item"].title if i < len(recs_a) else ""
        score_a = recs_a[i]["score"] * 100 if i < len(recs_a) else 0
        title_b = recs_b[i]["item"].title if i < len(recs_b) else ""
        score_b = recs_b[i]["score"] * 100 if i < len(recs_b) else 0
        print(f"  {f'{title_a} ({score_a:.0f}%)':<50} {f'{title_b} ({score_b:.0f}%)':<50}")

    # Cross-over: what does A think of B's top?
    print(f"\n  Cross check: How well does Profile A's #1 match Profile B?")
    top_a = recs_a[0]["item"]
    top_b = recs_b[0]["item"]

    from recommender import compute_score
    cross_a = compute_score(top_a, profile_b) * 100
    cross_b = compute_score(top_b, profile_a) * 100

    print(f"    A's top ({top_a.title}) for B:  {cross_a:.0f}%")
    print(f"    B's top ({top_b.title}) for A:  {cross_b:.0f}%")

    input("\n  Press Enter to continue...")


# ─── Main Menu ─────────────────────────────────────────────

def main() -> None:
    print(HR)
    print("  Project 3: AI Recommendation Logic")
    print("  DecodeLabs Industrial Training Kit 2026")
    print(HR)

    profile: UserProfile | None = None

    while True:
        print(f"\n{DASH}")
        print("  MAIN MENU")
        print(DASH)
        print("    1. Quick start -- pick genres, get recs")
        print("    2. Rate movies -- build detailed profile")
        print("    3. Browse catalogue")
        print("    4. Compare two profiles")
        print("    5. Refine with feedback (after step 1 or 2)")
        print("    6. Show recommendations")
        print("")
        print("    q. Quit")

        choice = get_choice("What would you like to do?", {"1", "2", "3", "4", "5", "6", "q"})

        if choice == "q":
            break

        elif choice == "1":
            profile = phase_genre_pick()
            show_recommendations(profile)

        elif choice == "2":
            ratings = phase_rate_items()
            if ratings:
                profile = build_profile_from_ratings(ratings)
                print("\n  Profile built from your ratings!")
                show_recommendations(profile)
            else:
                print("  No ratings given. Try again!")

        elif choice == "3":
            phase_explore_catalogue()

        elif choice == "4":
            phase_compare()

        elif choice == "5":
            if profile is None:
                print("  No profile yet! Choose option 1 or 2 first.")
            else:
                print_step("Feedback-based refinement")
                print("  Rate the recommendations to teach the engine what you like.")
                profile = phase_feedback_loop(profile)

        elif choice == "6":
            if profile is None:
                print("  No profile yet! Choose option 1 or 2 first.")
            else:
                show_recommendations(profile, top_n=10)

    print(f"\n{HR}")
    print("  Thanks for using the Recommendation Engine!")
    print("  DecodeLabs Industrial Training Kit 2026")
    print(HR)


if __name__ == "__main__":
    main()
