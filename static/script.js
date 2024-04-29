document.addEventListener("DOMContentLoaded", function() {
    // For flashed messages
    var flashedMessages = document.querySelectorAll('.flashed-message');

    flashedMessages.forEach(function(message) {
        // Hide the message after 3 seconds (3000 milliseconds)
        setTimeout(function() {
            message.style.display = 'none';
        }, 3000);
    });


    // For Add Meal button
    const addMealBtn = document.getElementById('add-meal-btn')

    addMealBtn.addEventListener('click', function () {
        getElementById('add-meal-name').style.display = 'block'
    })


});
