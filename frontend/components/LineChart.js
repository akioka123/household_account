/**
 * LineChart component for rendering line charts using Chart.js.
 * @module LineChart
 */

export default class LineChart {
  /**
   * Creates a chart instance.
   *
   * @param {HTMLCanvasElement} canvas - Canvas element for rendering chart
   * @param {string[]} labels - Labels for the x-axis
   * @param {number[]} data - Data points for the chart
   * @param {string} label - Dataset label
   * @param {string} color - Line color
   * @param {number} [max] - Optional initial maximum value for the y-axis
   * Existing charts on the same canvas are destroyed to avoid Chart.js errors.
   */
  constructor(canvas, labels, data, label, color, max) {
    if (typeof Chart !== 'undefined' && typeof Chart.getChart === 'function') {
      const existing = Chart.getChart(canvas);
      if (existing) {
        existing.destroy();
      }
    }
    this.chart = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label,
          data,
          borderColor: color,
          backgroundColor: color,
          fill: false
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            max
          }
        }
      }
    });
  }

  /**
   * Update the maximum value of the y-axis and redraw the chart.
   *
   * @param {number} max - Maximum value for the y-axis.
   */
  setMax(max) {
    this.chart.options.scales.y.max = max;
    this.chart.update();
  }

  /**
   * Replace dataset with new label and data.
   *
   * @param {string[]} labels - X-axis labels.
   * @param {number[]} data - Data points.
   * @param {string} label - Dataset label.
   */
  updateData(labels, data, label) {
    this.chart.data.labels = labels;
    this.chart.data.datasets[0].data = data;
    this.chart.data.datasets[0].label = label;
    this.chart.update();
  }
}
