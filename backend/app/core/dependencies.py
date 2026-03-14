"""FastAPI dependency providers for settings, services, and repositories."""

from __future__ import annotations

from fastapi import Depends

from backend.app.core.config import Settings
from backend.app.core.database import Database
from backend.app.repositories.day_log_repository import DayLogRepository
from backend.app.services.ai_client import AIClientProtocol, build_ai_client
from backend.app.services.draft_pipeline import MealDraftService
from backend.app.services.nutrition import NutritionLookupService
from backend.app.services.upload_storage import LocalUploadStorage


def get_settings() -> Settings:
    """Load settings from current environment variables.

    Returns:
        Settings: Runtime settings object.

    Example:
        >>> isinstance(get_settings(), Settings)
        True
    """

    return Settings.from_env()


def get_database(settings: Settings = Depends(get_settings)) -> Database:
    """Create and initialize a database helper for current request context.

    Parameters:
        settings: Injected runtime settings.

    Returns:
        Database: Initialized database helper.

    Example:
        >>> db = get_database(Settings.from_env())
        >>> isinstance(db, Database)
        True
    """

    database = Database(settings.database_path)
    database.initialize()
    return database


def get_day_log_repository(database: Database = Depends(get_database)) -> DayLogRepository:
    """Build repository for day-log persistence and aggregate reads.

    Parameters:
        database: Injected initialized database helper.

    Returns:
        DayLogRepository: Persistence repository instance.

    Example:
        >>> isinstance(get_day_log_repository(get_database(Settings.from_env())), DayLogRepository)
        True
    """

    return DayLogRepository(database)


def get_nutrition_lookup_service() -> NutritionLookupService:
    """Create nutrition lookup service used during meal draft parsing.

    Returns:
        NutritionLookupService: Nutrition matching service.

    Example:
        >>> isinstance(get_nutrition_lookup_service(), NutritionLookupService)
        True
    """

    return NutritionLookupService()


def get_ai_client(settings: Settings = Depends(get_settings)) -> AIClientProtocol:
    """Create the configured AI client implementation.

    Parameters:
        settings: Injected runtime settings.

    Returns:
        AIClientProtocol: OpenAI-backed or fallback AI client.

    Example:
        >>> client = get_ai_client(Settings.from_env())
        >>> hasattr(client, "transcribe_audio")
        True
    """

    return build_ai_client(settings)


def get_meal_draft_service(
    nutrition_lookup: NutritionLookupService = Depends(get_nutrition_lookup_service),
    ai_client: AIClientProtocol = Depends(get_ai_client),
) -> MealDraftService:
    """Build draft service combining nutrition matching and AI hints.

    Parameters:
        nutrition_lookup: Injected nutrition lookup service.
        ai_client: Injected AI client.

    Returns:
        MealDraftService: Draft pipeline service.

    Example:
        >>> service = get_meal_draft_service(
        ...     get_nutrition_lookup_service(),
        ...     get_ai_client(Settings.from_env()),
        ... )
        >>> isinstance(service, MealDraftService)
        True
    """

    return MealDraftService(nutrition_lookup=nutrition_lookup, ai_client=ai_client)


def get_upload_storage(settings: Settings = Depends(get_settings)) -> LocalUploadStorage:
    """Create local upload storage service for glucose screenshots.

    Parameters:
        settings: Injected runtime settings.

    Returns:
        LocalUploadStorage: Filesystem storage service.

    Example:
        >>> storage = get_upload_storage(Settings.from_env())
        >>> isinstance(storage, LocalUploadStorage)
        True
    """

    return LocalUploadStorage(settings.upload_dir)
