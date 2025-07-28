/* eslint-disable @typescript-eslint/no-explicit-any */

const ModelUsageTable = ({ modelStats }: { modelStats: any }) => {
  return (
    <div className='rounded-lg border border-gray-200 shadow'>
      <table className='min-w-full divide-y divide-gray-200'>
        <thead>
          <tr className='bg-gray-100'>
            <th
              scope='col'
              className='px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-600'
            >
              Tên mô hình
            </th>
            <th
              scope='col'
              className='px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-600'
            >
              Người dùng
            </th>
            <th
              scope='col'
              className='px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-600'
            >
              Giao dịch
            </th>
            <th
              scope='col'
              className='px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-600'
            >
              Trung bình/GD
            </th>
          </tr>
        </thead>
        <tbody className='divide-y divide-gray-200 bg-white'>
          {modelStats.map((model: any, index: number) => (
            <tr
              key={model.modelId}
              className={`transition-colors hover:bg-light/60 ${
                index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
              }`}
            >
              <td className='whitespace-nowrap px-6 py-4'>
                <div className='flex items-center'>
                  <div className='font-medium text-gray-900'>{model.modelName}</div>
                </div>
              </td>
              <td className='whitespace-nowrap px-6 py-4'>
                <div className='text-gray-700'>{model.userCount}</div>
              </td>
              <td className='whitespace-nowrap px-6 py-4'>
                <div className='text-gray-700'>{model.transactionCount}</div>
              </td>
              <td className='whitespace-nowrap px-6 py-4'>
                <div className='text-gray-700'>
                  {model.transactionCount && model.userCount > 0
                    ? Math.round(model.transactionCount / model.userCount)
                    : 0}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export { ModelUsageTable };
