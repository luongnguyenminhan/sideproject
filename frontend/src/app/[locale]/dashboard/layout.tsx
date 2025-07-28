'use client';

import {
  BellOutlined,
  BuildOutlined,
  GiftOutlined,
  LogoutOutlined,
  ReadOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Avatar, Badge, Button, Dropdown, FloatButton, Layout, Menu, MenuProps, Space } from 'antd';
import Image from 'next/image';
import Link from 'next/link';
import { MenuItem } from './constants';
import { useSidebar } from './hooks/useSidebar';

const { Content, Sider, Footer } = Layout;

interface DashboardLayoutProps {
  readonly children: React.ReactNode;
}

function getItem(
  label: React.ReactNode,
  key: React.ReactNode,
  icon?: React.ReactNode,
  children?: MenuItem[],
  path?: string,
): MenuItem {
  return { key, icon, children, label, path } as MenuItem;
}

const items: MenuItem[] = [
  getItem('Dashboard', '1', <BuildOutlined />, undefined, '/dashboard/statistic'),
  getItem('User', '2', <UserOutlined />, undefined, '/dashboard/manage-member'),
  getItem('Package', '3', <GiftOutlined />, undefined, '/dashboard/manage-packages'),
  getItem('SubScription', '4', <ReadOutlined />, undefined, '/dashboard/manage-user-subscription'),
];

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const { collapsed, setCollapsed, selectedKeys, storeDefaultSelectedKeys } = useSidebar(items);

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined className='text-slate-500' />,
      label: (
        <div className='py-1'>
          <div className='font-medium text-slate-700'>Thông tin cá nhân</div>
          <div className='text-xs text-slate-500'>Xem và chỉnh sửa hồ sơ</div>
        </div>
      ),
    },
    {
      key: 'settings',
      icon: <SettingOutlined className='text-slate-500' />,
      label: (
        <div className='py-1'>
          <div className='font-medium text-slate-700'>Cài đặt</div>
          <div className='text-xs text-slate-500'>Tùy chỉnh hệ thống</div>
        </div>
      ),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined className='text-red-500' />,
      label: (
        <div className='py-1'>
          <div className='font-medium text-red-600'>Đăng xuất</div>
        </div>
      ),
      onClick: () => {
        console.log('Logout clicked');
      },
    },
  ];

  const notificationItems: MenuProps['items'] = [
    {
      key: 'notif1',
      label: (
        <div className='py-2 max-w-xs'>
          <div className='font-medium text-slate-700 text-sm'>Người dùng mới đăng ký</div>
          <div className='text-xs text-slate-500 mt-1'>John Doe vừa tạo tài khoản</div>
          <div className='text-xs text-blue-500 mt-1'>5 phút trước</div>
        </div>
      ),
    },
    {
      key: 'notif2',
      label: (
        <div className='py-2 max-w-xs'>
          <div className='font-medium text-slate-700 text-sm'>Cập nhật hệ thống</div>
          <div className='text-xs text-slate-500 mt-1'>Phiên bản 2.1.0 đã sẵn sàng</div>
          <div className='text-xs text-blue-500 mt-1'>1 giờ trước</div>
        </div>
      ),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'view-all',
      label: (
        <div className='text-center py-1'>
          <Button type='link' size='small' className='text-blue-600'>
            Xem tất cả thông báo
          </Button>
        </div>
      ),
    },
  ];

  const renderMenuItems = (items: MenuItem[]) =>
    items.map(item => {
      if (item.children && item.children.length > 0) {
        return (
          <Menu.SubMenu key={item.key} icon={item.icon} title={item.label}>
            {renderMenuItems(item.children)}
          </Menu.SubMenu>
        );
      }
      return (
        <Menu.Item
          key={item.key}
          icon={item.icon}
          onClick={() => storeDefaultSelectedKeys(item.key)}
        >
          {item.path ? <Link href={item.path}>{item.label}</Link> : item.label}
        </Menu.Item>
      );
    });

  return (
    <div className='min-h-screen bg-slate-50'>
      <div
        className={`fixed top-0 left-0 h-screen z-[1000] transition-all duration-300 ease-in-out ${
          collapsed ? 'w-[60px]' : 'w-[260px]'
        }`}
      >
        <Sider
          width={260}
          collapsedWidth={60}
          collapsed={collapsed}
          onCollapse={setCollapsed}
          breakpoint='lg'
          theme='light'
          collapsible
          className='h-full shadow-lg border-r border-slate-200 bg-white'
        >
          <div className='flex items-center justify-center py-6 px-4 border-b border-slate-100'>
            <div className='flex items-center gap-3 px-4 transition-all duration-300'>
              <div
                className={`w-10 h-10 rounded-full overflow-hidden transition-all duration-300 ${
                  collapsed ? 'mx-auto' : ''
                }`}
              >
                <Image
                  src='/assets/logo/logo_web.jpg'
                  alt='App Logo'
                  width={40}
                  height={40}
                  className='w-full h-full object-cover'
                />
              </div>

              {!collapsed && (
                <div className='flex flex-col overflow-hidden'>
                  <span className='text-xs font-bold text-slate-800 whitespace-nowrap'>
                    AdminHub
                  </span>
                  <span className='text-xs text-slate-500 whitespace-nowrap'>
                    Management System
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className='py-4'>
            <Menu theme='light' selectedKeys={selectedKeys} mode='inline' className='border-0'>
              {renderMenuItems(items)}
            </Menu>
          </div>
        </Sider>
      </div>

      <div
        className={`transition-all duration-300 ease-in-out ${
          collapsed ? 'ml-[60px]' : 'ml-[260px]'
        }`}
      >
        <div
          className='fixed top-0 right-0 h-16 z-[999] backdrop-blur-md bg-white/80 border-b border-slate-200 shadow-sm transition-all duration-300'
          style={{ left: collapsed ? '60px' : '260px' }}
        >
          <div className='flex items-center justify-end h-full px-6'>
            <Space size='large'>
              <Dropdown
                menu={{ items: notificationItems }}
                placement='bottomRight'
                trigger={['click']}
                popupRender={menu => (
                  <div className='bg-white rounded-lg shadow-xl border border-slate-200 min-w-[320px]'>
                    <div className='px-4 py-3 border-b border-slate-100'>
                      <h3 className='font-semibold text-slate-800'>Thông báo</h3>
                    </div>
                    {menu}
                  </div>
                )}
              >
                <Button
                  type='text'
                  shape='circle'
                  size='large'
                  className='flex items-center justify-center hover:bg-slate-100 transition-colors'
                >
                  <Badge count={2} size='small' offset={[-2, 2]}>
                    <BellOutlined className='text-slate-600 text-lg' />
                  </Badge>
                </Button>
              </Dropdown>

              <Dropdown
                menu={{ items: userMenuItems }}
                placement='bottomRight'
                trigger={['hover', 'click']}
                popupRender={menu => (
                  <div className='bg-white rounded-lg shadow-xl border border-slate-200 min-w-[280px]'>
                    <div className='px-4 py-4 border-b border-slate-100'>
                      <div className='flex items-center gap-3'>
                        <Avatar
                          size={48}
                          className='bg-gradient-to-br from-blue-500 to-purple-600'
                          icon={<UserOutlined />}
                        />
                        <div>
                          <div className='font-semibold text-slate-800'>Admin User</div>
                          <div className='text-sm text-slate-500'>admin@company.com</div>
                          <div className='text-xs text-emerald-600 font-medium mt-1'>
                            🏆 Super Administrator
                          </div>
                        </div>
                      </div>
                    </div>
                    {menu}
                  </div>
                )}
              >
                <div className='flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer'>
                  <Avatar
                    size={40}
                    className='bg-gradient-to-br from-blue-500 to-purple-600 shadow-md'
                    icon={<UserOutlined />}
                  />
                  <div className='text-left'>
                    <div className='font-semibold text-slate-800 text-sm'>Admin User</div>
                    <div className='text-xs text-emerald-600 font-medium'>Super Admin</div>
                  </div>
                </div>
              </Dropdown>
            </Space>
          </div>
        </div>

        <div className='pt-16'>
          <div className='min-h-[calc(100vh-64px)] flex flex-col'>
            {/* Content grow to push footer to bottom */}
            <Content className='flex-grow p-6'>
              <div className='bg-white border border-slate-200'>{children}</div>
            </Content>
            <Footer className='text-center'>
              Copyright ©2025 SideProject.inc. All right reserved
            </Footer>
          </div>
        </div>

        <FloatButton.BackTop
          style={{
            right: 24,
            bottom: 24,
          }}
          className='shadow-lg'
        />
      </div>
    </div>
  );
}
