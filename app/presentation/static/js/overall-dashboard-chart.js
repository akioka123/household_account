// 総合ダッシュボードグラフ
(function () {
    'use strict';

    // ストラテジーパターン：基底クラス（選択項目推移グラフ用）
    class ChartStrategy {
        extractData(monthSummaries, startYear, endYear) {
            throw new Error('extractData must be implemented');
        }

        getYAxisConfig() {
            throw new Error('getYAxisConfig must be implemented');
        }

        getLabel() {
            throw new Error('getLabel must be implemented');
        }

        getLineConfig() {
            throw new Error('getLineConfig must be implemented');
        }
    }

    // 損益ストラテジー
    class ProfitStrategy extends ChartStrategy {
        extractData(monthSummaries, startYear, endYear) {
            // 指定期間のデータを準備
            const data = [];
            const labels = [];
            
            // データマップを作成（年月をキーに）
            const dataMap = new Map();
            monthSummaries.forEach(summary => {
                const key = `${summary.year}-${summary.month}`;
                dataMap.set(key, summary.profit);
            });

            // startYear年1月からendYear年12月までループ
            for (let year = startYear; year <= endYear; year++) {
                for (let month = 1; month <= 12; month++) {
                    const key = `${year}-${month}`;
                    const value = dataMap.get(key);
                    data.push(value !== undefined ? value : null);
                    labels.push(`${year}/${month}`);
                }
            }

            return { data, labels };
        }

        getYAxisConfig() {
            return {
                min: -500000,
                max: 500000,
                ticks: {
                    stepSize: 50000,
                    callback: function (value) {
                        return (value / 10000) + '万';
                    }
                }
            };
        }

        getLabel() {
            return '損益';
        }

        getLineConfig() {
            return {
                color: 'rgb(239, 68, 68)',
                borderColor: 'rgb(239, 68, 68)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.1,
                fill: true
            };
        }
    }

    // 手取りストラテジー
    class NetIncomeStrategy extends ChartStrategy {
        extractData(monthSummaries, startYear, endYear) {
            const data = [];
            const labels = [];
            
            const dataMap = new Map();
            monthSummaries.forEach(summary => {
                const key = `${summary.year}-${summary.month}`;
                dataMap.set(key, summary.netIncome);
            });

            for (let year = startYear; year <= endYear; year++) {
                for (let month = 1; month <= 12; month++) {
                    const key = `${year}-${month}`;
                    const value = dataMap.get(key);
                    data.push(value !== undefined ? value : null);
                    labels.push(`${year}/${month}`);
                }
            }

            return { data, labels };
        }

        getYAxisConfig() {
            return {
                min: 200000,
                max: 1000000,
                ticks: {
                    stepSize: 50000,
                    callback: function (value) {
                        return (value / 10000) + '万';
                    }
                }
            };
        }

        getLabel() {
            return '手取り';
        }

        getLineConfig() {
            return {
                color: 'rgb(59, 246, 100)',
                borderColor: 'rgb(59, 246, 100)',
                backgroundColor: 'rgba(59, 246, 100, 0.1)',
                tension: 0.1,
                fill: true
            };
        }
    }

    // 変動費ストラテジー
    class VariableExpenseStrategy extends ChartStrategy {
        extractData(monthSummaries, startYear, endYear) {
            const data = [];
            const labels = [];
            
            const dataMap = new Map();
            monthSummaries.forEach(summary => {
                const key = `${summary.year}-${summary.month}`;
                dataMap.set(key, summary.variableTotal);
            });

            for (let year = startYear; year <= endYear; year++) {
                for (let month = 1; month <= 12; month++) {
                    const key = `${year}-${month}`;
                    const value = dataMap.get(key);
                    data.push(value !== undefined ? value : null);
                    labels.push(`${year}/${month}`);
                }
            }

            return { data, labels };
        }

        getYAxisConfig() {
            return {
                min: 50000,
                max: 350000,
                ticks: {
                    stepSize: 10000,
                    callback: function (value) {
                        return (value / 10000) + '万';
                    }
                }
            };
        }

        getLabel() {
            return '変動費';
        }

        getLineConfig() {
            return {
                color: 'rgb(243, 158, 48)',
                borderColor: 'rgb(243, 158, 48)',
                backgroundColor: 'rgba(243, 158, 48, 0.1)',
                tension: 0.1,
                fill: true
            };
        }
    }

    // ストラテジーファクトリ
    const strategyFactory = {
        'profit': () => new ProfitStrategy(),
        'netIncome': () => new NetIncomeStrategy(),
        'variableExpense': () => new VariableExpenseStrategy()
    };

    let annualIncomeChart = null;
    let selectedItemChart = null;

    // 年収推移グラフの初期化
    function initAnnualIncomeChart() {
        const canvas = document.getElementById('annual-income-chart');
        const dataElement = document.getElementById('overall-dashboard-chart-data');

        if (!canvas || !dataElement) {
            return;
        }

        let chartData;
        try {
            chartData = JSON.parse(dataElement.textContent);
        } catch (e) {
            console.error('Failed to parse chart data:', e);
            return;
        }

        // 既存のチャートを破棄
        if (annualIncomeChart) {
            annualIncomeChart.destroy();
            annualIncomeChart = null;
        }

        // 年ごとのデータを準備
        const labels = [];
        const grossData = [];
        const netData = [];

        chartData.annualIncomes.forEach(item => {
            labels.push(item.year + '年');
            // データがない年（gross/netが0）はnullにする
            grossData.push(item.gross > 0 ? item.gross : null);
            netData.push(item.net > 0 ? item.net : null);
        });

        // Chart.jsでグラフを作成
        const ctx = canvas.getContext('2d');
        annualIncomeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '額面',
                        data: grossData,
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1,
                        fill: true
                    },
                    {
                        label: '手取り',
                        data: netData,
                        borderColor: 'rgb(16, 185, 129)',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.1,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const value = context.parsed.y;
                                if (value === null) {
                                    return context.dataset.label + ': データなし';
                                }
                                return context.dataset.label + ': ' + (value / 10000).toFixed(1) + '万円';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        min: 2000000,
                        max: 8000000,
                        ticks: {
                            stepSize: 500000,
                            callback: function (value) {
                                return (value / 10000) + '万';
                            }
                        },
                        title: {
                            display: true,
                            text: '金額'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '年'
                        }
                    }
                }
            }
        });
    }

    // 選択項目推移グラフの初期化
    function initSelectedItemChart() {
        const canvas = document.getElementById('selected-item-chart');
        const dataElement = document.getElementById('overall-dashboard-chart-data');
        const selectElement = document.getElementById('chart-type-select');

        if (!canvas || !dataElement || !selectElement) {
            return;
        }

        let chartData;
        try {
            chartData = JSON.parse(dataElement.textContent);
        } catch (e) {
            console.error('Failed to parse chart data:', e);
            return;
        }

        // 既存のチャートを破棄
        if (selectedItemChart) {
            selectedItemChart.destroy();
            selectedItemChart = null;
        }

        // デフォルトのストラテジーを取得
        const defaultType = selectElement.value || 'profit';
        const strategy = strategyFactory[defaultType]();

        // データを抽出（期間を指定）
        const startYear = chartData.startYear || 2020;
        const endYear = chartData.endYear || 2050;
        const { data, labels } = strategy.extractData(chartData.monthSummaries, startYear, endYear);

        // ドロップダウンの変更イベント（既存のリスナーを削除してから追加）
        const newSelectElement = selectElement.cloneNode(true);
        selectElement.parentNode.replaceChild(newSelectElement, selectElement);

        // Chart.jsでグラフを作成
        const ctx = canvas.getContext('2d');
        selectedItemChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: strategy.getLabel(),
                    data: data,
                    ...strategy.getLineConfig()
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const value = context.parsed.y;
                                if (value === null) {
                                    return 'データなし';
                                }
                                return strategy.getLabel() + ': ' + (value / 10000).toFixed(1) + '万円';
                            }
                        }
                    }
                },
                scales: {
                    y: strategy.getYAxisConfig(),
                    x: {
                        title: {
                            display: true,
                            text: '月'
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });

        // ドロップダウンの変更イベント
        newSelectElement.addEventListener('change', function () {
            const selectedType = this.value;
            const newStrategy = strategyFactory[selectedType]();

            // データを更新（期間を指定）
            const { data: newData, labels: newLabels } = newStrategy.extractData(chartData.monthSummaries, startYear, endYear);
            selectedItemChart.data.labels = newLabels;
            selectedItemChart.data.datasets[0] = {
                ...newStrategy.getLineConfig(),
                data: newData,
                label: newStrategy.getLabel()
            };

            // Y軸設定を更新
            selectedItemChart.options.scales.y = newStrategy.getYAxisConfig();

            // グラフを更新
            selectedItemChart.update();
        });
    }

    // 初期化関数
    function tryInit() {
        setTimeout(() => {
            initAnnualIncomeChart();
            initSelectedItemChart();
        }, 10);
    }

    // DOMContentLoadedで初期化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', tryInit);
    } else {
        tryInit();
    }
})();
