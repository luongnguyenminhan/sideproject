'use client';

import { Spin } from 'antd';
import { Check, CheckCircle, Clock, Copy, Info, Receipt, Star, XCircle } from 'lucide-react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useClipboard } from '../../hooks/useClipboard';
import { formatAmount, formatDate } from '../../lib/utils';
import { PayOSPaymentData } from '../../types/payment.types';

const PayOSReturn = () => {
  const [paymentData, setPaymentData] = useState<PayOSPaymentData>();
  const { copiedField, copyToClipboard } = useClipboard();
  const router = useRouter();

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);

    const data: Record<string, string> = {};

    for (const [key, value] of urlParams.entries()) {
      data[key] = decodeURIComponent(value);
    }

    // nếu không có dữ liệu thì sử dụng data mock
    if (Object.keys(data).length === 0) {
      // const mockData = {
      //   code: '00',
      //   id: 'PAYOS2024112812345678',
      //   cancel: 'false',
      //   status: 'PAID',
      //   orderCode: 'ORD2024112812345',
      //   amount: 299000,
      //   // Thêm các field khác nếu PayOS trả về
      //   accountNumber: '0123456789',
      //   accountName: 'NGUYEN VAN A',
      //   description: 'Thanh toan goi dich vu Premium',
      //   reference: 'REF2024112812345',
      //   transactionDateTime: '2024-11-28T10:30:00Z',
      //   paymentLinkId: 'LINK2024112812345',
      //   // Có thể thêm thông tin khác
      //   currency: 'VND',
      //   paymentMethod: 'BANK_TRANSFER',
      //   bankCode: 'VCB',
      //   bankName: 'Vietcombank',
      // };
      router.push('/');

      // setPaymentData(mockData);
      return;
    }

    setPaymentData(data as unknown as PayOSPaymentData);
  }, [router]);

  // xác định trạng thái thanh toán dựa vào params từ PayOS
  const getStatusInfo = (code: string, status: string, cancel: string) => {
    // PayOS trả về code="00" và status="PAID" khi thành công
    if (code === '00' && status === 'PAID') {
      return {
        status: 'Thành công',
        message: 'THANH TOÁN THÀNH CÔNG',
        icon: CheckCircle,
        color: 'text-green-600',
        bgColor: 'bg-green-500',
      };
    } else if (cancel === 'true' || status === 'CANCELLED') {
      return {
        status: 'Đã hủy',
        message: 'THANH TOÁN ĐÃ BỊ HỦY',
        icon: XCircle,
        color: 'text-red-600',
        bgColor: 'bg-red-500',
      };
    } else if (status === 'PENDING') {
      return {
        status: 'Đang chờ',
        message: 'ĐANG XỬ LÝ',
        icon: Clock,
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-500',
      };
    } else {
      return {
        status: 'Thất bại',
        message: 'THANH TOÁN THẤT BẠI',
        icon: XCircle,
        color: 'text-red-600',
        bgColor: 'bg-red-500',
      };
    }
  };

  // format số tiền cho PayOS (PayOS thường trả về số tiền dạng number)

  // mapping response code message cho PayOS
  const getResponseCodeMessage = (code: string, status: string) => {
    if (code === '00' && status === 'PAID') {
      return 'Giao dịch thành công';
    } else if (status === 'CANCELLED') {
      return 'Giao dịch bị hủy bởi người dùng';
    } else if (status === 'PENDING') {
      return 'Giao dịch đang được xử lý';
    } else {
      return 'Giao dịch thất bại';
    }
  };

  // hiển thị loading khi chưa có dữ liệu
  if (!paymentData) {
    return (
      <div className='min-h-screen bg-gray-100 flex items-center justify-center'>
        <Spin size='large' />
      </div>
    );
  }

  const statusInfo = getStatusInfo(paymentData?.code, paymentData?.status, paymentData?.cancel);
  const StatusIcon = statusInfo?.icon;

  // kiểm tra thanh toán thành công hay không
  const isPaymentSuccessful = paymentData?.code === '00' && paymentData?.status === 'PAID';

  return (
    <div className='min-h-screen bg-gray-100 py-8 px-4'>
      <div className='max-w-2xl mx-auto'>
        <div className='bg-white shadow-2xl rounded-t-3xl border-b-4 border-green-600 overflow-hidden'>
          <div className='bg-gradient-to-r from-green-600 to-green-700 text-white p-6'>
            <div className='flex items-center justify-between'>
              <div className='flex gap-4 items-center'>
                <Image
                  src={'https://casso.vn/wp-content/uploads/2024/11/casso-logo-with-catowl.svg'}
                  alt='payos_logo'
                  className='w-12 h-12 bg-white rounded'
                  width={48}
                  height={48}
                />
                <div>
                  <h1 className='text-2xl font-bold'>PayOS</h1>
                  <p className='text-green-100 text-sm'>Cổng thanh toán điện tử</p>
                </div>
              </div>
              <div className='text-right'>
                <Receipt className='w-12 h-12 text-green-200 mb-2' />
                <div className='text-xs text-green-100'>HÓA ĐƠN ĐIỆN TỬ</div>
              </div>
            </div>
          </div>

          <div className={`${statusInfo.bgColor} text-white py-4 px-6`}>
            <div className='flex items-center justify-center'>
              <StatusIcon className='w-6 h-6 mr-3' />
              <span className='text-lg font-bold tracking-wide'>{statusInfo.message}</span>
            </div>
          </div>

          <div className='p-6 bg-white'>
            <div className='flex justify-between items-start mb-6 pb-4 border-b-2 border-dashed border-gray-200'>
              <div>
                <h2 className='text-lg font-bold text-gray-800 mb-1'>HÓA ĐƠN THANH TOÁN</h2>
                <p className='text-sm text-gray-600'>Mã đơn hàng: {paymentData?.orderCode}</p>
              </div>
              <div className='text-right'>
                <div
                  className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${statusInfo.color} bg-gray-100`}
                >
                  {statusInfo.status}
                </div>
                {paymentData?.transactionDateTime && (
                  <p className='text-xs text-gray-500 mt-1'>
                    {formatDate(paymentData?.transactionDateTime)}
                  </p>
                )}
              </div>
            </div>

            <div className='space-y-4'>
              <div className='bg-gray-50 rounded-xl p-4 border-l-4 border-green-500'>
                <div className='flex justify-between items-center'>
                  <div>
                    <h3 className='font-semibold text-gray-800'>Chi tiết thanh toán</h3>
                    <p className='text-sm text-gray-600 mt-1'>
                      {paymentData?.description || 'Thanh toán gói dịch vụ'}
                    </p>
                  </div>
                  <div className='text-right'>
                    <div className='text-2xl font-bold text-green-600'>
                      {formatAmount(paymentData?.amount)}
                    </div>
                    <div className='text-xs text-gray-500'>Đã bao gồm VAT</div>
                  </div>
                </div>
              </div>

              <div className='bg-white border border-gray-600 rounded-xl overflow-hidden'>
                <div className='bg-gray-50 px-4 py-3 border-b'>
                  <h4 className='font-semibold text-gray-800 flex items-center'>
                    <Info className='w-4 h-4 mr-2' />
                    Thông tin giao dịch
                  </h4>
                </div>

                <div className='divide-y divide-gray-100'>
                  <div className='px-4 py-3 flex justify-between items-center'>
                    <span className='text-gray-600 text-sm'>Mã đơn hàng</span>
                    <div className='flex items-center'>
                      <span className='font-mono text-sm font-medium mr-2 text-black'>
                        {paymentData?.orderCode}
                      </span>
                      <button
                        onClick={() => copyToClipboard(paymentData?.orderCode, 'orderCode')}
                        className='text-gray-400 hover:text-green-600 transition-colors'
                      >
                        {copiedField === 'orderCode' ? (
                          <Check className='w-4 h-4 text-green-600' />
                        ) : (
                          <Copy className='w-4 h-4' />
                        )}
                      </button>
                    </div>
                  </div>

                  {paymentData?.id && (
                    <div className='px-4 py-3 flex justify-between items-center'>
                      <span className='text-gray-600 text-sm'>Mã giao dịch</span>
                      <div className='flex items-center'>
                        <span className='font-mono text-sm font-medium mr-2 text-black'>
                          {paymentData?.id}
                        </span>
                        <button
                          onClick={() => copyToClipboard(paymentData?.id, 'transactionId')}
                          className='text-gray-400 hover:text-green-600 transition-colors'
                        >
                          {copiedField === 'transactionId' ? (
                            <Check className='w-4 h-4 text-green-600' />
                          ) : (
                            <Copy className='w-4 h-4' />
                          )}
                        </button>
                      </div>
                    </div>
                  )}

                  {paymentData?.bankCode && (
                    <div className='px-4 py-3 flex justify-between items-center'>
                      <span className='text-gray-600 text-sm'>Ngân hàng</span>
                      <span className='font-medium text-sm text-black'>
                        {paymentData?.bankName || paymentData?.bankCode}
                      </span>
                    </div>
                  )}

                  {paymentData?.accountNumber && (
                    <div className='px-4 py-3 flex justify-between items-center'>
                      <span className='text-gray-600 text-sm'>Số tài khoản</span>
                      <span className='font-medium text-sm text-black'>
                        {paymentData?.accountNumber}
                      </span>
                    </div>
                  )}

                  {paymentData?.accountName && (
                    <div className='px-4 py-3 flex justify-between items-center'>
                      <span className='text-gray-600 text-sm'>Chủ tài khoản</span>
                      <span className='font-medium text-sm text-black'>
                        {paymentData?.accountName}
                      </span>
                    </div>
                  )}

                  <div className='px-4 py-3 flex justify-between items-center'>
                    <span className='text-gray-600 text-sm'>Phương thức</span>
                    <span className='font-medium text-sm text-black'>
                      {paymentData?.paymentMethod === 'BANK_TRANSFER'
                        ? 'Chuyển khoản ngân hàng'
                        : paymentData?.paymentMethod || 'PayOS'}
                    </span>
                  </div>

                  {paymentData?.reference && (
                    <div className='px-4 py-3 flex justify-between items-center'>
                      <span className='text-gray-600 text-sm'>Mã tham chiếu</span>
                      <div className='flex items-center'>
                        <span className='font-mono text-sm font-medium mr-2 text-black'>
                          {paymentData?.reference}
                        </span>
                        <button
                          onClick={() =>
                            paymentData?.reference &&
                            copyToClipboard(paymentData.reference, 'reference')
                          }
                          className='text-gray-400 hover:text-green-600 transition-colors'
                        >
                          {copiedField === 'reference' ? (
                            <Check className='w-4 h-4 text-green-600' />
                          ) : (
                            <Copy className='w-4 h-4' />
                          )}
                        </button>
                      </div>
                    </div>
                  )}

                  {paymentData?.transactionDateTime && (
                    <div className='px-4 py-3 flex justify-between items-center'>
                      <span className='text-gray-600 text-sm'>Thời gian giao dịch</span>
                      <span className='font-medium text-sm text-black'>
                        {formatDate(paymentData?.transactionDateTime)}
                      </span>
                    </div>
                  )}

                  <div className='px-4 py-3 flex justify-between'>
                    <span className='text-gray-600 text-sm block mb-1'>Trạng thái</span>
                    <span className='text-sm text-gray-700 italic '>
                      {getResponseCodeMessage(paymentData?.code, paymentData?.status)}
                    </span>
                  </div>
                </div>
              </div>

              {/* tổng cộng chỉ hiển thị khi thanh toán thành công */}
              {isPaymentSuccessful && (
                <div className='bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 border-2 border-green-100'>
                  <div className='flex justify-between items-center'>
                    <div>
                      <h3 className='font-bold text-gray-800'>TỔNG CỘNG</h3>
                      <p className='text-xs text-gray-600'>Số tiền đã thanh toán</p>
                    </div>
                    <div className='text-right'>
                      <div className='text-3xl font-extrabold text-green-600'>
                        {formatAmount(paymentData?.amount)}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Hiển thị thông báo lỗi nếu thanh toán thất bại */}
              {(paymentData?.cancel === 'true' || paymentData?.status === 'CANCELLED') && (
                <div className='bg-red-50 border border-red-200 rounded-xl p-4'>
                  <div className='flex items-start'>
                    <XCircle className='w-5 h-5 text-red-600 mr-3 mt-0.5' />
                    <div>
                      <h4 className='font-semibold text-red-800'>Thanh toán đã bị hủy</h4>
                      <p className='text-sm text-red-600 mt-1'>
                        Giao dịch của bạn đã bị hủy. Vui lòng thử lại hoặc liên hệ hỗ trợ.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Hiển thị thông báo pending */}
              {paymentData?.status === 'PENDING' && (
                <div className='bg-yellow-50 border border-yellow-200 rounded-xl p-4'>
                  <div className='flex items-start'>
                    <Clock className='w-5 h-5 text-yellow-600 mr-3 mt-0.5' />
                    <div>
                      <h4 className='font-semibold text-yellow-800'>Đang xử lý thanh toán</h4>
                      <p className='text-sm text-yellow-600 mt-1'>
                        Giao dịch của bạn đang được xử lý. Vui lòng chờ trong giây lát.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className='bg-gray-50 px-6 py-4 border-t border-gray-300'>
            <div className='text-center'>
              <div className='flex items-center justify-center mb-2'>
                <Star className='w-4 h-4 text-yellow-400 mr-1' />
                <span className='text-sm text-gray-600'>Cảm ơn bạn đã sử dụng dịch vụ!</span>
              </div>
              <p className='text-xs text-gray-500'>Hóa đơn được tạo tự động bởi hệ thống PayOS</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PayOSReturn;
