import { getDictionary, createTranslator } from '@/utils/translation';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import AdminKBClient from './admin-kb-client';

async function AdminKBPage() {
  const locale = await getCurrentLocale();
  const dictionary = await getDictionary(locale);
  const t = createTranslator(dictionary);

  const translations = {
    title: t('admin.globalKB.title') || 'Quản lý Global Knowledge Base',
    description: t('admin.globalKB.description') || 'Upload và quản lý tài liệu cho Global Knowledge Base',
    uploadTitle: t('admin.globalKB.uploadTitle') || 'Upload Tài liệu',
    searchTitle: t('admin.globalKB.searchTitle') || 'Tìm kiếm & Test',
    statsTitle: t('admin.globalKB.statsTitle') || 'Thống kê',
    initializeBtn: t('admin.globalKB.initialize') || 'Khởi tạo KB',
    uploadBtn: t('admin.globalKB.upload') || 'Tải lên',
    searchBtn: t('admin.globalKB.search') || 'Tìm kiếm',
    documentTitle: t('admin.globalKB.documentTitle') || 'Tiêu đề tài liệu',
    documentContent: t('admin.globalKB.documentContent') || 'Nội dung tài liệu',
    category: t('admin.globalKB.category') || 'Danh mục',
    tags: t('admin.globalKB.tags') || 'Tags',
    searchQuery: t('admin.globalKB.searchQuery') || 'Câu hỏi tìm kiếm',
    results: t('admin.globalKB.results') || 'Kết quả',
    score: t('admin.globalKB.score') || 'Điểm số',
    source: t('admin.globalKB.source') || 'Nguồn',
    addDocument: t('admin.globalKB.addDocument') || 'Thêm tài liệu',
    removeDocument: t('admin.globalKB.removeDocument') || 'Xóa',
    success: t('success') || 'Thành công',
    error: t('error') || 'Lỗi',
    loading: t('loading') || 'Đang tải...',
    selectFile: t('admin.globalKB.selectFile') || 'Chọn file',
    fileSelected: t('admin.globalKB.fileSelected') || 'File đã chọn',
    dragDropText: t('admin.globalKB.dragDrop') || 'Kéo thả file hoặc click để chọn',
    supportedFormats: t('admin.globalKB.supportedFormats') || 'Hỗ trợ: TXT, PDF, DOC, DOCX',
  };

  return (
    <div className="min-h-screen bg-[color:var(--background)]">
      <div className="container mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[color:var(--foreground)] mb-2">
            {translations.title}
          </h1>
          <p className="text-[color:var(--muted-foreground)]">
            {translations.description}
          </p>
        </div>
        <AdminKBClient translations={translations} />
      </div>
    </div>
  );
}

export default AdminKBPage;