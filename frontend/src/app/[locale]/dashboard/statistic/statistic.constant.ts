/* eslint-disable @typescript-eslint/no-explicit-any */
export const lineOptions = {
  plugins: {
    datalabels: {
      display: false,
    },
    legend: {
      position: 'top',
      align: 'center',
      labels: {
        usePointStyle: false,
        font: {
          size: 12,
        },
      },
    },
    tooltip: {
      backgroundColor: 'rgba(53, 72, 91, 0.95)',
      titleFont: {
        size: 13,
      },
      bodyFont: {
        size: 12,
      },
      padding: 12,
      cornerRadius: 8,
      displayColors: true,
    },
  },
  elements: {
    point: {
      radius: 3,
      backgroundColor: 'currentColor',
      hoverRadius: 5,
      hitRadius: 8,
    },
    line: {
      tension: 0.3,
    },
  },
  scales: {
    y: {
      type: 'linear',
      display: true,
      position: 'left',
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      ticks: {
        font: {
          size: 11,
        },
      },
      title: {
        display: true,
        text: 'Số giao dịch',
        font: {
          size: 12,
          weight: 'normal',
        },
      },
    },
    y1: {
      type: 'linear',
      display: true,
      position: 'right',
      grid: {
        drawOnChartArea: false,
      },
      ticks: {
        font: {
          size: 11,
        },
      },
      title: {
        display: true,
        text: 'Người dùng',
        font: {
          size: 12,
          weight: 'normal',
        },
      },
    },
    x: {
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      ticks: {
        font: {
          size: 12,
        },
      },
    },
  },
  responsive: true,
  maintainAspectRatio: false,
};

export const barOptions = {
  plugins: {
    datalabels: {
      display: false,
    },
    legend: {
      position: 'top',
      labels: {
        usePointStyle: false,
        padding: 20,
        font: {
          size: 12,
        },
      },
    },
    tooltip: {
      backgroundColor: 'rgba(53, 72, 91, 0.95)',
      titleFont: {
        size: 13,
      },
      bodyFont: {
        size: 12,
      },
      padding: 12,
      cornerRadius: 8,
      displayColors: true,
      callbacks: {
        label: function (context: any) {
          let label = context.dataset.label || '';
          if (label) {
            label += ': ';
          }
          if (context.parsed.y !== null) {
            if (label.includes('Avg')) {
              label += new Intl.NumberFormat('vi-VN', {
                style: 'currency',
                currency: 'VND',
              }).format(context.parsed.y);
            } else {
              label += context.parsed.y;
            }
          }
          return label;
        },
      },
    },
  },
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      ticks: {
        font: {
          size: 11,
        },
      },
      title: {
        // display: true,
        text: 'Giá trị',
        font: {
          size: 12,
          weight: 'normal',
        },
      },
    },
    x: {
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      ticks: {
        font: {
          size: 11,
        },
      },
    },
  },
  barPercentage: 0.8,
  categoryPercentage: 0.7,
};

export const donutOptions = {
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        usePointStyle: false,
        padding: 20,
      },
    },
  },
};

export const CHART_COLORS = [
  'rgba(66, 133, 244, 0.8)', // Blue
  'rgba(219, 68, 55, 0.8)', // Red
  'rgba(244, 180, 0, 0.8)', // Yellow
  'rgba(15, 157, 88, 0.8)', // Green
  'rgba(171, 71, 188, 0.8)', // Purple
];
