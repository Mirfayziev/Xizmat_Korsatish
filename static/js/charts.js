// ================================
//  GLOBAL CHART SETTINGS
// ================================

Chart.defaults.font.family = "Segoe UI";
Chart.defaults.font.size = 14;
Chart.defaults.color = "#333";


// ================================
//  BAR CHART (Buyurtmalar statistikasi)
// ================================

function createOrdersChart(ctx, labels, values) {
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: "Buyurtmalar soni",
                data: values,
                backgroundColor: "rgba(33, 150, 243, 0.6)",
                borderColor: "#0d6efd",
                borderWidth: 2,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}


// ================================
//  PIE CHART (Xizmatlar ulushi)
// ================================

function createServicePieChart(ctx, labels, values) {
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    "#0d6efd",
                    "#dc3545",
                    "#ffc107",
                    "#198754",
                    "#6f42c1",
                    "#fd7e14"
                ],
                borderWidth: 2
            }]
        }
    });
}


// ================================
//  LINE CHART (Kunlik buyurtmalar)
// ================================

function createOrdersLineChart(ctx, labels, values) {
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: "Kunlik buyurtmalar",
                data: values,
                fill: false,
                borderColor: "#198754",
                borderWidth: 3,
                tension: 0.3,
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}


// ================================
//  RADAR CHART (Usta KPI)
// ================================

function createKPIChart(ctx, labels, values) {
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: "Usta KPI",
                data: values,
                backgroundColor: "rgba(13,110,253,0.2)",
                borderColor: "#0d6efd",
                borderWidth: 2,
                pointBackgroundColor: "#0d6efd"
            }]
        },
        options: {
            responsive: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}
