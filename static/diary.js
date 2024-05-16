// Assistance from ChatGPT taken for Javascript code.

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
    const addFoodBtns = document.querySelectorAll('.add-food-btn');

    addFoodBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const foodInputOverlay = this.parentNode.querySelector('.food-input-overlay');
            const foodInput = foodInputOverlay.querySelector('.food-input');

            foodInputOverlay.style.display = "block";
            foodInput.style.display = "flex";
        });
    });

    document.addEventListener('click', function(event) {
        const foodInputOverlays = document.querySelectorAll('.food-input-overlay');
    
        foodInputOverlays.forEach(function(overlay) {
            overlay.addEventListener('click', function() {
                overlay.style.display = 'none';
                const foodInput = overlay.querySelector('.food-input');
                foodInput.style.display = 'none';
            });
    
            // Prevent closing when clicking inside the food input
            const foodInput = overlay.querySelector('.food-input');
            foodInput.addEventListener('click', function(event) {
                event.stopPropagation(); // Stop the click event from propagating to the overlay
            });

            // Prevent multiple submissions
            const foodSubmitBtn = overlay.querySelector('.food-submit')
            let submitted = false;

            foodSubmitBtn.addEventListener('click', function(event) {
                event.preventDefault();

                if (!submitted) {
                    foodSubmitBtn.disabled = true;
                    submitted = true;
                    this.closest('form').submit();
                }
            });
        });
    });
});