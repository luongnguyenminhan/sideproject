// import { ModelStats } from "@/helpers/types/dashboard.type";
// import {
//   useGetModelUsageQuery,
//   useGetStatisticsQuery,
// } from "@/services/admin/admin-dashboard";
import { useEffect, useMemo, useState } from 'react';
import { ModelStats } from '../../../../../types/dashboard.type';

const useChartView = () => {
  const statistics = {};
  const modelUsage = {};
  const isStatisticsLoading = false;
  const isModelUsageLoading = false;
  // const { data: statistics, isLoading: isStatisticsLoading } = useGetStatisticsQuery({});
  // const { data: modelUsage, isLoading: isModelUsageLoading } = useGetModelUsageQuery({});

  const [modelStats, setModelStats] = useState<ModelStats[]>([]);
  const [dashboardStats, setDashboardStats] = useState({
    users: { total: 0, active: 0, inactive: 0 },
    totalModels: 0,
    totalCategories: 0,
    totalGroups: 0,
  });

  const isLoading = isStatisticsLoading || isModelUsageLoading;

  useEffect(() => {
    if (statistics?.data) {
      setDashboardStats(statistics.data);
    }
    if (modelUsage?.data?.models) {
      setModelStats(modelUsage.data.models);
    }
  }, [statistics, modelUsage]);

  const dashboardData = useMemo(() => {
    return {
      numberOfCategories: dashboardStats?.totalCategories,
      numOfGroups: dashboardStats?.totalGroups,
      numOfUsers: dashboardStats?.users?.total,
      numOfModels: dashboardStats?.totalModels,
      lastUpdated: new Date().toISOString(),
    };
  }, [isLoading, modelStats, dashboardStats]);

  return {
    state: {
      statistics,
      modelUsage,
      isLoading,
      modelStats,
      dashboardStats,
      dashboardData,
    },
    handler: {
      setModelStats,
      setDashboardStats,
    },
  };
};

export { useChartView };
