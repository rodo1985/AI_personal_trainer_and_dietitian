"""Nutrition lookup service with explicit match confidence handling."""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.app.models.schemas import NutritionTotals


@dataclass(frozen=True)
class CatalogFood:
    """Canonical nutrition record used by lookup matching.

    Attributes:
        canonical_name: Canonical label returned to clients.
        aliases: Alias strings recognized in free text.
        per_serving: Nutrition values for one serving.
    """

    canonical_name: str
    aliases: tuple[str, ...]
    per_serving: NutritionTotals


@dataclass
class NutritionLookupResult:
    """Result of matching one free-text food fragment.

    Attributes:
        canonical_name: Matched food name when available.
        quantity_text: Quantity text extracted from user input.
        servings: Serving multiplier used for nutrition totals.
        matched: Whether a confident catalog match was found.
        confidence: Confidence score for the selected match.
        nutrition: Item nutrition totals when matched.
        unresolved_reason: Why lookup could not return a safe match.
        assumptions: Assumptions made during quantity parsing.
        warnings: Warnings for ambiguous matching or unsupported text.
    """

    canonical_name: str | None
    quantity_text: str | None
    servings: float | None
    matched: bool
    confidence: float | None
    nutrition: NutritionTotals | None
    unresolved_reason: str | None
    assumptions: list[str]
    warnings: list[str]


class NutritionLookupService:
    """Match food text fragments against a small nutrition catalog.

    The catalog is intentionally compact in v1. Unmatched foods are surfaced
    to the user to prevent false precision in daily totals.

    Example:
        >>> service = NutritionLookupService()
        >>> result = service.lookup("2 eggs")
        >>> result.matched
        True
    """

    _catalog: tuple[CatalogFood, ...] = (
        CatalogFood(
            canonical_name="oats",
            aliases=("oats", "oatmeal"),
            per_serving=NutritionTotals(calories=154, protein_g=5.0, carbs_g=27.0, fat_g=3.0),
        ),
        CatalogFood(
            canonical_name="banana",
            aliases=("banana",),
            per_serving=NutritionTotals(calories=105, protein_g=1.3, carbs_g=27.0, fat_g=0.3),
        ),
        CatalogFood(
            canonical_name="greek yogurt",
            aliases=("greek yogurt", "yogurt", "yoghurt"),
            per_serving=NutritionTotals(calories=120, protein_g=17.0, carbs_g=6.0, fat_g=2.0),
        ),
        CatalogFood(
            canonical_name="eggs",
            aliases=("egg", "eggs"),
            per_serving=NutritionTotals(calories=78, protein_g=6.0, carbs_g=0.6, fat_g=5.0),
        ),
        CatalogFood(
            canonical_name="rice",
            aliases=("rice",),
            per_serving=NutritionTotals(calories=205, protein_g=4.3, carbs_g=45.0, fat_g=0.4),
        ),
        CatalogFood(
            canonical_name="chicken breast",
            aliases=("chicken", "chicken breast"),
            per_serving=NutritionTotals(calories=165, protein_g=31.0, carbs_g=0.0, fat_g=3.6),
        ),
        CatalogFood(
            canonical_name="salmon",
            aliases=("salmon",),
            per_serving=NutritionTotals(calories=208, protein_g=20.0, carbs_g=0.0, fat_g=13.0),
        ),
        CatalogFood(
            canonical_name="whole wheat bread",
            aliases=("whole wheat bread", "bread", "toast"),
            per_serving=NutritionTotals(calories=90, protein_g=4.0, carbs_g=17.0, fat_g=1.2),
        ),
        CatalogFood(
            canonical_name="avocado",
            aliases=("avocado",),
            per_serving=NutritionTotals(calories=160, protein_g=2.0, carbs_g=9.0, fat_g=15.0),
        ),
        CatalogFood(
            canonical_name="apple",
            aliases=("apple",),
            per_serving=NutritionTotals(calories=95, protein_g=0.5, carbs_g=25.0, fat_g=0.3),
        ),
    )

    def lookup(self, fragment: str) -> NutritionLookupResult:
        """Match one fragment and return transparent nutrition metadata.

        Parameters:
            fragment: Free-text fragment, usually one parsed food item.

        Returns:
            NutritionLookupResult: Match metadata and optional totals.

        Example:
            >>> service = NutritionLookupService()
            >>> service.lookup("banana").canonical_name
            'banana'
        """

        normalized_fragment = _normalize_text(fragment)
        servings, quantity_text, quantity_assumptions = _extract_servings(fragment)

        candidates: list[tuple[CatalogFood, float]] = []
        for food in self._catalog:
            for alias in food.aliases:
                alias_normalized = _normalize_text(alias)
                if normalized_fragment == alias_normalized:
                    candidates.append((food, 1.0))
                    continue
                if f" {alias_normalized} " in f" {normalized_fragment} ":
                    # Longer alias matches are usually less ambiguous than short alias
                    # matches (for example, "bread" vs "whole wheat bread").
                    score = 0.74 + min(len(alias_normalized) / 100, 0.2)
                    candidates.append((food, score))

        if not candidates:
            return NutritionLookupResult(
                canonical_name=None,
                quantity_text=quantity_text,
                servings=servings,
                matched=False,
                confidence=None,
                nutrition=None,
                unresolved_reason=(
                    "No catalog nutrition match found. Confirm manually before save."
                ),
                assumptions=quantity_assumptions,
                warnings=[
                    "Nutrition totals exclude this item because no reliable match was found."
                ],
            )

        # Keep the highest confidence match but refuse near-ties to avoid silent mistakes.
        candidates.sort(key=lambda item: item[1], reverse=True)
        top_food, top_score = candidates[0]
        if len(candidates) > 1 and (top_score - candidates[1][1]) < 0.08:
            return NutritionLookupResult(
                canonical_name=None,
                quantity_text=quantity_text,
                servings=servings,
                matched=False,
                confidence=top_score,
                nutrition=None,
                unresolved_reason=(
                    "Multiple nutrition matches are similarly likely. Choose one manually."
                ),
                assumptions=quantity_assumptions,
                warnings=[
                    "Ambiguous nutrition match; this item was excluded from totals."
                ],
            )

        multiplier = servings if servings is not None else 1.0
        nutrition = _scale_totals(top_food.per_serving, multiplier)
        return NutritionLookupResult(
            canonical_name=top_food.canonical_name,
            quantity_text=quantity_text,
            servings=multiplier,
            matched=True,
            confidence=top_score,
            nutrition=nutrition,
            unresolved_reason=None,
            assumptions=quantity_assumptions,
            warnings=[],
        )


