import re
import sqlite3
from contextlib import contextmanager

import pytest

from meal_max.models.kitchen_model import (
    Meal,
    clear_meals,
    create_meal,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats,
)

######################################################
#
#    Fixtures
#
######################################################


def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r"\s+", " ", sql_query).strip()


# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch(
        "meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection
    )

    return mock_cursor  # Return the mock cursor so we can set expectations per test


######################################################
#
#    Add and delete
#
######################################################


def test_create_meal(mock_cursor):
    """Test creating a new meal in the catalog."""

    # Call the function to create a new meal
    create_meal(
        meal="Meal Name", cuisine="Cuisine Country", price=10.0, difficulty="MED"
    )

    expected_query = normalize_whitespace(
        """
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """
    )

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert (
        actual_query == expected_query
    ), "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal Name", "Cuisine Country", 10.0, "MED")
    assert (
        actual_arguments == expected_arguments
    ), f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate name (should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError

    # Expect the function to raise a ValueError
    with pytest.raises(ValueError, match="Meal with name 'Meal Name' already exists"):
        create_meal(
            meal="Meal Name", cuisine="Cuisine Country", price=10.0, difficulty="MED"
        )


def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an invalid price."""

    # Attempt to create a meal with a negative price
    with pytest.raises(
        ValueError, match="Invalid price: -10.0. Price must be a positive number."
    ):
        create_meal(
            meal="Meal Name", cuisine="Cuisine Country", price=-10.0, difficulty="MED"
        )


def test_create_meal_invalid_difficulty():
    """Test error when trying to create a meal with an invalid difficulty."""

    with pytest.raises(
        ValueError,
        match="Invalid difficulty level: HARD. Must be 'LOW', 'MED', or 'HIGH'.",
    ):
        create_meal(
            meal="Meal Name", cuisine="Cuisine Country", price=10.0, difficulty="HARD"
        )


def test_delete_meal(mock_cursor):
    """Test soft deleting a meal from the catalog by meal ID."""

    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the delete_meal function
    delete_meal(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace(
        "UPDATE meals SET deleted = TRUE WHERE id = ?"
    )

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(
        mock_cursor.execute.call_args_list[0][0][0]
    )
    actual_update_sql = normalize_whitespace(
        mock_cursor.execute.call_args_list[1][0][0]
    )

    # Ensure the correct SQL queries were executed
    assert (
        actual_select_sql == expected_select_sql
    ), "The SELECT query did not match the expected structure."
    assert (
        actual_update_sql == expected_update_sql
    ), "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args
    assert actual_update_args == expected_update_args


def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)


def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = [True]

    # Expect a ValueError when attempting to delete a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has been deleted"):
        delete_meal(999)


def test_clear_meals(mock_cursor, mocker):
    """Test clearing the entire meals list."""

    # Mock the file reading
    mocker.patch.dict(
        "os.environ", {"SQL_CREATE_TABLE_PATH": "sql/create_meal_table.sql"}
    )
    mock_open = mocker.patch(
        "builtins.open", mocker.mock_open(read_data="The body of the create statement")
    )

    # Call the clear_meals function
    clear_meals()

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()


######################################################
#
#    Get Meal
#
######################################################


def test_get_meal_by_id(mock_cursor):
    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = (
        1,
        "Meal Name",
        "Cuisine Country",
        10.0,
        "MED",
        False,
    )

    # Call the function and check the result
    result = get_meal_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine Country", 10.0, "MED")
    assert result == expected_result


def test_get_meal_by_id_bad_id(mock_cursor):
    # Simulate that no meal exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)


def test_get_meal_by_name(mock_cursor):
    # Simulate that the meal exists
    mock_cursor.fetchone.return_value = (
        1,
        "Meal Name",
        "Cuisine Country",
        10.0,
        "MED",
        False,
    )

    # Call the function and check the result
    result = get_meal_by_name("Meal Name")

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine Country", 10.0, "MED")
    assert result == expected_result


def test_get_leaderboard_ordered_by_wins(mock_cursor):
    """Test retrieving all meals ordered by wins."""

    # Mocked database response in compact format
    mock_cursor.fetchall.return_value = [
        (3, "Meal C", "Cuisine C", 30.0, "HIGH", 20, 10, 0.50),
        (2, "Meal B", "Cuisine B", 20.0, "MED", 10, 5, 0.50),
        (1, "Meal A", "Cuisine A", 10.0, "LOW", 5, 3, 0.60),
    ]

    meals = get_leaderboard(sort_by="wins")

    # Expected result format in dictionary form for easier assertion
    expected_result = [
        {
            "id": 3,
            "meal": "Meal C",
            "cuisine": "Cuisine C",
            "price": 30.0,
            "difficulty": "HIGH",
            "battles": 20,
            "wins": 10,
            "win_pct": 50.0,
        },
        {
            "id": 2,
            "meal": "Meal B",
            "cuisine": "Cuisine B",
            "price": 20.0,
            "difficulty": "MED",
            "battles": 10,
            "wins": 5,
            "win_pct": 50.0,
        },
        {
            "id": 1,
            "meal": "Meal A",
            "cuisine": "Cuisine A",
            "price": 10.0,
            "difficulty": "LOW",
            "battles": 5,
            "wins": 3,
            "win_pct": 60.0,
        },
    ]

    # Assert the meals result matches the expected result
    assert meals == expected_result, f"Expected {expected_result}, but got {meals}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace(
        """
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0
        ORDER BY wins DESC
    """
    )
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert (
        actual_query == expected_query
    ), f"Expected query {expected_query}, but got {actual_query}"


def test_get_leaderboard_ordered_by_win_pct(mock_cursor):
    """Test retrieving all meals ordered by win percentage."""
    mock_cursor.fetchall.return_value = [
        (1, "Meal A", "Cuisine A", 10.0, "LOW", 5, 3, 0.60),
        (3, "Meal C", "Cuisine C", 30.0, "HIGH", 20, 10, 0.50),
        (2, "Meal B", "Cuisine B", 20.0, "MED", 10, 5, 0.50),
    ]

    meals = get_leaderboard(sort_by="win_pct")

    expected_result = [
        {
            "id": 1,
            "meal": "Meal A",
            "cuisine": "Cuisine A",
            "price": 10.0,
            "difficulty": "LOW",
            "battles": 5,
            "wins": 3,
            "win_pct": 60.0,
        },
        {
            "id": 3,
            "meal": "Meal C",
            "cuisine": "Cuisine C",
            "price": 30.0,
            "difficulty": "HIGH",
            "battles": 20,
            "wins": 10,
            "win_pct": 50.0,
        },
        {
            "id": 2,
            "meal": "Meal B",
            "cuisine": "Cuisine B",
            "price": 20.0,
            "difficulty": "MED",
            "battles": 10,
            "wins": 5,
            "win_pct": 50.0,
        },
    ]

    assert meals == expected_result, f"Expected {expected_result}, but got {meals}"

    expected_query = normalize_whitespace(
        """
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0
        ORDER BY win_pct DESC
    """
    )
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query


def test_update_meal_stats(mock_cursor):
    """Test updating meal stats with a win."""

    # Simulate that the meal exists and is not deleted
    mock_cursor.fetchone.return_value = (False,)

    # Call the update_meal_stats function
    update_meal_stats(1, "win")

    expected_query = normalize_whitespace(
        """
        UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?
    """
    )
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])
    assert actual_query == expected_query


def test_update_meal_stats_deleted_meal(mock_cursor):
    """Test error when trying to update stats for a deleted meal."""

    # Simulate that the meal exists but is marked as deleted
    mock_cursor.fetchone.return_value = [True]

    # Expect a ValueError when attempting to update a deleted meal
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, "win")

    # Ensure only the check query was executed
    mock_cursor.execute.assert_called_once_with(
        "SELECT deleted FROM meals WHERE id = ?", (1,)
    )
