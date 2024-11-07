import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal

@pytest.fixture()
def battle_model():
    """Fixture to provide a new instance of PlaylistModel for each test."""
    return BattleModel()

@pytest.fixture
def mock_update_play_count(mocker):
    """Mock the update_meal_stats function for testing purposes."""
    return mocker.patch("meal_max.models.battle_model.update_meal_stats")

"""Fixtures providing sample songs for the tests."""
@pytest.fixture
def sample_meal1():
    return Meal(1, 'Sushi', 15.0, "Japanese", "HIGH")

@pytest.fixture
def sample_meal2():
    return Meal(2, 'Burger', 8.0, "American", "LOW")

@pytest.fixture
def sample_battle(sample_meal1, sample_meal2):
    return [sample_meal1, sample_meal2]

def test_prep_combatant(battle_model, sample_battle):

    battle_model.combatants.extend(sample_battle)

    assert len(battle_model.combatant) == 2
    assert battle_model.combatants[0].id == 1
    assert battle_model.combatants[1].id == 2 

    # Test error on adding a third combatant
    meal_3 = Meal(2, 'Taco', 8.0, "Mexican", "MED")
    with pytest.raises(ValueError):
        battle_model.prep_combatant(meal_3)


def test_battle(battle_model, sample_battle, mock_update_meal_stats):
    # Add two combatants to the battle
    battle_model.combatants.extend(sample_battle)

    # Rn the battle
    winner = battle_model.battle()

    # Assert the winner is one of the combatants
    assert winner in [meal.meal for meal in sample_battle]

    # Verify 'update_meal_stats' was called for both winner and loser
    assert mock_update_meal_stats.call_count == 2

    # Verify only the winner should remain
    assert len(battle_model.combatants) == 1 

    # Assert that the remaining combatant is the one who won
    assert battle_model.combatants[0].meal == winner

def test_get_battle_score(battle_model, sample_meal1):
    # Create a sample combatant meal
    meal = battle_model.combatants.extend(sample_meal1)

    # Expected score calculation
    difficulty_modifier = {"HIGH": 1, "MED": 2, "LOW": 3}
    expected_score = (meal.price * len(meal.cuisine)) - difficulty_modifier[meal.difficulty]

    score = battle_model.get_battle_score(meal)

    # Assert that the score is as expected
    assert score == expected_score, f"Expected score {expected_score}, but got {score}"

def test_clear_combatants(battle_model, sample_battle):
    # Set up combatants in the battle model
    battle_model.combatants.extend(sample_battle)

    # Ensure combatants list is not empty
    assert len(battle_model.combatants) == 2

    # Call clear_combatants and check if the list is empty
    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0

def test_get_combatants(battle_model, sample_battle):
    # Set up combatants in the battle model
    combatants = battle_model.combatants.extend(sample_battle)

    # Retrieve the combatants using get_combatants 
    result = battle_model.get_combatants()

    # Verify the result matches the combatants list
    assert result == combatants

