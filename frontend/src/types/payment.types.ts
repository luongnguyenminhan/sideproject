export interface PayOSPaymentData {
  code: string; // e.g., '00'
  id: string; // e.g., 'PAYOS2024112812345678'
  cancel: 'true' | 'false'; // hoặc boolean nếu backend trả về kiểu boolean
  status: 'PAID' | 'UNPAID' | 'CANCELLED' | string;
  orderCode: string; // e.g., 'ORD2024112812345'
  amount: number;
  accountNumber?: string;
  accountName?: string;
  description?: string;
  reference?: string;
  transactionDateTime?: string; // ISO format date string
  paymentLinkId?: string;
  currency?: string; // e.g., 'VND'
  paymentMethod?: string; // e.g., 'BANK_TRANSFER'
  bankCode?: string; // e.g., 'VCB'
  bankName?: string; // e.g., 'Vietcombank'
  // Bạn có thể thêm các field mở rộng ở đây nếu cần
}
