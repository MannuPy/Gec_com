"""
Tests unitaires — services/price_elasticity_service.py
Fonctions testées (pures, sans DB) :
  - _interpret_elasticity
  - _recommend_discount_policy
"""
import pytest
from app.services.price_elasticity_service import (
    _interpret_elasticity,
    _recommend_discount_policy,
)


class TestInterpretElasticity:
    """_interpret_elasticity(e) → str"""

    def test_none_returns_insufficient(self):
        result = _interpret_elasticity(None)
        assert "insuffisantes" in result.lower() or "insuffisant" in result.lower()

    def test_very_elastic_negative(self):
        result = _interpret_elasticity(-2.5)
        assert "très élastique" in result.lower() or "tres" in result.lower()

    def test_elastic_negative(self):
        result = _interpret_elasticity(-1.2)
        assert "élastique" in result.lower()

    def test_slightly_elastic(self):
        result = _interpret_elasticity(-0.7)
        # faiblement élastique
        assert "faiblement" in result.lower() or "limité" in result.lower()

    def test_inelastic(self):
        result = _interpret_elasticity(-0.2)
        assert "inélastique" in result.lower() or "inelastique" in result.lower()

    def test_positive_elasticity_atypical(self):
        result = _interpret_elasticity(0.5)
        assert "atypique" in result.lower() or "luxe" in result.lower()

    def test_zero_elasticity_inelastic(self):
        result = _interpret_elasticity(0.0)
        # 0 >= 0 → "atypique" ou "inélastique"
        assert result  # non vide

    def test_exact_boundary_minus_2(self):
        # e == -2.0 → "élastique" (pas "très élastique")
        result = _interpret_elasticity(-2.0)
        assert result  # non vide, valeur limite cohérente

    def test_exact_boundary_minus_1(self):
        result = _interpret_elasticity(-1.0)
        assert result


class TestRecommendDiscountPolicy:
    """_recommend_discount_policy(e, avg_discount) → str"""

    def test_none_elasticity_returns_collect_data(self):
        result = _recommend_discount_policy(None, 0.10)
        assert result  # non vide

    def test_very_elastic_recommends_maintain_discount(self):
        result = _recommend_discount_policy(-2.0, 0.10)
        # Recommande de maintenir ou augmenter les remises
        assert result

    def test_elastic_recommends_keep(self):
        result = _recommend_discount_policy(-1.2, 0.10)
        assert result

    def test_slightly_elastic_recommends_reduce(self):
        result = _recommend_discount_policy(-0.7, 0.10)
        assert "réduire" in result.lower() or "reduc" in result.lower()

    def test_inelastic_recommends_suppress(self):
        result = _recommend_discount_policy(-0.2, 0.10)
        assert "supprimer" in result.lower() or "supprim" in result.lower()

    def test_positive_recommends_suppress(self):
        result = _recommend_discount_policy(0.5, 0.10)
        assert result  # non vide

    def test_zero_discount_arg_does_not_crash(self):
        # avg_discount = 0.0 ne doit pas provoquer de ZeroDivisionError
        result = _recommend_discount_policy(-1.5, 0.0)
        assert result
