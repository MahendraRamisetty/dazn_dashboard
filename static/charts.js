function renderChart(chartID, chartData) {
    const ctx = document.getElementById(chartID).getContext('2d');
    new Chart(ctx, chartData);
}
