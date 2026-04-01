"""
services/price_service.py — Danish Market Price Abstraction

Architecture decision:
  PriceService defines a clean interface. The mock implementation
  returns hard-coded Danish grocery averages for ~50 common ingredients.
  
  Future integrations (e.g. Salling Group API, Coop API) plug in as
  concrete subclasses without touching calling code.

Usage:
    from app.services.price_service import get_price_service
    svc = get_price_service()
    price = svc.get_price("mælk")  # → 12.5 (DKK per liter)
"""
from abc import ABC, abstractmethod
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AbstractPriceService(ABC):
    @abstractmethod
    def get_price(self, ingredient_name: str) -> float | None:
        """
        Return price in DKK per base unit, or None if unknown.
        """
        raise NotImplementedError


class MockDanishPriceService(AbstractPriceService):
    """
    Mock prices based on typical Danish supermarket averages (2024).
    Prices are per standard unit (liter, kg, piece, etc.)
    """

    # ingredient_name (lowercase) → (price_dkk, unit)
    PRICE_TABLE: dict[str, tuple[float, str]] = {
        # Mejeri
        "mælk": (12.5, "liter"),
        "smør": (25.0, "250g"),
        "fløde": (18.0, "liter"),
        "creme fraiche": (15.0, "200ml"),
        "ost": (80.0, "kg"),
        "æggehvider": (20.0, "liter"),
        "æg": (3.5, "stk"),
        "yoghurt": (22.0, "kg"),
        # Kød
        "kyllingebryst": (95.0, "kg"),
        "hakket oksekød": (75.0, "kg"),
        "svinekød": (65.0, "kg"),
        "bacon": (50.0, "200g"),
        "laks": (120.0, "kg"),
        "torsk": (100.0, "kg"),
        "rejer": (180.0, "kg"),
        # Grøntsager
        "løg": (10.0, "kg"),
        "hvidløg": (15.0, "kg"),
        "tomater": (25.0, "kg"),
        "gulerødder": (12.0, "kg"),
        "kartofler": (8.0, "kg"),
        "broccoli": (20.0, "kg"),
        "spinat": (25.0, "kg"),
        "agurk": (8.0, "stk"),
        "peberfrugt": (10.0, "stk"),
        "champignoner": (20.0, "kg"),
        "courgette": (15.0, "kg"),
        # Frugt
        "bananer": (15.0, "kg"),
        "æbler": (20.0, "kg"),
        "appelsiner": (18.0, "kg"),
        "citroner": (5.0, "stk"),
        # Kornprodukter
        "pasta": (12.0, "500g"),
        "ris": (15.0, "kg"),
        "brød": (22.0, "stk"),
        "mel": (8.0, "kg"),
        "havregryn": (12.0, "kg"),
        # Dåse / tørvarer
        "dåsetomater": (12.0, "400g"),
        "kokosmælk": (15.0, "400ml"),
        "kikærter": (10.0, "400g"),
        "linser": (18.0, "kg"),
        "sort bønner": (10.0, "400g"),
        # Krydderier / olier
        "olivenolie": (60.0, "liter"),
        "solsikkeolie": (25.0, "liter"),
        "salt": (5.0, "kg"),
        "peber": (30.0, "kg"),
        "stødt kanel": (25.0, "50g"),
        "paprika": (25.0, "50g"),
        "spidskommen": (25.0, "50g"),
        # Saucer / bouillon
        "sojasauce": (20.0, "250ml"),
        "bouillon": (15.0, "liter"),
        # Sukkervarer
        "sukker": (10.0, "kg"),
        "honning": (45.0, "500g"),
        "chokolade": (25.0, "100g"),
    }

    def get_price(self, ingredient_name: str) -> float | None:
        key = ingredient_name.strip().lower()
        if key in self.PRICE_TABLE:
            price, unit = self.PRICE_TABLE[key]
            logger.debug(f"PriceService: {ingredient_name} → {price} DKK/{unit}")
            return price
        # Partial match fallback
        for table_key, (price, unit) in self.PRICE_TABLE.items():
            if table_key in key or key in table_key:
                logger.debug(f"PriceService (fuzzy): {ingredient_name} → {price} DKK/{unit} via '{table_key}'")
                return price
        logger.warning(f"PriceService: no price for '{ingredient_name}'")
        return None

    def get_price_with_unit(self, ingredient_name: str) -> tuple[float, str] | None:
        key = ingredient_name.strip().lower()
        return self.PRICE_TABLE.get(key)


# Singleton — swap class here to change implementation globally
_service_instance = None


def get_price_service() -> AbstractPriceService:
    global _service_instance
    if _service_instance is None:
        _service_instance = MockDanishPriceService()
    return _service_instance


def refresh_ingredient_prices(app_context_db):
    """
    Utility: updates all Ingredient.price_dkk_per_unit from PriceService.
    Call from a scheduled job or manually from settings.
    """
    from app.models import Ingredient
    svc = get_price_service()
    updated = 0
    for ingredient in Ingredient.query.all():
        price = svc.get_price(ingredient.name)
        if price is not None:
            ingredient.price_dkk_per_unit = price
            ingredient.price_updated_at = datetime.utcnow()
            updated += 1
    app_context_db.session.commit()
    logger.info(f"PriceService: refreshed {updated} ingredient prices")
    return updated
