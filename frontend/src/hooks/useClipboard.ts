'use client';

import { message } from 'antd';
import { SetStateAction, useState } from 'react';

export const useClipboard = (timeout = 2000) => {
  const [copiedField, setCopiedField] = useState('');

  const copyToClipboard = (text: string, field: SetStateAction<string>) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), timeout);
      message.success({ content: 'Sao chép thành công', key: 'copy' });
    });
  };

  return { copiedField, copyToClipboard };
};
