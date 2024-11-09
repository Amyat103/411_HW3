import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal


@pytest.fixture()
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()


@pytest.fixture
def mock_update_meal_stats(mocker):
    """Mock the update_meal_stats function for testing purposes."""
    return mocker.patch("meal_max.models.battle_model.update_meal_stats")


"""Fixtures providing sample meals for the tests."""


@pytest.fixture
def sample_meal1():
    """Fixture providing a sample meal for the tests."""
    return Meal(1, "Sushi", "Japanese", 15.0, "HIGH")


@pytest.fixture
def sample_meal2():
    """Fixture providing a sample meal for the tests."""
    return Meal(2, "Burger", "American", 8.0, "LOW")


@pytest.fixture
def sample_battle(sample_meal1, sample_meal2):
    return [sample_meal1, sample_meal2]


##################################################
# Add battle Management Test Cases
##################################################


def test_prep_combatant(battle_model, sample_meal1):
    """Test adding a meal to the battle."""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].id == 1


def test_battle(battle_model, sample_battle, mock_update_meal_stats):
    """Test running a battle and updating stats."""
    for meal in sample_battle:
        battle_model.prep_combatant(meal)

    winner = battle_model.battle()
    assert winner in [meal.meal for meal in sample_battle]
    assert mock_update_meal_stats.call_count == 2


def test_get_battle_score(battle_model, sample_meal1):
    """Test battle score calculation."""
    score = battle_model.get_battle_score(sample_meal1)
    difficulty_modifier = {"HIGH": 1, "MED": 2, "LOW": 3}
    expected_score = (
        sample_meal1.price * len(sample_meal1.cuisine)
    ) - difficulty_modifier[sample_meal1.difficulty]
    assert score == expected_score


def test_clear_combatants(battle_model, sample_meal1):
    """Test clearing all combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0


def test_get_combatants(battle_model, sample_meal1):
    """Test getting the list of combatants."""
    battle_model.prep_combatant(sample_meal1)
    result = battle_model.get_combatants()
    assert result == battle_model.combatants
