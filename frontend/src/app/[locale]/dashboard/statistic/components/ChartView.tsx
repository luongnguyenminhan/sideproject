'use client';

import { LoadingSectionWrapper } from '../../../../../components/common/LoadingSectionWrapper';
import { useChartView } from '../hooks/useChartView';
import { useDonutChartData } from '../hooks/useDonutChartData';
import { useLineChartData } from '../hooks/useLineChartData';
import { donutOptions, lineOptions } from '../statistic.constant';
import { DonutChart } from './DonutChart';
import { LineChart } from './LineChart';
import { TotalField } from './TotalField';

const ChartView = () => {
  const { state } = useChartView();
  const lineData = useLineChartData(state.modelStats);
  const donutData = useDonutChartData(state.modelStats);
  // const barData = useBarChartData(state.modelStats);

  return (
    <LoadingSectionWrapper isLoading={state.isLoading}>
      <section className='bg-gray-50 py-6'>
        <div className='px-6'>
          <TotalField data={state.dashboardData} />
        </div>
        <div className='mt-8 grid grid-cols-1 gap-6 px-6 md:grid-cols-3'>
          <div className='col-span-1 overflow-hidden rounded-xl bg-white p-4 shadow-md transition-all duration-300 hover:shadow-lg md:col-span-2'>
            <LineChart chartData={lineData} options={lineOptions} />
          </div>
          <div className='col-span-1 overflow-hidden rounded-xl bg-white p-4 shadow-md transition-all duration-300 hover:shadow-lg'>
            <div className='flex h-full flex-col justify-center px-2'>
              <DonutChart chartData={donutData} options={donutOptions} />
            </div>
          </div>
        </div>
        {/* <div className='mt-8 grid grid-cols-1 gap-6 px-6 lg:grid-cols-2'>
          <div className='overflow-hidden rounded-xl bg-white p-4 shadow-md transition-all duration-300 hover:shadow-lg'>
            <BarChart chartData={barData} options={barOptions} />
          </div>
          <div className='overflow-hidden rounded-xl bg-white p-6 shadow-md transition-all duration-300 hover:shadow-lg'>
            <div className='mb-6'>
              <h3 className='text-xl font-bold text-gray-800'>
                {TEXT_TRANSLATE.MODEL_USAGE_TABLE.TITLE}
              </h3>
              <p className='mt-1 text-sm text-gray-500'>
                {TEXT_TRANSLATE.MODEL_USAGE_TABLE.SUB_TITLE}
              </p>
            </div>
            <ModelUsageTable modelStats={state.modelStats} />
          </div>
        </div> */}
      </section>
    </LoadingSectionWrapper>
  );
};

export { ChartView };
