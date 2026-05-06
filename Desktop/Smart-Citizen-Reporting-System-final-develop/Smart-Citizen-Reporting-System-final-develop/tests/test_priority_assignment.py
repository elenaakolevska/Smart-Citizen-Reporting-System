from __future__ import annotations

from app.services.ai_service import assign_priority


def test_fire_maps_to_iten() -> None:
    assert assign_priority("Има пожар во зградата", []) == "Итен"


def test_flood_maps_to_iten() -> None:
    assert assign_priority("Голема поплава на улицата", []) == "Итен"


def test_opasno_maps_to_iten() -> None:
    assert assign_priority("Објектот е опасно оштетен", []) == "Итен"


def test_emergency_maps_to_iten() -> None:
    assert assign_priority("This is an emergency near the school", []) == "Итен"


def test_hazard_maps_to_visok() -> None:
    assert assign_priority("Постои опасност за пешаците", []) == "Висок"


def test_nebezbedno_maps_to_visok() -> None:
    assert assign_priority("Скалите се небезбедно нестабилни", []) == "Висок"


def test_damaged_road_maps_to_sreden() -> None:
    assert assign_priority("Оштетен пат во населба", []) == "Среден"


def test_minor_problem_maps_to_nizok() -> None:
    assert assign_priority("Незначителен проблем со ознака", []) == "Низок"


def test_cosmetic_issue_maps_to_nizok() -> None:
    assert assign_priority("Cosmetic slight damage on the bench", []) == "Низок"


def test_history_boost_increases_priority_by_one_level() -> None:
    history = [
        "Истата улица имаше пожар и експлозија минатата недела",
        "Друга пријава без ризик",
    ]
    assert assign_priority("Оштетен пат на истата улица", history) == "Висок"
