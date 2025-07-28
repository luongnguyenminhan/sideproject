/* eslint-disable react-hooks/exhaustive-deps */
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { normalizePath } from '../../../../lib/utils';
import { MenuItem } from '../constants';

const useSidebar = (items: MenuItem[]) => {
  const [collapsed, setCollapsed] = useState<boolean>(true);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const pathname = usePathname();

  const storeDefaultSelectedKeys = (key: string) => {
    sessionStorage.setItem('keys', key);
    setSelectedKeys([key]);
  };

  useEffect(() => {
    setCollapsed(true);
  }, []);

  const findMenuItem = (items: MenuItem[], path: string): MenuItem | undefined => {
    const normalizedPath = normalizePath(path);

    for (const item of items) {
      if (normalizedPath.startsWith(item.path as string)) return item;
      if (item.children) {
        const found = findMenuItem(item.children, normalizedPath);
        if (found) return found;
      }
    }
    return undefined;
  };

  useEffect(() => {
    const matchedItem = findMenuItem(items, pathname);
    if (matchedItem) {
      setSelectedKeys([matchedItem.key]);
      storeDefaultSelectedKeys(matchedItem.key);
    }
  }, [pathname, items, findMenuItem]);

  return {
    collapsed,
    setCollapsed,
    selectedKeys,
    storeDefaultSelectedKeys,
  };
};

export { useSidebar };
