document.addEventListener('DOMContentLoaded', function() {

    // Adding a meal
    const addMealBtn = document.getElementById('add-meal-btn');
    const mealInputOverlay = document.getElementById('meal-input-overlay')
    const mealInput = document.getElementById('meal-input');

    addMealBtn.addEventListener('click', function() {
        mealInputOverlay.style.display = "block";
        mealInput.style.display = "flex";
    });

    mealInputOverlay.addEventListener('click', function() {
        mealInputOverlay.style.display = "none";
        mealInput.style.display = "none";
        document.getElementById('meal-name').value = "";
    });

    mealInput.addEventListener('click', function(event) {
        event.stopPropagation(); // Stop the click event from propagating to the overlay
    });


    // Adding a food
    
    });