const chartFont = {
    family: "Inter, system-ui, sans-serif",
    size: 12
};

Chart.defaults.font = chartFont;
Chart.defaults.color = "#6b7a8f";

new Chart(document.getElementById("salesChart"), {
    type: "bar",
    data: {
        labels: window.chartData.labels,
        datasets: [{
            label: "Sales",
            data: window.chartData.sales,
            backgroundColor: "#0f6e66",
            borderRadius: 5,
            maxBarThickness: 34
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                }
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: "#e5e9ee"
                }
            }
        }
    }
});

new Chart(document.getElementById("paymentChart"), {
    type: "doughnut",
    data: {
        labels: window.chartData.paymentLabels,
        datasets: [{
            data: window.chartData.paymentValues,
            backgroundColor: [
                "#0f6e66",
                "#2f5fb0",
                "#7c5cbf",
                "#b5680a",
                "#b3261e"
            ],
            borderWidth: 2,
            borderColor: "#ffffff"
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "62%",
        plugins: {
            legend: {
                position: "bottom",
                labels: {
                    boxWidth: 10,
                    padding: 14
                }
            }
        }
    }
});