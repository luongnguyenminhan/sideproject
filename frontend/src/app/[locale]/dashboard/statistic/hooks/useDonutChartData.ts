import { useMemo } from 'react';
import { ModelStats } from '../../../../../types/dashboard.type';
import { CHART_COLORS } from '../statistic.constant';

const useDonutChartData = (modelStats: ModelStats[]) => {
  return useMemo(() => {
    return {
      labels: modelStats.map((model: ModelStats) => model.modelName),
      datasets: [
        {
          label: 'Người dùng',
          data: modelStats.map((model: ModelStats) => model.userCount),
          backgroundColor: CHART_COLORS,
          hoverOffset: 4,
        },
      ],
    };
  }, [modelStats]);
};

export { useDonutChartData };
