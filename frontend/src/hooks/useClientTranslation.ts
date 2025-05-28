'use client';

import { useParams } from 'next/navigation';
import { useMemo } from 'react';
import type { Locale } from '@/i18n.config';

// Client-side translation hook for components that need translations
// Note: This is for simple cases. For complex translations, pass them from Server Components
export function useClientTranslation() {
  const params = useParams();
  const locale = (params?.locale || 'vi') as Locale;

  const t = useMemo(() => {
    // Simple client-side translations for common cases
    const translations = {
      vi: {
        common: {
          loading: 'Đang tải...',
          error: 'Có lỗi xảy ra',
          success: 'Thành công',
          cancel: 'Hủy',
          confirm: 'Xác nhận',
        },
        auth: {
          loginSuccess: 'Đăng nhập thành công!',
          loginFailed: 'Đăng nhập thất bại',
        },
      },
      en: {
        common: {
          loading: 'Loading...',
          error: 'An error occurred',
          success: 'Success',
          cancel: 'Cancel',
          confirm: 'Confirm',
        },
        auth: {
          loginSuccess: 'Successfully signed in!',
          loginFailed: 'Login failed',
        },
      },
    };

    return function (key: string): string {
      const keys = key.split('.');
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let value: any = translations[locale];
      
      for (const k of keys) {
        value = value?.[k];
      }
      
      return typeof value === 'string' ? value : key;
    };
  }, [locale]);

  return { t, locale };
}
