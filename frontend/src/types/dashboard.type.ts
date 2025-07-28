export interface AdminDashboardInfo {
  numberOfCategories: number;
  numOfGroups: number;
  numOfUsers: number;
  numOfModels: number;
  lastUpdated: string;
}

export interface AdminDashboardRevenueCategory {
  categoryId: number;
  categoryName: string;
  revenue: number;
  lastUpdated: string;
}

export interface AdminDashboardRevenueStore {
  storeId: number;
  storeName: string;
  revenue: number;
  lastUpdated: string;
}

export interface AdminDashboardMainChart {
  date: string;
  orderCount: number;
  revenue: number;
}

export interface ModelStats {
  modelId: string;
  modelName: string;
  userCount: number;
  transactionCount: number;
  totalAmount: number;
}

export interface DashboardStats {
  users: {
    total: number;
    active: number;
    inactive: number;
  };
  totalModels: number;
  totalCategories: number;
  totalGroups: number;
}

export interface ModelUsageResponse {
  status: number;
  errorCode: string;
  message: string;
  data: {
    models: ModelStats[];
  };
}

export interface StatisticsResponse {
  status: number;
  errorCode: string;
  message: string;
  data: DashboardStats;
}

export interface DashboardData {
  revenue: number;
  numOfProducts: number;
  numOfStores: number;
  numOfOrders: number;
  numOfUsers: number;
  lastUpdated: string;
}
