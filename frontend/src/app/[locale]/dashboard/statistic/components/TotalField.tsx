// import Category from '@/assets/images/icons/copy.png';
// import User from '@/assets/images/icons/ic_glass_users.png';
// import Group from '@/assets/images/icons/identity.png';
// import Model from '@/assets/images/icons/tag.png';
// import Image from 'next/image';
import CountUp from 'react-countup';
import { AdminDashboardInfo } from '../../../../../types/dashboard.type';
import { TEXT_TRANSLATE } from '../statistic.translate';

interface TotalFieldProps {
  data: AdminDashboardInfo;
}

const TotalField = ({ data }: TotalFieldProps) => {
  const fields = [
    {
      icon: '',
      label: TEXT_TRANSLATE.TOTAL_FIELDS.USER,
      value: data.numOfUsers,
    },
    {
      icon: '',
      label: TEXT_TRANSLATE.TOTAL_FIELDS.CV,
      value: data.numOfGroups ?? 0,
    },
    {
      icon: '',
      label: TEXT_TRANSLATE.TOTAL_FIELDS.CHAT_HISTORY,
      value: data.numOfModels ?? 0,
    },
    {
      icon: '',
      label: TEXT_TRANSLATE.TOTAL_FIELDS.SOLD_PACKAGES,
      value: data.numberOfCategories ?? 0,
    },
  ];

  return (
    <section className='grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4'>
      {fields &&
        fields.length > 0 &&
        fields?.map((field, index) => (
          <div
            key={index}
            className='overflow-hidden rounded-xl bg-white shadow-sm transition-all duration-300 hover:translate-y-px hover:shadow-md'
          >
            <div className='flex items-center p-6'>
              <div className='flex-shrink-0 rounded-lg p-3'>
                {/* <Image
                  src={field.icon}
                  alt={`${field.label} icon`}
                  width={50}
                  height={50}
                  quality={100}
                  className='h-14 w-14'
                /> */}
              </div>
              <div className='ml-4'>
                <p className='mb-1 text-xs font-medium uppercase tracking-wider text-gray-500'>
                  {field.label}
                </p>
                <div className='flex items-baseline'>
                  <p className='text-2xl font-bold text-gray-800'>
                    <CountUp end={field.value} duration={2} separator='.' />
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
    </section>
  );
};

export { TotalField };
