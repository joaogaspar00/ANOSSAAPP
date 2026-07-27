"""
services/price_service.py — Grocery Price Abstraction

Architecture decision:
  PriceService defines a clean interface. The mock implementation
  returns hard-coded Portuguese supermarket averages for ~50 common ingredients.

  Future integrations (e.g. Continente, Pingo Doce APIs) plug in as
  concrete subclasses without touching calling code.

Usage:
    from app.services.price_service import get_price_service
    svc = get_price_service()
    price = svc.get_price("leite")  # → 0.9 (EUR per liter)
"""
from abc import ABC, abstractmethod
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AbstractPriceService(ABC):
    @abstractmethod
    def get_price(self, ingredient_name: str) -> float | None:
        """
        Return price in EUR per base unit, or None if unknown.
        """
        raise NotImplementedError


class MockPriceService(AbstractPriceService):
    """
    Mock prices based on typical Portuguese supermarket averages (2024).
    Prices are per standard unit (litro, kg, unidade, etc.)
    """

    # ingredient_name (lowercase) → (price_eur, unit)
    PRICE_TABLE: dict[str, tuple[float, str]] = {
        # Lacticínios
        "leite": (0.9, "litro"),
        "manteiga": (2.5, "250g"),
        "natas": (1.2, "200ml"),
        "queijo": (9.0, "kg"),
        "claras de ovo": (3.0, "litro"),
        "ovos": (0.25, "un"),
        "iogurte": (2.5, "kg"),
        # Carne
        "peito de frango": (7.5, "kg"),
        "carne picada": (6.5, "kg"),
        "carne de porco": (6.0, "kg"),
        "bacon": (4.0, "200g"),
        "salmão": (14.0, "kg"),
        "bacalhau": (12.0, "kg"),
        "camarão": (16.0, "kg"),
        # Vegetais
        "cebola": (1.0, "kg"),
        "alho": (3.0, "kg"),
        "tomate": (2.0, "kg"),
        "cenoura": (1.0, "kg"),
        "batata": (0.8, "kg"),
        "brócolos": (2.0, "kg"),
        "espinafres": (2.5, "kg"),
        "pepino": (0.8, "un"),
        "pimento": (1.0, "un"),
        "cogumelos": (3.0, "kg"),
        "courgette": (1.5, "kg"),
        # Fruta
        "banana": (1.4, "kg"),
        "maçã": (1.6, "kg"),
        "laranja": (1.3, "kg"),
        "limão": (0.4, "un"),
        # Cereais
        "massa": (1.0, "500g"),
        "arroz": (1.3, "kg"),
        "pão": (1.5, "un"),
        "farinha": (0.8, "kg"),
        "aveia": (1.5, "kg"),
        # Conservas / secos
        "tomate pelado": (0.9, "400g"),
        "leite de coco": (1.5, "400ml"),
        "grão-de-bico": (0.9, "400g"),
        "lentilhas": (2.0, "kg"),
        "feijão preto": (0.9, "400g"),
        # Especiarias / óleos
        "azeite": (6.0, "litro"),
        "óleo de girassol": (2.0, "litro"),
        "sal": (0.6, "kg"),
        "pimenta": (4.0, "kg"),
        "canela em pó": (2.5, "50g"),
        "colorau": (2.0, "50g"),
        "cominhos": (2.5, "50g"),
        # Molhos / caldos
        "molho de soja": (2.0, "250ml"),
        "caldo": (2.0, "litro"),
        # Doces
        "açúcar": (1.2, "kg"),
        "mel": (5.0, "500g"),
        "chocolate": (2.0, "100g"),
    }

    def get_price(self, ingredient_name: str) -> float | None:
        key = ingredient_name.strip().lower()
        if key in self.PRICE_TABLE:
            price, unit = self.PRICE_TABLE[key]
            logger.debug(f"PriceService: {ingredient_name} → {price} EUR/{unit}")
            return price
        # Partial match fallback
        for table_key, (price, unit) in self.PRICE_TABLE.items():
            if table_key in key or key in table_key:
                logger.debug(f"PriceService (fuzzy): {ingredient_name} → {price} EUR/{unit} via '{table_key}'")
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
        _service_instance = MockPriceService()
    return _service_instance


def refresh_ingredient_prices(app_context_db):
    """
    Utility: updates all Ingredient.price_per_unit from PriceService.
    Call from a scheduled job or manually from settings.
    """
    from app.models import Ingredient
    svc = get_price_service()
    updated = 0
    for ingredient in Ingredient.query.all():
        price = svc.get_price(ingredient.name)
        if price is not None:
            ingredient.price_per_unit = price
            ingredient.price_updated_at = datetime.utcnow()
            updated += 1
    app_context_db.session.commit()
    logger.info(f"PriceService: refreshed {updated} ingredient prices")
    return updated
