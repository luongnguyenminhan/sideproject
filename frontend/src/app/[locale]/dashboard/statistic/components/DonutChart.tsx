import Chart, { CategoryScale, ChartData } from "chart.js/auto";
import { Doughnut } from "react-chartjs-2";
import { TEXT_TRANSLATE } from "../statistic.translate";

Chart.register(CategoryScale);

interface DonutChartProps {
  chartData: ChartData<"doughnut">;
  options?: object;
}

const DonutChart = ({ chartData, options }: DonutChartProps) => {
  return (
    <div className="p-2">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-800">
          {TEXT_TRANSLATE.DONUT_CHART.TITLE}
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          {TEXT_TRANSLATE.DONUT_CHART.SUB_TITLE}
        </p>
      </div>
      <div className="flex h-96 w-full items-center justify-center">
        <Doughnut data={chartData} options={options} />
      </div>
    </div>
  );
};

export { DonutChart };
