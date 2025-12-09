// ==================== GLOBAL VARIABLES ====================

let socket;
let tempChart;
let humChart;
let previousTemp = null;
let previousHum = null;

// Chart data storage
const maxDataPoints = 20;
const chartData = {
    labels: [],
    temperature: [],
    humidity: []
};

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initialized');
    initializeCharts();
    connectWebSocket();
    loadHistoricalData();
});

// ==================== WEBSOCKET CONNECTION ====================

function connectWebSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('WebSocket connected');
        updateConnectionStatus('connected', 'Connected');
    });

    socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus('error', 'Disconnected');
    });

    socket.on('sensor_update', (data) => {
        console.log('Received sensor update:', data);
        updateDashboard(data);
    });

    socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        updateConnectionStatus('error', 'Connection Error');
    });
}

// ==================== UPDATE FUNCTIONS ====================

function updateDashboard(data) {
    const { temperature, humidity, sensor_id, timestamp, status } = data;

    // Update connection status
    if (status === 'connected') {
        updateConnectionStatus('connected', 'Live');
    }

    // Update temperature
    if (temperature !== null && temperature !== undefined) {
        document.getElementById('temperatureValue').textContent = temperature.toFixed(1);
        updateTrend('tempTrend', temperature, previousTemp, '°C');
        previousTemp = temperature;
    }

    // Update humidity
    if (humidity !== null && humidity !== undefined) {
        document.getElementById('humidityValue').textContent = humidity.toFixed(1);
        updateTrend('humTrend', humidity, previousHum, '%');
        previousHum = humidity;
    }

    // Update sensor info
    if (sensor_id) {
        document.getElementById('sensorId').textContent = sensor_id;
    }

    if (timestamp) {
        document.getElementById('lastUpdate').textContent = formatTimestamp(timestamp);
    }

    // Update charts
    addDataToCharts(timestamp, temperature, humidity);
}

function updateConnectionStatus(status, text) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.getElementById('statusText');

    // Remove all status classes
    statusDot.classList.remove('status-connected', 'status-waiting', 'status-error');

    // Add appropriate class
    statusDot.classList.add(`status-${status}`);
    statusText.textContent = text;
}

function updateTrend(elementId, current, previous, unit) {
    const trendElement = document.getElementById(elementId);

    if (previous === null || previous === undefined) {
        trendElement.textContent = '';
        return;
    }

    const diff = current - previous;
    const arrow = diff > 0 ? '↑' : diff < 0 ? '↓' : '→';
    const color = diff > 0 ? '#f59e0b' : diff < 0 ? '#3b82f6' : '#6b7280';

    trendElement.textContent = `${arrow} ${Math.abs(diff).toFixed(1)}${unit}`;
    trendElement.style.color = color;
}

// ==================== CHART FUNCTIONS ====================

function initializeCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            y: {
                ticks: {
                    color: '#a0aec0'
                },
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                }
            },
            x: {
                ticks: {
                    color: '#a0aec0',
                    maxRotation: 45,
                    minRotation: 45
                },
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                }
            }
        }
    };

    // Temperature Chart
    const tempCtx = document.getElementById('tempChart').getContext('2d');
    tempChart = new Chart(tempCtx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Temperature (°C)',
                data: chartData.temperature,
                borderColor: 'rgba(245, 87, 108, 1)',
                backgroundColor: 'rgba(245, 87, 108, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5
            }]
        },
        options: chartOptions
    });

    // Humidity Chart
    const humCtx = document.getElementById('humChart').getContext('2d');
    humChart = new Chart(humCtx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Humidity (%)',
                data: chartData.humidity,
                borderColor: 'rgba(79, 172, 254, 1)',
                backgroundColor: 'rgba(79, 172, 254, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5
            }]
        },
        options: chartOptions
    });
}

function addDataToCharts(timestamp, temperature, humidity) {
    // Format timestamp for chart label
    const timeLabel = formatTimeForChart(timestamp);

    // Add data
    chartData.labels.push(timeLabel);
    chartData.temperature.push(temperature);
    chartData.humidity.push(humidity);

    // Limit data points
    if (chartData.labels.length > maxDataPoints) {
        chartData.labels.shift();
        chartData.temperature.shift();
        chartData.humidity.shift();
    }

    // Update charts
    tempChart.update('none'); // 'none' for no animation on update
    humChart.update('none');
}

// ==================== UTILITY FUNCTIONS ====================

function loadHistoricalData() {
    fetch('/api/history')
        .then(response => response.json())
        .then(data => {
            console.log('Loaded historical data:', data.length, 'points');

            // Add historical data to charts
            data.forEach(point => {
                const timeLabel = formatTimeForChart(point.timestamp);
                chartData.labels.push(timeLabel);
                chartData.temperature.push(point.temperature);
                chartData.humidity.push(point.humidity);
            });

            // Limit to maxDataPoints
            if (chartData.labels.length > maxDataPoints) {
                const excess = chartData.labels.length - maxDataPoints;
                chartData.labels = chartData.labels.slice(excess);
                chartData.temperature = chartData.temperature.slice(excess);
                chartData.humidity = chartData.humidity.slice(excess);
            }

            // Update charts
            tempChart.update();
            humChart.update();
        })
        .catch(error => {
            console.error('Error loading historical data:', error);
        });
}

function formatTimestamp(timestamp) {
    // Format: "2025-12-09 20:15:30"
    if (!timestamp) return '--';

    try {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (e) {
        return timestamp;
    }
}

function formatTimeForChart(timestamp) {
    // Format: "20:15:30"
    if (!timestamp) return '';

    try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    } catch (e) {
        // If timestamp is already in the right format, extract time
        const parts = timestamp.split(' ');
        if (parts.length === 2) {
            const timeParts = parts[1].split(':');
            return `${timeParts[0]}:${timeParts[1]}`;
        }
        return timestamp;
    }
}

function closeAlert(alertId) {
    const alert = document.getElementById(alertId);
    if (alert) {
        alert.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => {
            alert.style.display = 'none';
        }, 300);
    }
}

// ==================== AUTO-REFRESH ====================

// Periodically check for latest data (fallback if WebSocket fails)
setInterval(() => {
    fetch('/api/latest')
        .then(response => response.json())
        .then(data => {
            if (!socket.connected) {
                updateDashboard(data);
            }
        })
        .catch(error => {
            console.error('Error fetching latest data:', error);
        });
}, 10000); // Check every 10 seconds

// ==================== ANIMATIONS ====================

const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-20px);
        }
    }
`;
document.head.appendChild(style);
