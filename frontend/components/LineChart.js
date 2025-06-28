/**
 * LineChart component for rendering line charts using Chart.js.
 * @module LineChart
 */

export default class LineChart {
  /**
   * Creates a chart instance.
  * @param {HTMLCanvasElement} canvas - Canvas element for rendering chart
  * @param {string[]} labels - Labels for the x-axis
  * @param {number[]} data - Data points for the chart
  * @param {string} label - Dataset label
  * @param {string} color - Line color
  * Existing charts on the same canvas are destroyed to avoid Chart.js errors.
  */
  constructor(canvas, labels, data, label, color) {
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
            beginAtZero: true
          }
        }
      }
    });
  }
}
