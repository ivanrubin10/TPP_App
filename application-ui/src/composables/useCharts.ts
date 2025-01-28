import { computed } from 'vue';
import type { ChartData, ChartOptions } from 'chart.js';
import type { CarItem } from '@/types';

export function useCharts(items: CarItem[]) {
  const pieChartData = computed<ChartData<'pie'>>(() => ({
    labels: ['Pass', 'Fail'],
    datasets: [{
      data: [
        items.filter(item => item.outcome === 'GOOD').length,
        items.filter(item => item.outcome === 'NOGOOD').length
      ],
      backgroundColor: ['#4CAF50', '#f44336'],
      borderColor: ['#388E3C', '#D32F2F'],
      borderWidth: 1
    }]
  }));

  const lineChartData = computed<ChartData<'line'>>(() => {
    const last7Days = [...Array(7)].map((_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - i);
      return `${String(d.getDate()).padStart(2, '0')}-${String(d.getMonth() + 1).padStart(2, '0')}-${d.getFullYear()}`;
    }).reverse();

    return {
      labels: last7Days,
      datasets: [{
        label: 'Daily Inspections',
        data: last7Days.map(date =>
          items.filter(item => item.date.startsWith(date)).length
        ),
        borderColor: 'rgba(255, 255, 255, 0.5)',
        backgroundColor: 'rgba(255, 255, 255, 1)',
        tension: 0.1
      }]
    };
  });

  const baseChartOptions: ChartOptions<'pie' | 'line'> = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: 'var(--text-100)',
          font: {
            size: 12,
            family: 'Arial'
          }
        }
      }
    }
  };

  const lineChartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: 'var(--text-100)',
          font: {
            size: 12,
            family: 'Arial'
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.3)'
        },
        ticks: {
          color: 'var(--text-100)',
          font: {
            size: 12,
            family: 'Arial'
          }
        }
      },
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.3)'
        },
        ticks: {
          color: 'var(--text-100)',
          font: {
            size: 12,
            family: 'Arial'
          }
        }
      }
    }
  };

  const modalChartOptions = computed(() => ({
    pie: {
      ...baseChartOptions,
      maintainAspectRatio: true
    },
    line: {
      ...lineChartOptions,
      maintainAspectRatio: true
    }
  }));

  return {
    pieChartData,
    lineChartData,
    baseChartOptions,
    lineChartOptions,
    modalChartOptions
  };
} 