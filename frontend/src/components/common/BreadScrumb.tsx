'use client';

import { HomeOutlined } from '@ant-design/icons';
import { Breadcrumb } from 'antd';
import Link from 'next/link';
import React, { memo } from 'react';

interface BreadcrumbItem {
  href?: string;
  title: React.ReactNode;
}

interface BreadScrumbProps {
  items: BreadcrumbItem[];
}

const BreadScrumb = memo(({ items }: BreadScrumbProps) => {
  const breadcrumbItems = [
    {
      href: '/admin/statistic',
      title: <HomeOutlined />,
    },
    ...items,
  ];

  return (
    <Breadcrumb>
      {breadcrumbItems.map((item, index) => (
        <Breadcrumb.Item key={index}>
          {item.href ? <Link href={item.href}>{item.title}</Link> : item.title}
        </Breadcrumb.Item>
      ))}
    </Breadcrumb>
  );
});

BreadScrumb.displayName = 'BreadScrumb';

export { BreadScrumb };
