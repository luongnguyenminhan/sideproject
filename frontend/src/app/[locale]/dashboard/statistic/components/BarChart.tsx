import Chart, { CategoryScale, ChartData } from "chart.js/auto";
import { Bar } from "react-chartjs-2";
import { TEXT_TRANSLATE } from "../statistic.translate";

Chart.register(CategoryScale);

interface BarChartProps {
  chartData: ChartData<"bar"> | any;
  options?: object;
  title?: string;
  description?: string;
}

const BarChart = ({
  chartData,
  options,
  title = TEXT_TRANSLATE.BAR_CHART.TITLE,
  description = TEXT_TRANSLATE.BAR_CHART.SUB_TITLE,
}: BarChartProps) => {
  return (
    <div className="px-4 py-2">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-800">{title}</h3>
        <p className="mt-1 text-sm text-gray-500">{description}</p>
      </div>
      <div className="h-96">
        <Bar
          data={chartData}
          options={{ ...options, maintainAspectRatio: false }}
        />
      </div>
    </div>
  );
};

export { BarChart };
