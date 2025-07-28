/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMemo } from 'react';
import { ModelStats } from '../../../../../types/dashboard.type';
import { CHART_COLORS } from '../statistic.constant';

const useBarChartData = (modelStats: ModelStats[]) => {
  return useMemo(() => {
    const transactionsPerUser = modelStats.map((model: ModelStats) => {
      if (model.userCount === 0) return 0;
      return parseFloat((model.transactionCount / model.userCount).toFixed(1));
    });

    const modelNames = modelStats.map((model: ModelStats) => model.modelName);

    return {
      labels: modelNames,
      datasets: [
        {
          label: 'Giao dịch trung bình/người dùng',
          data: transactionsPerUser,
          backgroundColor: CHART_COLORS[0],
          barPercentage: 0.8,
          order: 1,
        },
        {
          label: 'Số lượng người dùng',
          data: modelStats.map((model: any) => model.userCount),
          backgroundColor: CHART_COLORS[1],
          barPercentage: 0.8,
          order: 2,
        },
        {
          label: 'Số lượng giao dịch',
          data: modelStats.map((model: any) => model.transactionCount),
          backgroundColor: CHART_COLORS[2],
          barPercentage: 0.8,
          order: 3,
        },
      ],
    };
  }, [modelStats]);
};

export { useBarChartData };
