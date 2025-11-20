/**
 * ChartsManager Module
 * Handles real-time visualization of process variables using Chart.js
 */

const ChartsManager = (() => {
    const WINDOW_SECONDS = 600;
    let startTimestamp = null;
    const charts = {
        levels: null,
        concentrations: null,
        controls: null
    };

    const LEVEL_SERIES = [
        { key: 'tank_a_level', label: 'Tanque A', color: '#2563eb' },
        { key: 'tank_b_level', label: 'Tanque B', color: '#7c3aed' },
        { key: 'tank_c_level', label: 'Tanque C', color: '#16a34a' },
        { key: 'tank_d_level', label: 'Tanque D', color: '#dc2626' },
        { key: 'tank_e_level', label: 'Tanque E', color: '#f97316' }
    ];

    const CONCENTRATION_SERIES = [
        { key: 'tank_c_concentration', label: 'Tanque C', color: '#0ea5e9' },
        { key: 'tank_d_concentration', label: 'Tanque D', color: '#a855f7' },
        { key: 'tank_e_concentration', label: 'Tanque E', color: '#f43f5e' }
    ];

    const CONTROL_SERIES = [
        { key: 'tank_a_supply_valve', label: 'Válvula de Suprimento A', color: '#1d4ed8' },
        { key: 'tank_b_supply_valve', label: 'Válvula de Suprimento B', color: '#7e22ce' },
        { key: 'tank_c_water_pump', label: 'Bomba de Água C', color: '#10b981' },
        { key: 'tank_c_brine_pump', label: 'Bomba de Salmoura C', color: '#0d9488' },
        { key: 'tank_c_outlet_valve', label: 'Válvula de Saída C', color: '#b45309' },
        { key: 'tank_d_water_pump', label: 'Bomba de Água D', color: '#059669' },
        { key: 'tank_d_brine_pump', label: 'Bomba de Salmoura D', color: '#047857' },
        { key: 'tank_d_outlet_valve', label: 'Válvula de Saída D', color: '#b91c1c' },
        { key: 'tank_e_water_pump', label: 'Bomba de Água E', color: '#14b8a6' },
        { key: 'tank_e_brine_pump', label: 'Bomba de Salmoura E', color: '#0f766e' },
        { key: 'tank_e_outlet_valve', label: 'Válvula de Saída E', color: '#e11d48' }
    ];

    function initialize() {
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded. Charts will be disabled.');
            return;
        }

        charts.levels = createChart('chart-levels', LEVEL_SERIES, {
            yMin: 0,
            yMax: 3.5,
            yTitle: 'Nível (m)'
        });

        charts.concentrations = createChart('chart-concentrations', CONCENTRATION_SERIES, {
            yMin: 0,
            yMax: 360,
            yTitle: 'Concentração (kg/m³)'
        });

        charts.controls = createChart('chart-controls', CONTROL_SERIES, {
            yMin: 0,
            yMax: 100,
            yTitle: 'Controle (%)'
        });

        reset();
    }

    function createChart(canvasId, series, { yMin = undefined, yMax = undefined, yTitle = '' } = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.warn(`Canvas #${canvasId} not found.`);
            return null;
        }

        const ctx = canvas.getContext('2d');
        const datasets = series.map((serie) => ({
            label: serie.label,
            key: serie.key,
            data: [],
            borderColor: serie.color,
            backgroundColor: serie.color,
            borderWidth: 2,
            tension: 0.15,
            fill: false,
            pointRadius: 0,
            spanGaps: true
        }));

        return new Chart(ctx, {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: {
                    intersect: false,
                    mode: 'nearest'
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: 'Tempo (s)'
                        },
                        min: 0,
                        max: WINDOW_SECONDS,
                        ticks: {
                            callback: (value) => `${Math.round(value)} s`
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: yTitle
                        },
                        min: yMin,
                        max: yMax,
                        ticks: {
                            callback: (value) => typeof value === 'number' ? value.toFixed(0) : value
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.y;
                                return `${context.dataset.label}: ${value?.toFixed(2)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    function ingestRealtimeSample(timestamp, variables = {}, controls = {}) {
        const relativeTime = normalizeTimestamp(timestamp);

        addDataToChart(charts.levels, LEVEL_SERIES, variables, relativeTime);
        addDataToChart(charts.concentrations, CONCENTRATION_SERIES, variables, relativeTime);

        const controlPercentages = {};
        Object.entries(controls || {}).forEach(([key, value]) => {
            if (typeof value === 'number') {
                controlPercentages[key] = value * 100;
            }
        });
        addDataToChart(charts.controls, CONTROL_SERIES, controlPercentages, relativeTime);
    }

    function addDataToChart(chart, series, source, xValue) {
        if (!chart) return;

        series.forEach((serie) => {
            const value = source?.[serie.key];
            if (typeof value !== 'number' || Number.isNaN(value)) {
                return;
            }

            const dataset = chart.data.datasets.find((ds) => ds.key === serie.key);
            if (!dataset) return;

            dataset.data.push({ x: xValue, y: value });
        });

        trimOldPoints(chart, xValue - WINDOW_SECONDS);
        chart.update('none');
    }

    function trimOldPoints(chart, minAllowedX) {
        chart.data.datasets.forEach((dataset) => {
            while (dataset.data.length && dataset.data[0].x < minAllowedX) {
                dataset.data.shift();
            }
        });

        chart.options.scales.x.min = Math.max(0, minAllowedX);
        chart.options.scales.x.max = Math.max(WINDOW_SECONDS, minAllowedX + WINDOW_SECONDS);
    }

    function normalizeTimestamp(timestamp) {
        let ts = typeof timestamp === 'number' && Number.isFinite(timestamp)
            ? timestamp
            : Date.now() / 1000;

        if (startTimestamp === null) {
            startTimestamp = ts;
        }

        return ts - startTimestamp;
    }

    function reset() {
        startTimestamp = null;
        Object.values(charts).forEach((chartInstance) => {
            if (!chartInstance) return;
            chartInstance.data.datasets.forEach((dataset) => {
                dataset.data = [];
            });
            chartInstance.options.scales.x.min = 0;
            chartInstance.options.scales.x.max = WINDOW_SECONDS;
            chartInstance.update('none');
        });
    }

    return {
        initialize,
        ingestRealtimeSample,
        reset
    };
})();
