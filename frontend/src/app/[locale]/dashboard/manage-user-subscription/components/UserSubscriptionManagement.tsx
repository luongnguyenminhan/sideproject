/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { SearchAndAdd } from '../../../../../components/common/table/SearchAndAdd';
import { TableCustom } from '../../../../../components/common/table/TableCustom';
import { TableListLayout } from '../../../../../components/layout/TableListLayout';
import { formatAmount } from '../../../../../lib/utils';

export interface Subscription {
  user_id: string;
  order_code: string;
  rank_type: 'BASIC' | 'PRO' | 'ULTRA';
  amount: number;
  status: 'PENDING' | 'COMPLETED' | 'CANCELED' | 'EXPIRED';
  payment_link_id: string | null;
  checkout_url: string | null;
  transaction_id: string | null;
  created_at: string | null;
  expired_at: string;
  activated_at: string | null;
  expired_subscription_at: string | null;
  cancel_reason: string | null;
  id: string;
  create_date: string | null;
  update_date: string | null;
  is_deleted: boolean | null;
}

const UserSubscriptionManagement = () => {
  const [, setSearchQuery] = useState('');
  const [pageIndex, setPageIndex] = useState(1);
  const [dataSource, setDataSource] = useState<Subscription[]>([]);

  const [loading, setLoading] = useState(false);
  const pageSize = 10;

  const token =
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTM4ODA1ODgsImlhdCI6MTc1MzcwMDU4OCwiaXNzIjoiZnByb2plY3QtYXBpIiwiYXVkIjoiZnByb2plY3QtY2xpZW50IiwidXNlcl9pZCI6IjRlMTYzOTZiLTYwZjktNDI2Yi1hMGJkLWI0M2YzNzE1YzU5NyIsImVtYWlsIjoiZ2lhZHVjZGFuZ0BnbWFpbC5jb20iLCJyb2xlIjoidXNlciJ9.ThBJq1mEwtFfTBqZnvbTQ54eoyf3GzrQAzrrhRhA6Lg';

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const response = await fetch(
          `https://api.wc504.io.vn/api/v1/subscription/?page=${pageIndex}&page_size=${pageSize}`,
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
          },
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setDataSource(data.data.items);
      } catch (error) {
        console.error('Error fetching users:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [pageIndex]);

  const handleOpenModalAdd = () => {
    console.log('Open add modal');
  };

  const handleOpenModalEdit = (record: Subscription) => {
    console.log('Edit record:', record);
  };

  const handleDeleteSubCategory = (id: string) => {
    console.log('Delete user with id:', id);
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
        render: (_: any, _record: Subscription, index: number) =>
          (pageIndex - 1) * pageSize + index + 1,
      },
      {
        title: 'Mã đơn hàng',
        dataIndex: 'order_code',
        width: '15%',
      },
      {
        title: 'Gói đăng ký',
        dataIndex: 'rank_type',
        width: '10%',
        render: (type: Subscription['rank_type']) => {
          switch (type) {
            case 'BASIC':
              return 'Cơ bản';
            case 'PRO':
              return 'Chuyên nghiệp';
            case 'ULTRA':
              return 'Cao cấp';
            default:
              return type;
          }
        },
      },
      {
        title: 'Trạng thái',
        dataIndex: 'status',
        width: '10%',
        render: (status: Subscription['status']) => {
          switch (status) {
            case 'PENDING':
              return 'Chờ thanh toán';
            case 'COMPLETED':
              return 'Hoàn tất';
            case 'CANCELED':
              return 'Đã hủy';
            case 'EXPIRED':
              return 'Hết hạn';
            default:
              return status;
          }
        },
      },
      {
        title: 'Số tiền (VND)',
        dataIndex: 'amount',
        width: '10%',
        render: (amount: number) => formatAmount(amount),
      },
      {
        title: 'Ngày tạo',
        dataIndex: 'created_at',
        width: '12%',
      },
      {
        title: 'Ngày kích hoạt',
        dataIndex: 'activated_at',
        width: '12%',
      },
      {
        title: 'Ngày hết hạn',
        dataIndex: 'expired_subscription_at',
        width: '12%',
      },
      {
        title: 'Lý do hủy',
        dataIndex: 'cancel_reason',
        width: '15%',
        render: (reason: string | null) => reason || '—',
      },
      {
        title: 'Chức năng',
        dataIndex: '',
        width: '10%',
        render: (_: any, record: Subscription) => (
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
      title='Quản lý gói đăng ký'
      subTitle='Danh sách gói đăng ký hiện có trong hệ thống'
      breadcrumbItems={[]}
    >
      <SearchAndAdd
        searchPlaceholder='Tìm kiếm gói đăng ký'
        addButtonText='Thêm gói đăng ký'
        onSearch={setSearchQuery}
        onAddClick={handleOpenModalAdd}
      />
      <TableCustom
        title='Danh sách gói đăng ký'
        columns={columns}
        dataSource={dataSource}
        pagination={{
          current: pageIndex,
          pageSize: pageSize,
        }}
        onChange={handlePageChange}
        loading={loading}
        rowKey={(record: Subscription) => record.id}
      />
    </TableListLayout>
  );
};

export { UserSubscriptionManagement };
