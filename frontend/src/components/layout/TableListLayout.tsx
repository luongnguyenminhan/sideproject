'use client';
import { Typography } from 'antd';
import { ReactNode } from 'react';
import { BreadScrumb } from '../common/BreadScrumb';
import { LoadingSectionWrapper } from '../common/LoadingSectionWrapper';

interface CommonTableLayoutProps {
  title: string;
  breadcrumbItems: { href?: string; title: ReactNode }[];
  children?: ReactNode;
  isLoading?: boolean;
  subTitle: string;
}

const TableListLayout = ({
  title,
  breadcrumbItems = [],
  children,
  isLoading = false,
  subTitle,
}: CommonTableLayoutProps) => {
  const { Title, Text } = Typography;

  return (
    <main>
      {breadcrumbItems.length > 0 && <BreadScrumb items={breadcrumbItems} />}
      <LoadingSectionWrapper isLoading={isLoading}>
        <div className='flex flex-col gap-6 bg-gray-50 p-4 md:p-6'>
          <div className='mb-2'>
            <Title level={3} className='mb-1 text-primary'>
              {title}
            </Title>
            <Text type='secondary'>{subTitle}</Text>
          </div>
          <div className='rounded-xl bg-[#fff] p-5'>{children}</div>
        </div>
      </LoadingSectionWrapper>
    </main>
  );
};

export { TableListLayout };
