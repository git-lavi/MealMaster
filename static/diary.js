document.addEventListener('DOMContentLoaded', function() {
    const addMealBtn = document.getElementById('add-meal-btn');
    const mealInput = document.getElementById('meal-input');
    const addMealForm = document.getElementById('add-meal-form');
    const mealTable = document.getElementById('meal-table');
    const mealBody = document.getElementById('meal-body');

    // Event listener for add meal button
    addMealBtn.addEventListener('click', function() {
        mealInput.style.display = 'block';
        addMealBtn.style.display = 'none';
    });

    // When add meal form is submitted
    addMealForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const mealName = document.getElementById('meal-name').value;

        if (mealName.trim() !== '') {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${mealName}</td>
                <td colspan="3"></td>
                <td><button class="add-food">Add Food</button></td>
            `;

            mealBody.appendChild(row); // Append the new row to the meal table body

            mealInput.style.display = 'none';
            addMealBtn.style.display = 'block'
            mealTable.style.display = 'table'; 
        }

        else {
            alert('Please enter a meal name.');
        }
    });


    // Adding food to a meal
    mealBody.addEventListener('click', function(e) {
        if (e.target.classList.contains('add-food')) {
            const newRow = mealBody.insertRow();
            newRow.innerHTML = `
                <td></td>
                <td><input type="text" name="food_name[]" required></td>
                <td><input type="number" name="food_quantity[]" required></td>
                <td><button class="remove-food">Remove</button></td>
            `;
        }
    });

    // Remove food from a meal
    mealBody.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-food')) {
            e.target.closest('tr').remove();
        }
    });

});