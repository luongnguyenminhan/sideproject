import Chart, { CategoryScale, ChartData } from "chart.js/auto";
import dayjs from "dayjs";
import { Line } from "react-chartjs-2";
import { TEXT_TRANSLATE } from "../statistic.translate";

Chart.register(CategoryScale);

interface LineChartProps {
  chartData: ChartData<"line"> | any;
  options?: object;
}

const LineChart = ({ chartData, options }: LineChartProps) => {
  const currentDate = dayjs();
  const startOfWeek =
    currentDate.day() === 0
      ? currentDate.day(-6).startOf("day")
      : currentDate.day(1).startOf("day");
  const endOfWeek = startOfWeek.add(6, "days").endOf("day");

  return (
    <div className="px-4 py-2">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-800">
          {TEXT_TRANSLATE.LINE_CHART.TITLE}
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          {TEXT_TRANSLATE.LINE_CHART.SUB_TITLE}
        </p>
      </div>
      <div className="h-96">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
};

export { LineChart };
