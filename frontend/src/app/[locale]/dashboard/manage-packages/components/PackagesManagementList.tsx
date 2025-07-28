/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useMemo, useState } from 'react';
import { SearchAndAdd } from '../../../../../components/common/table/SearchAndAdd';
import { TableCustom } from '../../../../../components/common/table/TableCustom';
import { TableListLayout } from '../../../../../components/layout/TableListLayout';
import { formatAmount } from '../../../../../lib/utils';

const mockData = [
  {
    id: 1,
    code: 'PK001',
    price: 29000,
    name: 'Gói 1',
    description: 'Gói cơ bản',
    createdDate: '2025-07-01T12:00:00Z',
  },
  {
    id: 2,
    code: 'PK002',
    price: 49000,
    name: 'Gói 2',
    description: 'Gói nâng cao',
    createdDate: '2025-07-01T12:00:00Z',
  },
  {
    id: 3,
    code: 'PK003',
    price: 79000,
    name: 'Gói 2',
    description: 'Gói chuyên sâu',
    createdDate: '2025-07-05T10:30:00Z',
  },
];

const PackagesManagementList = () => {
  const [, setSearchQuery] = useState('');
  const [pageIndex, setPageIndex] = useState(1);
  const pageSize = 10;

  const handleOpenModalAdd = () => {
    console.log('Open add modal');
  };

  const handleOpenModalEdit = (record: any) => {
    console.log('Edit record:', record);
  };

  const handleDeleteSubCategory = (id: number) => {
    console.log('Delete subcategory with id:', id);
  };

  const handlePageChange = (pagination: any) => {
    setPageIndex(pagination.current);
  };

  const columns = useMemo(
    () => [
      {
        title: 'STT',
        dataIndex: 'index',
        key: 'index',
        width: '5%',
        render: (_: any, _record: any, index: number) => (pageIndex - 1) * pageSize + index + 1,
      },
      {
        title: 'Mã gói',
        dataIndex: 'code',
        width: '15%',
      },
      {
        title: 'Gói dịch vụ',
        dataIndex: 'name',
        width: '20%',
      },
      {
        title: 'Giá',
        dataIndex: 'price',
        width: '7%',
        render: (item: string) => <div className='text-primary'>{formatAmount(item)}</div>,
      },
      {
        title: 'Mô tả',
        dataIndex: 'description',
        width: '30%',
      },
      {
        title: 'Ngày tạo',
        dataIndex: 'createdDate',
        width: '12%',
        render: (date: string) => new Date(date).toLocaleDateString(),
      },
      {
        title: 'Chức năng',
        dataIndex: '',
        width: '15%',
        render: (_: any, record: any) => (
          <div className='flex items-center justify-center gap-2'>
            <Button
              size='small'
              className='flex items-center justify-center !border-none !bg-transparent !shadow-none'
              onClick={() => handleOpenModalEdit(record)}
            >
              <EditOutlined className='text-primary' />
            </Button>
            <Button
              onClick={() => handleDeleteSubCategory(record.id)}
              danger
              size='small'
              className='flex items-center justify-center !border-none !bg-transparent !shadow-none'
            >
              <DeleteOutlined />
            </Button>
          </div>
        ),
      },
    ],
    [pageIndex],
  );

  return (
    <TableListLayout
      title='Quản lý gói dịch vụ'
      subTitle='Danh sách gói dịch vụ hiện có trong hệ thống'
      breadcrumbItems={[]}
    >
      <SearchAndAdd
        searchPlaceholder='Tìm kiếm gói'
        addButtonText='Thêm gói dịch vụ'
        onSearch={setSearchQuery}
        onAddClick={handleOpenModalAdd}
      />
      <TableCustom
        title='Danh sách gói dịch vụ'
        columns={columns}
        dataSource={mockData}
        pagination={{
          current: pageIndex,
          total: 20,
          pageSize: pageSize,
        }}
        onChange={handlePageChange}
        loading={false}
        rowKey={(record: { id: number }) => record.id}
      />
    </TableListLayout>
  );
};

export { PackagesManagementList };
