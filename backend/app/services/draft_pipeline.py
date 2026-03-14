"""Meal draft pipeline for typed and transcribed input text."""

from __future__ import annotations

import re

from backend.app.models.schemas import (
    AssistantDraft,
    DraftFoodItem,
    MealDraftPayload,
    MealSlot,
    NutritionTotals,
)
from backend.app.services.ai_client import AIClientProtocol
from backend.app.services.nutrition import NutritionLookupService


class MealDraftService:
    """Build normalized assistant drafts from free text or transcript text.

    Parameters:
        nutrition_lookup: Service used for nutrition matching and totals.
        ai_client: AI client used for optional structured hints.

    Example:
        >>> service = MealDraftService(NutritionLookupService(), _NoOpAIClient())
        >>> draft = service.build_draft("breakfast: oats and banana")
        >>> draft.draft_type
        'meal'
    """

    def __init__(
        self,
        nutrition_lookup: NutritionLookupService,
        ai_client: AIClientProtocol,
    ) -> None:
        """Store service dependencies used for draft generation.

        Parameters:
            nutrition_lookup: Nutrition lookup dependency.
            ai_client: AI client dependency.

        Returns:
            None.
        """

        self._nutrition_lookup = nutrition_lookup
        self._ai_client = ai_client

    def build_draft(self, text: str, source: str = "typed") -> AssistantDraft:
        """Convert source text into a previewable meal draft.

        Parameters:
            text: Source text entered by user or generated from transcription.
            source: Source identifier (`typed` or `transcript`).

        Returns:
            AssistantDraft: Normalized draft payload plus assumptions and warnings.

        Raises:
            ValueError: If text is blank after trimming.

        Example:
            >>> service = MealDraftService(NutritionLookupService(), _NoOpAIClient())
            >>> service.build_draft("lunch: chicken and rice").normalized_payload.meal_slot
            <MealSlot.LUNCH: 'lunch'>
        """

        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Draft text cannot be empty.")

        assumptions: list[str] = []
        warnings: list[str] = []
        confirm_before_save = False

        ai_hint = self._ai_client.extract_meal_structure(cleaned_text)
        if ai_hint:
            assumptions.extend(ai_hint.assumptions)
            warnings.extend(ai_hint.warnings)

        meal_slot, meal_body, slot_assumptions, slot_warnings = _detect_meal_slot_and_body(
            cleaned_text
        )
        assumptions.extend(slot_assumptions)
        warnings.extend(slot_warnings)

        if meal_slot is None and ai_hint and ai_hint.meal_slot:
            meal_slot = ai_hint.meal_slot
            assumptions.append("Meal slot inferred by AI because no slot was explicit in text.")

        item_candidates = _split_food_candidates(meal_body)
        if ai_hint and ai_hint.food_items:
            # AI extraction may preserve item boundaries better for run-on sentences.
            item_candidates = ai_hint.food_items

        parsed_items: list[DraftFoodItem] = []
        for candidate in item_candidates:
            lookup_result = self._nutrition_lookup.lookup(candidate)
            parsed_items.append(
                DraftFoodItem(
                    raw_text=candidate,
                    canonical_name=lookup_result.canonical_name,
                    quantity=lookup_result.quantity_text,
                    estimated_servings=lookup_result.servings,
                    matched=lookup_result.matched,
                    match_confidence=lookup_result.confidence,
                    nutrition=lookup_result.nutrition,
                    unresolved_reason=lookup_result.unresolved_reason,
                )
            )
            assumptions.extend(lookup_result.assumptions)
            warnings.extend(lookup_result.warnings)
            if not lookup_result.matched:
                confirm_before_save = True

        if meal_slot is None:
            warnings.append(
                "Meal slot is missing. Choose breakfast/lunch/dinner/snacks before saving."
            )
            confirm_before_save = True

        if source == "transcript":
            assumptions.append(
                "Draft is based on transcript text. "
                "Confirm wording in case transcription is imperfect."
            )

        totals = _calculate_totals(parsed_items)

        if _estimate_confidence(parsed_items) < 0.75:
            warnings.append(
                "Draft confidence is low due to unresolved or weak nutrition matches."
            )
            confirm_before_save = True

        normalized_payload = MealDraftPayload(
            meal_slot=meal_slot,
            source_text=cleaned_text,
            items=parsed_items,
            totals=totals,
        )

        return AssistantDraft(
            normalized_payload=normalized_payload,
            assumptions=_deduplicate_preserve_order(assumptions),
            warnings=_deduplicate_preserve_order(warnings),
            confirm_before_save=confirm_before_save,
        )


