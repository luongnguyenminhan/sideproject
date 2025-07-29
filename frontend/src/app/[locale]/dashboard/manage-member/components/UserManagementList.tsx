/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { SearchAndAdd } from '../../../../../components/common/table/SearchAndAdd';
import { TableCustom } from '../../../../../components/common/table/TableCustom';
import { TableListLayout } from '../../../../../components/layout/TableListLayout';
import Image from 'next/image';

// Type cho người dùng
export interface User {
  id: string;
  email: string;
  role: string;
  name: string;
  username: string;
  confirmed: boolean;
  create_date: string;
  update_date: string;
  profile_picture: string;
  first_name: string;
  last_name: string;
  locale: string | null;
  google_id: string;
  access_token: string | null;
  refresh_token: string | null;
  token_type: string | null;
}

const UserManagementList = () => {
  const [, setSearchQuery] = useState('');
  const [pageIndex, setPageIndex] = useState(1);
  const [dataSource, setDataSource] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const pageSize = 10;

  const token =
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTM4ODA1ODgsImlhdCI6MTc1MzcwMDU4OCwiaXNzIjoiZnByb2plY3QtYXBpIiwiYXVkIjoiZnByb2plY3QtY2xpZW50IiwidXNlcl9pZCI6IjRlMTYzOTZiLTYwZjktNDI2Yi1hMGJkLWI0M2YzNzE1YzU5NyIsImVtYWlsIjoiZ2lhZHVjZGFuZ0BnbWFpbC5jb20iLCJyb2xlIjoidXNlciJ9.ThBJq1mEwtFfTBqZnvbTQ54eoyf3GzrQAzrrhRhA6Lg';

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const response = await fetch(
          `https://api.wc504.io.vn/api/v1/users/?page=${pageIndex}&page_size=${pageSize}`,
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

  const handleOpenModalEdit = (record: User) => {
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
        render: (_: any, _record: User, index: number) => (pageIndex - 1) * pageSize + index + 1,
      },
      {
        title: 'Ảnh',
        dataIndex: 'profile_picture',
        width: '8%',
        render: (url: string) => (
          <Image
            src={url}
            alt='avatar'
            width={40}
            height={40}
            className='w-10 h-10 rounded-full object-cover border'
          />
        ),
      },
      {
        title: 'Họ và tên',
        dataIndex: 'name',
        width: '20%',
      },
      {
        title: 'Tên đăng nhập',
        dataIndex: 'username',
        width: '15%',
      },
      {
        title: 'Email',
        dataIndex: 'email',
        width: '20%',
      },
      {
        title: 'Vai trò',
        dataIndex: 'role',
        width: '10%',
        render: (role: string) => (role === 'admin' ? 'Quản trị viên' : 'Người dùng'),
      },
      {
        title: 'Trạng thái',
        dataIndex: 'confirmed',
        width: '10%',
        render: (confirmed: boolean) => (confirmed ? 'Đã xác minh' : 'Chưa xác minh'),
      },
      {
        title: 'Ngày tạo',
        dataIndex: 'create_date',
        width: '12%',
        render: (date: string) => new Date(date).toLocaleDateString(),
      },
      {
        title: 'Chức năng',
        dataIndex: '',
        width: '10%',
        render: (_: any, record: User) => (
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
      title='Quản lý người dùng'
      subTitle='Danh sách người dùng hiện có trong hệ thống'
      breadcrumbItems={[]}
    >
      <SearchAndAdd
        searchPlaceholder='Tìm kiếm người dùng'
        addButtonText='Thêm người dùng'
        onSearch={setSearchQuery}
        onAddClick={handleOpenModalAdd}
      />
      <TableCustom
        title='Danh sách người dùng'
        columns={columns}
        dataSource={dataSource}
        pagination={{
          current: pageIndex,
          pageSize: pageSize,
        }}
        onChange={handlePageChange}
        loading={loading}
        rowKey={(record: User) => record.id}
      />
    </TableListLayout>
  );
};

export { UserManagementList };
