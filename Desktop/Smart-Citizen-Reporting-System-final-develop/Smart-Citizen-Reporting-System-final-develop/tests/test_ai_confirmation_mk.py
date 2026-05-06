"""
Tests for generate_confirmation_mk()

Tests cover:
  - Fallback template output for 5+ report types
  - Priority translation (known + unknown + None)
  - Duplicate flag inclusion
  - AI disabled path
  - HF API failure graceful fallback
  - No crash on empty/None inputs
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.ai_service import _mk_fallback, _priority_to_mk, generate_confirmation_mk


# ---------------------------------------------------------------------------
# _priority_to_mk — unit tests

class TestPriorityTranslation:
    def test_low(self):
        assert _priority_to_mk("low") == "низок"

    def test_medium(self):
        assert _priority_to_mk("medium") == "среден"

    def test_high(self):
        assert _priority_to_mk("high") == "висок"

    def test_urgent(self):
        assert _priority_to_mk("urgent") == "итен"

    def test_critical(self):
        assert _priority_to_mk("critical") == "критичен"

    def test_case_insensitive(self):
        assert _priority_to_mk("HIGH") == "висок"
        assert _priority_to_mk("Medium") == "среден"

    def test_unknown_returns_none(self):
        assert _priority_to_mk("superurgent") is None

    def test_none_returns_none(self):
        assert _priority_to_mk(None) is None


# ---------------------------------------------------------------------------
# _mk_fallback — 5 report type scenarios

class TestMkFallback:
    """Verify fallback template covers all required fields for each report type."""

    def test_infrastructure_high_priority(self):
        text = _mk_fallback(
            category_label="Infrastructure",
            priority="high",
            possible_duplicate_of=None,
        )
        assert "примена" in text
        assert "Infrastructure" in text
        assert "висок" in text
        assert "3–5 работни дена" in text

    def test_communal_medium_priority(self):
        text = _mk_fallback(
            category_label="Communal Services",
            priority="medium",
            possible_duplicate_of=None,
        )
        assert "Communal Services" in text
        assert "среден" in text

    def test_safety_urgent_with_duplicate(self):
        text = _mk_fallback(
            category_label="Safety",
            priority="urgent",
            possible_duplicate_of=42,
        )
        assert "Safety" in text
        assert "итен" in text
        assert "#42" in text

    def test_environment_low_priority(self):
        text = _mk_fallback(
            category_label="Environment",
            priority="low",
            possible_duplicate_of=None,
        )
        assert "Environment" in text
        assert "низок" in text

    def test_other_no_priority_no_category(self):
        """Fallback still produces valid Macedonian text with no info at all."""
        text = _mk_fallback(
            category_label=None,
            priority=None,
            possible_duplicate_of=None,
        )
        assert "примена" in text
        assert "3–5 работни дена" in text
        # No stray format placeholders left in the string
        assert "{" not in text

    def test_unknown_priority_shown_raw(self):
        """Unknown priority values are shown as-is rather than dropped."""
        text = _mk_fallback(
            category_label="Roads",
            priority="superurgent",
            possible_duplicate_of=None,
        )
        assert "superurgent" in text

    def test_no_duplicate_section_when_not_flagged(self):
        text = _mk_fallback("Roads", "high", possible_duplicate_of=None)
        assert "дупликат" not in text


# ---------------------------------------------------------------------------
# generate_confirmation_mk — integration paths

class TestGenerateConfirmationMk:

    def test_ai_disabled_returns_fallback(self):
        mock_settings = MagicMock()
        mock_settings.ai_enabled = False

        with patch("app.services.ai_service.get_settings", return_value=mock_settings):
            result = generate_confirmation_mk(
                "Дупка на улица Партизанска.",
                category_label="Infrastructure",
                priority="high",
            )
        assert "примена" in result
        assert "Infrastructure" in result
        assert "висок" in result

    def test_hf_api_success_returns_generated_text(self):
        mock_settings = MagicMock()
        mock_settings.ai_enabled = True
        mock_settings.hf_api_token = None
        mock_settings.ai_hf_inference_model = "mistralai/Mistral-7B-Instruct-v0.2"
        mock_settings.ai_hf_inference_timeout_seconds = 30

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"generated_text": "Вашата пријава е примена. Категорија: Инфраструктура со висок приоритет."}
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.ai_service.get_settings", return_value=mock_settings), \
             patch("app.services.ai_service._requests.post", return_value=mock_response):
            result = generate_confirmation_mk(
                "Дупка на улица.",
                category_label="Infrastructure",
                priority="high",
            )

        assert "примена" in result
        assert "Инфраструктура" in result

    def test_hf_api_failure_returns_fallback(self):
        mock_settings = MagicMock()
        mock_settings.ai_enabled = True
        mock_settings.hf_api_token = None
        mock_settings.ai_hf_inference_model = "mistralai/Mistral-7B-Instruct-v0.2"
        mock_settings.ai_hf_inference_timeout_seconds = 30

        with patch("app.services.ai_service.get_settings", return_value=mock_settings), \
             patch("app.services.ai_service._requests.post", side_effect=ConnectionError("timeout")):
            result = generate_confirmation_mk(
                "Скршена улична ламба.",
                category_label="Safety",
                priority="urgent",
            )

        # Must not crash; must return valid Macedonian fallback
        assert "примена" in result
        assert isinstance(result, str)
        assert len(result) > 20

    def test_hf_empty_response_returns_fallback(self):
        mock_settings = MagicMock()
        mock_settings.ai_enabled = True
        mock_settings.hf_api_token = None
        mock_settings.ai_hf_inference_model = "mistralai/Mistral-7B-Instruct-v0.2"
        mock_settings.ai_hf_inference_timeout_seconds = 30

        mock_response = MagicMock()
        mock_response.json.return_value = [{"generated_text": ""}]
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.ai_service.get_settings", return_value=mock_settings), \
             patch("app.services.ai_service._requests.post", return_value=mock_response):
            result = generate_confirmation_mk("Расфрлан отпад.", category_label="Environment", priority="low")

        assert "примена" in result

    def test_no_priority_no_category_no_crash(self):
        """Must never crash even with all-None optional params."""
        mock_settings = MagicMock()
        mock_settings.ai_enabled = False

        with patch("app.services.ai_service.get_settings", return_value=mock_settings):
            result = generate_confirmation_mk("Некој проблем.")

        assert isinstance(result, str)
        assert len(result) > 0