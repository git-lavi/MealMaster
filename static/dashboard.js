var canvas = document.getElementById('pieChart');

// Access the data-nutrients attribute as a JavaScript object
var nutrientsData = JSON.parse(canvas.dataset.nutrients);
delete nutrientsData['Calories'];
console.log(nutrientsData);

// Get the labels (keys) and data (values) for the pie chart
var labels = Object.keys(nutrientsData);
var data = Object.values(nutrientsData);

// Get the canvas element
var ctx = document.getElementById('pieChart').getContext('2d');

// Create the pie chart using Chart.js
var pieChart = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: labels,
        datasets: [{
            data: data,
            backgroundColor: [
                'orange', // Red
                'skyblue', // Blue
                'pink', // Yellow

            ],
            borderWidth: 1
        }]
    },
    options: {
        title: {
            display: true,
            text: 'Nutrient Distribution'
        }
    },
});