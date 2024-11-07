#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

##########################################################
#
# Song Management
#
##########################################################

clear_meals() {
  echo "Clearing the meals list..."
  curl -s -X DELETE "$BASE_URL/clear-meals" | grep -q '"status": "success"'
}

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Adding meal ($meal - $cuisine, $price, $difficulty) to the meals list..."
  curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Meal added successfully."
  else
    echo "Failed to add meal."
    exit 1
  fi
}

delete_meal_by_id() {
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully by ID ($meal_id)."
  else
    echo "Failed to delete meal by ID ($meal_id)."
    exit 1
  fi
}

get_leaderboard() {
  echo "Getting all meals in the meals list..."
  response=$(curl -s -X GET "$BASE_URL/get-all-meals-from-meals-list")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "All meals retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meals JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meals."
    exit 1
  fi
}

get_meal_by_id() {
  meal_id=$1

  echo "Getting meal by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-from-meals-list-by-id/$meals_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meals retrieved successfully by ID ($meals_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (ID $meal_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_name() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Getting meal by name (Meal: '$meal', Cuisine: '$cuisine', Price: $price)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-from-meals-list-by-name?meal=$(echo $meal | sed 's/ /%20/g')&cuisine=$(echo $cuisine | sed 's/ /%20/g')&price=$price&difficulty=$(echo $difficulty | sed 's/ /%20/g')")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by name."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (by name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name."
    exit 1
  fi
}


battle() {
    echo "Starting battle..."
    response=$(curl -s -X POST "$BASE_URL/battle" -H "Content-Type: application/json")

    if echo "$response" | grep -q '"winner"'; then
      winner=$(echo "$response" | jq -r '.winner')
      echo "The winner is: $winner"
      if [ "$ECHO_JSON" = true ]; then
        echo "Battle JSON:"
        echo "$response" | jq .
      fi
    else
      echo "Failed to start battle."
      exit 1
    fi
}

clear_combatants() {
    echo "Clearing all combatants..."
    response=$(curl -s -X DELETE "$BASE_URL/combatants/clear" -H "Content-Type: application/json")

    if echo "$response" | grep -q '"status": "success"'; then
      echo "Combatants cleared successfully."
    else
      echo "Failed to clear combatants."
      exit 1
    fi
}

get_combatants() {
    echo "Retrieving current combatants..."
    response=$(curl -s -X GET "BASE_URL/combatants" -H "Content-Type: application/json")
    
    if echo "$response" | jq '.'; then
      echo "Combatants retrieved successfully."
    else
      echo "Failed to retrieve combants."
      exit 1
    fi
}

# Health checks
check_health
check_db

# Clear the meals list
clear_meals

# Create meals
create_meal "Pizza" "Italian" 15.99 "MED"
create_meal "Taco" "Mexican" 8.99 "LOW"

delete_meal_by_id 1
get_leaderboard
create_meal "Burger" "American" 10.99 "HIGH"

get_meal_by_id 2
get_meal_by_name "Pizza" "Italian" 15.99 "MED"
battle
get_combatants