def estimate_draft_confidence(draft: AssistantDraft) -> float:
    """Compute aggregate confidence score for a generated meal draft.

    Parameters:
        draft: Assistant draft generated by `MealDraftService`.

    Returns:
        float: Confidence score in range 0-1.

    Example:
        >>> draft = AssistantDraft(
        ...     normalized_payload=MealDraftPayload(source_text="x"),
        ...     assumptions=[],
        ...     warnings=[],
        ... )
        >>> 0 <= estimate_draft_confidence(draft) <= 1
        True
    """

    return _estimate_confidence(draft.normalized_payload.items)


def _detect_meal_slot_and_body(
    text: str,
) -> tuple[MealSlot | None, str, list[str], list[str]]:
    """Extract meal slot and body text from free text.

    Parameters:
        text: Raw input text.

    Returns:
        tuple[MealSlot | None, str, list[str], list[str]]: Meal slot, body text,
            assumptions, and warnings.

    Example:
        >>> _detect_meal_slot_and_body("breakfast: oats")[0]
        <MealSlot.BREAKFAST: 'breakfast'>
    """

    pattern = re.compile(r"^(breakfast|lunch|dinner|snack|snacks)\s*[:\-]\s*(.+)$", re.IGNORECASE)
    match = pattern.match(text.strip())
    if not match:
        return None, text, [], ["Could not detect meal slot from text prefix."]

    slot_text = match.group(1).lower()
    body = match.group(2).strip()
    slot = MealSlot.SNACKS if slot_text.startswith("snack") else MealSlot(slot_text)
    return slot, body, [], []


def _split_food_candidates(text: str) -> list[str]:
    """Split meal body text into candidate food fragments.

    Parameters:
        text: Meal body text after removing slot prefix.

    Returns:
        list[str]: Candidate food fragments.

    Example:
        >>> _split_food_candidates("oats, banana and yogurt")
        ['oats', 'banana', 'yogurt']
    """

    normalized = re.sub(r"\band\b", ",", text, flags=re.IGNORECASE)
    chunks = [chunk.strip() for chunk in re.split(r"[,;]", normalized) if chunk.strip()]
    return chunks or [text.strip()]


def _calculate_totals(items: list[DraftFoodItem]) -> NutritionTotals:
    """Aggregate totals from matched food items only.

    Parameters:
        items: Parsed food items from draft generation.

    Returns:
        NutritionTotals: Summed totals for matched items.

    Example:
        >>> _calculate_totals([]).calories
        0.0
    """

    calories = 0.0
    protein = 0.0
    carbs = 0.0
    fat = 0.0

    for item in items:
        if item.nutrition is None:
            # Unmatched items are intentionally excluded from totals so the API
            # never presents false precision.
            continue
        calories += item.nutrition.calories
        protein += item.nutrition.protein_g
        carbs += item.nutrition.carbs_g
        fat += item.nutrition.fat_g

    return NutritionTotals(
        calories=round(calories, 2),
        protein_g=round(protein, 2),
        carbs_g=round(carbs, 2),
        fat_g=round(fat, 2),
    )


def _estimate_confidence(items: list[DraftFoodItem]) -> float:
    """Estimate overall draft confidence from item-level match quality.

    Parameters:
        items: Parsed draft food items.

    Returns:
        float: Confidence score between 0 and 1.

    Example:
        >>> _estimate_confidence([])
        0.0
    """

    if not items:
        return 0.0

    weighted = 0.0
    for item in items:
        if not item.matched:
            weighted += 0.0
            continue
        weighted += item.match_confidence if item.match_confidence is not None else 0.7

    return round(weighted / len(items), 2)


def _deduplicate_preserve_order(values: list[str]) -> list[str]:
    """Remove duplicates while preserving first-seen order.

    Parameters:
        values: List with potential duplicate strings.

    Returns:
        list[str]: Deduplicated list.

    Example:
        >>> _deduplicate_preserve_order(["a", "b", "a"])
        ['a', 'b']
    """

    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


class _NoOpAIClient:
    """Tiny test-only helper used in doctest examples for this module."""

    def extract_meal_structure(self, text: str):
        """Return no hint for doctest examples.

        Parameters:
            text: Input text.

        Returns:
            None: Always returns no hint.
        """

        return None
