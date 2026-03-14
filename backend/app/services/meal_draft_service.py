"""Meal draft generation logic used by assistant endpoints."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from backend.app.schemas import AssistantDraft, FoodItem, MealDraftPayload, MealSlot


@dataclass(frozen=True)
class NutritionProfile:
    """Per-serving macro profile for a known food item.

    Parameters:
        calories: Calories per serving.
        protein_g: Protein grams per serving.
        carbs_g: Carbohydrate grams per serving.
        fat_g: Fat grams per serving.

    Returns:
        NutritionProfile: Immutable nutrition profile.

    Raises:
        TypeError: If invalid types are passed to dataclass fields.

    Example:
        >>> NutritionProfile(calories=105, protein_g=1.3, carbs_g=27, fat_g=0.3)
    """

    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


NUTRITION_LOOKUP: dict[str, NutritionProfile] = {
    "banana": NutritionProfile(calories=105, protein_g=1.3, carbs_g=27, fat_g=0.3),
    "oats": NutritionProfile(calories=150, protein_g=5.0, carbs_g=27, fat_g=3.0),
    "yogurt": NutritionProfile(calories=120, protein_g=10.0, carbs_g=15, fat_g=2.5),
    "eggs": NutritionProfile(calories=140, protein_g=12.0, carbs_g=1.1, fat_g=10.0),
    "chicken": NutritionProfile(calories=231, protein_g=43.0, carbs_g=0.0, fat_g=5.0),
    "rice": NutritionProfile(calories=205, protein_g=4.3, carbs_g=45, fat_g=0.4),
    "salad": NutritionProfile(calories=60, protein_g=2.0, carbs_g=8.0, fat_g=2.5),
    "protein shake": NutritionProfile(calories=160, protein_g=30.0, carbs_g=6.0, fat_g=2.0),
    "toast": NutritionProfile(calories=80, protein_g=3.0, carbs_g=14.0, fat_g=1.0),
    "apple": NutritionProfile(calories=95, protein_g=0.5, carbs_g=25.0, fat_g=0.3),
}

SLOT_KEYWORDS: dict[MealSlot, tuple[str, ...]] = {
    "breakfast": ("breakfast", "morning"),
    "lunch": ("lunch", "midday"),
    "dinner": ("dinner", "supper", "evening"),
    "snacks": ("snack", "snacks"),
}


def build_meal_draft(source_text: str, meal_slot_hint: MealSlot | None = None) -> AssistantDraft:
    """Convert free text into a structured meal draft with uncertainty metadata.

    Parameters:
        source_text: Natural language meal note provided by the user.
        meal_slot_hint: Optional slot hint from the UI selection.

    Returns:
        AssistantDraft: Structured meal payload with assumptions and warnings.

    Raises:
        ValueError: If the input source text is empty after trimming whitespace.

    Example:
        >>> build_meal_draft("breakfast oats with banana", "breakfast").draft_type
        'meal'
    """

    cleaned_text = source_text.strip()
    if not cleaned_text:
        raise ValueError("Meal draft text cannot be empty.")

    detected_slot = detect_meal_slot(cleaned_text)
    meal_slot = meal_slot_hint or detected_slot or "snacks"

    raw_item_segments = split_food_segments(cleaned_text)
    food_items, assumptions, warnings = parse_food_items(raw_item_segments)
    totals = calculate_totals(food_items)

    missing_quantities = [item for item in food_items if item.quantity_text == "1 serving"]
    if missing_quantities:
        assumptions.append(
            "Items without a quantity were estimated as one serving, "
            "so totals are review-only until confirmed."
        )

    confidence = derive_confidence(food_items=food_items, warnings=warnings)
    confirm_before_save = bool(warnings or missing_quantities)

    payload = MealDraftPayload(
        meal_slot=meal_slot,
        source_text=cleaned_text,
        items=food_items,
        calories=totals.calories,
        protein_g=totals.protein_g,
        carbs_g=totals.carbs_g,
        fat_g=totals.fat_g,
        confidence=confidence,
        status="needs_review" if confirm_before_save else "confirmed",
    )

    return AssistantDraft(
        normalized_payload=payload,
        assumptions=dedupe_preserving_order(assumptions),
        warnings=dedupe_preserving_order(warnings),
        confirm_before_save=confirm_before_save,
    )


def detect_meal_slot(source_text: str) -> MealSlot | None:
    """Infer a meal slot from source text keywords.

    Parameters:
        source_text: Natural language meal description.

    Returns:
        MealSlot | None: Detected slot, or ``None`` when no keyword matches.

    Raises:
        None.

    Example:
        >>> detect_meal_slot("Lunch: rice and chicken")
        'lunch'
    """

    lowered = source_text.lower()
    for slot, keywords in SLOT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return slot
    return None


def split_food_segments(source_text: str) -> list[str]:
    """Split a free-text meal description into item-like segments.

    Parameters:
        source_text: Natural language meal description.

    Returns:
        list[str]: Candidate food segments extracted from the text.

    Raises:
        None.

    Example:
        >>> split_food_segments("oats, banana and yogurt")
        ['oats', 'banana', 'yogurt']
    """

    working_text = source_text

    # Strip leading meal labels so they do not become fake food items.
    working_text = re.sub(
        r"^(breakfast|lunch|dinner|snack|snacks)\s*:\s*",
        "",
        working_text,
        flags=re.I,
    )

    segments = re.split(r",|\band\b|\+", working_text, flags=re.I)
    return [segment.strip() for segment in segments if segment.strip()]


def parse_food_items(segments: Iterable[str]) -> tuple[list[FoodItem], list[str], list[str]]:
    """Parse food segments into normalized ``FoodItem`` objects.

    Parameters:
        segments: Iterable of text segments representing candidate food items.

    Returns:
        tuple[list[FoodItem], list[str], list[str]]: Parsed items, assumptions, and warnings.

    Raises:
        None.

    Example:
        >>> parse_food_items(["1 banana"])[0][0].name
        'banana'
    """

    assumptions: list[str] = []
    warnings: list[str] = []
    parsed_items: list[FoodItem] = []

    for segment in segments:
        quantity_multiplier, quantity_text = extract_quantity(segment)
        canonical_name = canonicalize_food_name(segment)
        profile = NUTRITION_LOOKUP.get(canonical_name)

        if profile is None:
            warnings.append(
                f"No nutrition match found for '{canonical_name}'. "
                "Confirm or edit before saving totals."
            )
            parsed_items.append(
                FoodItem(
                    name=canonical_name,
                    quantity_text=quantity_text,
                    matched=False,
                )
            )
            continue

        assumptions.append(
            f"Nutrition for '{canonical_name}' used a generic serving "
            "profile from the local reference table."
        )
        parsed_items.append(
            FoodItem(
                name=canonical_name,
                quantity_text=quantity_text,
                matched=True,
                calories=round(profile.calories * quantity_multiplier, 2),
                protein_g=round(profile.protein_g * quantity_multiplier, 2),
                carbs_g=round(profile.carbs_g * quantity_multiplier, 2),
                fat_g=round(profile.fat_g * quantity_multiplier, 2),
            )
        )

    if not parsed_items:
        warnings.append("No food items were parsed from the provided text.")

    return parsed_items, assumptions, warnings


def extract_quantity(segment: str) -> tuple[float, str]:
    """Extract a numeric quantity hint from one food segment.

    Parameters:
        segment: Candidate food segment text.

    Returns:
        tuple[float, str]: Quantity multiplier and human-readable quantity text.

    Raises:
        None.

    Example:
        >>> extract_quantity("2 eggs")
        (2.0, '2')
    """

    match = re.search(r"(\d+(?:\.\d+)?)", segment)
    if match:
        raw_quantity = match.group(1)
        return float(raw_quantity), raw_quantity

    return 1.0, "1 serving"


def canonicalize_food_name(segment: str) -> str:
    """Normalize raw segment text to a lookup-friendly food key.

    Parameters:
        segment: Raw food segment that may include quantities and punctuation.

    Returns:
        str: Lowercased canonical food phrase.

    Raises:
        None.

    Example:
        >>> canonicalize_food_name("2x Protein Shake")
        'protein shake'
    """

    lowered = segment.lower()
    without_numbers = re.sub(r"\d+(?:\.\d+)?", "", lowered)
    normalized = re.sub(r"[^a-z\s]", " ", without_numbers)
    collapsed = re.sub(r"\s+", " ", normalized).strip()

    # Map common singular/plural mismatches to one canonical reference key.
    if collapsed.endswith(" egg"):
        return "eggs"
    if collapsed.endswith(" apples"):
        return "apple"

    return collapsed or "unknown item"


def derive_confidence(food_items: list[FoodItem], warnings: list[str]) -> float:
    """Derive a bounded confidence score based on data completeness.

    Parameters:
        food_items: Parsed food items from the draft pipeline.
        warnings: Warning messages raised during parsing.

    Returns:
        float: Confidence score clamped to ``0`` through ``1``.

    Raises:
        None.

    Example:
        >>> derive_confidence([FoodItem(name="banana", quantity_text="1", matched=True)], [])
        0.95
    """

    if not food_items:
        return 0.2

    matched_items = sum(1 for item in food_items if item.matched)
    matched_ratio = matched_items / len(food_items)

    confidence = 0.55 + (0.4 * matched_ratio) - (0.08 * len(warnings))
    return round(max(0.0, min(1.0, confidence)), 2)


def dedupe_preserving_order(values: Iterable[str]) -> list[str]:
    """Return a list with duplicates removed while preserving insertion order.

    Parameters:
        values: Iterable of strings that may contain duplicates.

    Returns:
        list[str]: Stable de-duplicated list.

    Raises:
        None.

    Example:
        >>> dedupe_preserving_order(["a", "a", "b"])
        ['a', 'b']
    """

    seen: set[str] = set()
    output: list[str] = []

    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)

    return output


@dataclass(frozen=True)
class NutritionTotals:
    """Aggregate macronutrient totals for one meal payload.

    Parameters:
        calories: Total calories.
        protein_g: Total protein grams.
        carbs_g: Total carbohydrate grams.
        fat_g: Total fat grams.

    Returns:
        NutritionTotals: Immutable total values.

    Raises:
        TypeError: If invalid field types are passed.

    Example:
        >>> NutritionTotals(calories=100, protein_g=10, carbs_g=10, fat_g=2)
    """

    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


def calculate_totals(items: list[FoodItem]) -> NutritionTotals:
    """Sum nutrition totals from matched food items.

    Parameters:
        items: Parsed food items that may include unmatched rows.

    Returns:
        NutritionTotals: Summed calories and macronutrients.

    Raises:
        None.

    Example:
        >>> calculate_totals([
        ...     FoodItem(
        ...         name="banana",
        ...         quantity_text="1",
        ...         matched=True,
        ...         calories=100,
        ...         protein_g=1,
        ...         carbs_g=20,
        ...         fat_g=1,
        ...     )
        ... ]).calories
        100.0
    """

    return NutritionTotals(
        calories=round(sum(item.calories or 0 for item in items), 2),
        protein_g=round(sum(item.protein_g or 0 for item in items), 2),
        carbs_g=round(sum(item.carbs_g or 0 for item in items), 2),
        fat_g=round(sum(item.fat_g or 0 for item in items), 2),
    )