def _normalize_text(value: str) -> str:
    """Normalize free text to simplify matching comparisons.

    Parameters:
        value: Original free-text value.

    Returns:
        str: Lower-cased, punctuation-stripped value.

    Example:
        >>> _normalize_text(" Greek Yogurt! ")
        'greek yogurt'
    """

    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", value.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _extract_servings(fragment: str) -> tuple[float | None, str | None, list[str]]:
    """Extract a serving multiplier and quantity hint from a fragment.

    Parameters:
        fragment: Raw free-text food fragment.

    Returns:
        tuple[float | None, str | None, list[str]]: Parsed servings, quantity text,
            and assumptions generated during parsing.

    Example:
        >>> _extract_servings("2 eggs")[0]
        2.0
    """

    lowered = fragment.lower()

    # Handle common textual fractions before generic numeric parsing.
    if "half" in lowered:
        return 0.5, "half", ["Interpreted 'half' as 0.5 serving."]
    if "quarter" in lowered:
        return 0.25, "quarter", ["Interpreted 'quarter' as 0.25 serving."]

    number_match = re.search(r"\b(\d+(?:\.\d+)?)\b", lowered)
    if number_match:
        parsed = float(number_match.group(1))
        return parsed, number_match.group(1), []

    return 1.0, None, ["No explicit quantity found; assumed 1 serving."]


def _scale_totals(totals: NutritionTotals, multiplier: float) -> NutritionTotals:
    """Scale nutrition totals by a serving multiplier.

    Parameters:
        totals: Base nutrition values per serving.
        multiplier: Serving multiplier to apply.

    Returns:
        NutritionTotals: Scaled totals rounded to two decimals.

    Example:
        >>> _scale_totals(
        ...     NutritionTotals(calories=100, protein_g=10, carbs_g=0, fat_g=2),
        ...     2,
        ... ).calories
        200.0
    """

    return NutritionTotals(
        calories=round(totals.calories * multiplier, 2),
        protein_g=round(totals.protein_g * multiplier, 2),
        carbs_g=round(totals.carbs_g * multiplier, 2),
        fat_g=round(totals.fat_g * multiplier, 2),
    )
