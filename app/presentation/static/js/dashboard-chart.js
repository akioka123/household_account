// ダッシュボード月次推移グラフ
(function () {
    'use strict';

    // ストラテジーパターン：基底クラス
    class ChartStrategy {
        extractData(monthSummaries) {
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
        extractData(monthSummaries) {
            // 12ヶ月分のデータを準備（未登録月はnull）
            const data = new Array(12).fill(null);
            monthSummaries.forEach(summary => {
                const monthIndex = summary.month - 1; // 0-11のインデックス
                data[monthIndex] = summary.profit;
            });
            return data;
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
        extractData(monthSummaries) {
            const data = new Array(12).fill(null);
            monthSummaries.forEach(summary => {
                const monthIndex = summary.month - 1;
                data[monthIndex] = summary.netIncome;
            });
            return data;
        }

        getYAxisConfig() {
            return {
                min: 100000,
                max: 800000,
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
        extractData(monthSummaries) {
            const data = new Array(12).fill(null);
            monthSummaries.forEach(summary => {
                const monthIndex = summary.month - 1;
                data[monthIndex] = summary.variableTotal;
            });
            return data;
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

    let chart = null;

    function initChart() {
        const canvas = document.getElementById('monthly-chart');
        const dataElement = document.getElementById('dashboard-chart-data');
        const selectElement = document.getElementById('chart-type-select');

        if (!canvas || !dataElement || !selectElement) {
            return;
        }

        // データを取得
        let chartData;
        try {
            chartData = JSON.parse(dataElement.textContent);
        } catch (e) {
            console.error('Failed to parse chart data:', e);
            return;
        }

        // 既存のチャートを破棄
        if (chart) {
            chart.destroy();
            chart = null;
        }

        // デフォルトのストラテジーを取得
        const defaultType = selectElement.value || 'profit';
        const strategy = strategyFactory[defaultType]();

        // データを抽出
        const data = strategy.extractData(chartData.monthSummaries);
        const labels = Array.from({ length: 12 }, (_, i) => (i + 1) + '月');

        // ドロップダウンの変更イベント（既存のリスナーを削除してから追加）
        const newSelectElement = selectElement.cloneNode(true);
        selectElement.parentNode.replaceChild(newSelectElement, selectElement);

        // Chart.jsでグラフを作成
        const ctx = canvas.getContext('2d');
        chart = new Chart(ctx, {
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
                maintainAspectRatio: true,
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
                        }
                    }
                }
            }
        });

        // ドロップダウンの変更イベント
        newSelectElement.addEventListener('change', function () {
            const selectedType = this.value;
            const newStrategy = strategyFactory[selectedType]();

            // データを更新
            const newData = newStrategy.extractData(chartData.monthSummaries);
            chart.data.datasets[0] = {
                ...newStrategy.getLineConfig(),
                data: newData,
                label: newStrategy.getLabel()
            };

            // Y軸設定を更新
            chart.options.scales.y = newStrategy.getYAxisConfig();

            // グラフを更新
            chart.update();
        });
    }

    // 初期化関数
    function tryInit() {
        setTimeout(initChart, 10);
    }

    // DOMContentLoadedで初期化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', tryInit);
    } else {
        tryInit();
    }

    // HTMXのafterSwapイベントで再初期化
    document.body.addEventListener('htmx:afterSwap', function (event) {
        const target = event.detail.target;
        if (target.id === 'main-content' || target.querySelector('#monthly-chart')) {
            tryInit();
        }
    });
})();
