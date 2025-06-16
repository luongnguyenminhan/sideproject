/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';
import { useState, useCallback } from 'react';
import { globalKBAPI } from '@/apis/global-kb-api';
import type {
  AdminDocumentData,
  GlobalKBSearchResult,
  GlobalKBStats,
  UploadGlobalKBFileResponse,
} from '@/types/global-kb.type';

interface AdminKBClientProps {
  translations: Record<string, string>;
}

function AdminKBClient({ translations }: AdminKBClientProps) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [documents, setDocuments] = useState<AdminDocumentData[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<GlobalKBSearchResult[]>([]);
  const [stats, setStats] = useState<GlobalKBStats | null>(null);
  const [, setSelectedFile] = useState<File | null>(null);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  // Initialize Global KB
  const handleInitialize = async () => {
    try {
      setLoading(true);
      const response = await globalKBAPI.initialize({ include_defaults: true });
      if (response.error_code === 0) {
        showMessage('success', translations.success);
        await fetchStats();
      } else {
        showMessage('error', response.message);
      }
    } catch (error: any) {
      showMessage('error', error.message || translations.error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch stats
  const fetchStats = async () => {
    try {
      const response = await globalKBAPI.getStats();
      if (response.error_code === 0) {
        setStats(response.data as GlobalKBStats);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  // Handle file upload
  const handleFileUpload = useCallback(async (file: File) => {
    try {
      setLoading(true);
      const uploaded: UploadGlobalKBFileResponse = await globalKBAPI.uploadFile(file);
      setDocuments((prev) => [
        ...prev,
        {
          title: uploaded.title,
          content: uploaded.source, // content là url
          category: uploaded.category,
          tags: uploaded.tags,
          source: uploaded.source,
        },
      ]);
      showMessage('success', `File "${file.name}" đã được upload thành công!`);
    } catch (error: any) {
      showMessage('error', error.message || translations.error);
    } finally {
      setLoading(false);
      setSelectedFile(null);
    }
  }, [translations.error]);

  // Handle drag and drop
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, [handleFileUpload]);

  // Upload documents to Global KB
  const handleUploadDocuments = async () => {
    try {
      setLoading(true);
      const validDocs = documents.filter(doc => doc.title.trim() && doc.content.trim());
      if (validDocs.length === 0) {
        showMessage('error', 'Vui lòng thêm ít nhất một tài liệu có tiêu đề và nội dung');
        return;
      }
      const response = await globalKBAPI.indexAdminDocuments({ documents: validDocs });
      if (response.error_code === 0) {
        showMessage('success', `Đã upload thành công ${response.data?.indexed_count || validDocs.length} tài liệu!`);
        setDocuments([]);
        await fetchStats();
      } else {
        showMessage('error', response.message);
      }
    } catch (error: any) {
      showMessage('error', error.message || translations.error);
    } finally {
      setLoading(false);
    }
  };

  // Search Global KB
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      showMessage('error', 'Vui lòng nhập câu hỏi tìm kiếm');
      return;
    }
    try {
      setLoading(true);
      const response = await globalKBAPI.search({ query: searchQuery, top_k: 5 });
      if (response.error_code === 0) {
        setSearchResults(response.data?.results || []);
        showMessage('success', `Tìm thấy ${response.data?.total_results} kết quả`);
      } else {
        showMessage('error', response.message);
      }
    } catch (error: any) {
      showMessage('error', error.message || translations.error);
    } finally {
      setLoading(false);
    }
  };

  // Remove document
  const removeDocument = (index: number) => {
    if (documents.length > 1) {
      setDocuments(documents.filter((_, i) => i !== index));
    } else {
      setDocuments([]);
    }
  };

  // Update document
  const updateDocument = (index: number, field: keyof AdminDocumentData, value: any) => {
    const updatedDocs = [...documents];
    if (field === 'tags' && typeof value === 'string') {
      updatedDocs[index][field] = value.split(',').map(tag => tag.trim()).filter(Boolean);
    } else {
      (updatedDocs[index] as any)[field] = value;
    }
    setDocuments(updatedDocs);
  };

  useState(() => {
    fetchStats();
  });

  return (
    <div className="space-y-8">
      {/* Message Display */}
      {message && (
        <div className={`p-4 rounded-lg ${
          message.type === 'success'
            ? 'bg-green-50 text-green-800 border border-green-200'
            : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          {message.text}
        </div>
      )}

      {/* Stats Section */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-[color:var(--foreground)]">
            {translations.statsTitle}
          </h2>
          <button
            onClick={handleInitialize}
            disabled={loading}
            className="px-4 py-2 bg-[color:var(--primary)] text-[color:var(--primary-foreground)] rounded-lg hover:opacity-90 disabled:opacity-50"
          >
            {loading ? translations.loading : translations.initializeBtn}
          </button>
        </div>
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-[color:var(--muted)] rounded-lg">
              <p className="text-sm text-[color:var(--muted-foreground)]">Collection</p>
              <p className="font-semibold text-[color:var(--foreground)]">{stats.collection_name}</p>
            </div>
            <div className="p-4 bg-[color:var(--muted)] rounded-lg">
              <p className="text-sm text-[color:var(--muted-foreground)]">Status</p>
              <p className="font-semibold text-[color:var(--foreground)]">{stats.status}</p>
            </div>
            <div className="p-4 bg-[color:var(--muted)] rounded-lg">
              <p className="text-sm text-[color:var(--muted-foreground)]">Exists</p>
              <p className="font-semibold text-[color:var(--foreground)]">{stats.exists ? 'Yes' : 'No'}</p>
            </div>
          </div>
        )}
      </div>

      {/* Upload Section */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6">
        <h2 className="text-xl font-semibold text-[color:var(--foreground)] mb-4">
          {translations.uploadTitle}
        </h2>
        {/* File Upload Area */}
        <div
          className="border-2 border-dashed border-[color:var(--border)] rounded-lg p-8 text-center mb-6 hover:border-[color:var(--primary)] transition-colors"
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
        >
          <input
            type="file"
            id="fileInput"
            accept=".txt,.pdf,.doc,.docx"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                setSelectedFile(file);
                handleFileUpload(file);
              }
            }}
            className="hidden"
          />
          <label htmlFor="fileInput" className="cursor-pointer">
            <div className="space-y-2">
              <div className="text-3xl">📁</div>
              <p className="text-[color:var(--foreground)] font-medium">
                {translations.dragDropText}
              </p>
              <p className="text-sm text-[color:var(--muted-foreground)]">
                {translations.supportedFormats}
              </p>
            </div>
          </label>
        </div>
        {/* Document Forms */}
        <div className="space-y-4">
          {documents.map((doc, index) => (
            <div key={index} className="border border-[color:var(--border)] rounded-lg p-4">
              <div className="flex justify-between items-center mb-4">
                <span className="font-semibold">{doc.title}</span>
                <button
                  onClick={() => removeDocument(index)}
                  className="text-red-500 hover:underline"
                >
                  {translations.removeDocument}
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <input
                  type="text"
                  value={doc.title}
                  onChange={(e) => updateDocument(index, 'title', e.target.value)}
                  className="w-full px-3 py-2 border border-[color:var(--border)] rounded-lg bg-[color:var(--background)] text-[color:var(--foreground)]"
                  placeholder={translations.documentTitle}
                />
                <input
                  type="text"
                  value={doc.category}
                  onChange={(e) => updateDocument(index, 'category', e.target.value)}
                  className="w-full px-3 py-2 border border-[color:var(--border)] rounded-lg bg-[color:var(--background)] text-[color:var(--foreground)]"
                  placeholder={translations.category}
                />
              </div>
              <div className="mb-4">
                <input
                  type="text"
                  value={doc.tags.join(', ')}
                  onChange={(e) => updateDocument(index, 'tags', e.target.value)}
                  className="w-full px-3 py-2 border border-[color:var(--border)] rounded-lg bg-[color:var(--background)] text-[color:var(--foreground)]"
                  placeholder="tag1, tag2, tag3..."
                />
              </div>
              <div className="mb-2">
                <a href={doc.content} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                  {translations.source}
                </a>
              </div>
            </div>
          ))}
        </div>
        <div className="flex gap-4 mt-6">
          <button
            onClick={() => setDocuments([...documents, { title: '', content: '', category: 'general', tags: [], source: '' }])}
            className="px-4 py-2 border border-[color:var(--border)] text-[color:var(--foreground)] rounded-lg hover:bg-[color:var(--muted)]"
          >
            {translations.addDocument}
          </button>
          <button
            onClick={handleUploadDocuments}
            disabled={loading}
            className="px-6 py-2 bg-[color:var(--primary)] text-[color:var(--primary-foreground)] rounded-lg hover:opacity-90 disabled:opacity-50"
          >
            {loading ? translations.loading : translations.uploadBtn}
          </button>
        </div>
      </div>

      {/* Search Section */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6">
        <h2 className="text-xl font-semibold text-[color:var(--foreground)] mb-4">
          {translations.searchTitle}
        </h2>
        <div className="flex gap-4 mb-6">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-3 py-2 border border-[color:var(--border)] rounded-lg bg-[color:var(--background)] text-[color:var(--foreground)]"
            placeholder="Nhập câu hỏi để test Global KB..."
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-2 bg-[color:var(--primary)] text-[color:var(--primary-foreground)] rounded-lg hover:opacity-90 disabled:opacity-50"
          >
            {loading ? translations.loading : translations.searchBtn}
          </button>
        </div>
        {/* Search Results */}
        {searchResults.length > 0 && (
          <div>
            <h3 className="font-medium text-[color:var(--foreground)] mb-4">
              {translations.results}
            </h3>
            <div className="space-y-4">
              {searchResults.map((result, idx) => (
                <div key={idx} className="border border-[color:var(--border)] rounded-lg p-4">
                  <div className="font-semibold mb-2">{result.content}</div>
                  <div className="text-sm text-[color:var(--muted-foreground)]">
                    {translations.score}: {result.similarity_score?.toFixed(2)} | {translations.source}: <a href={result.source} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">{result.source}</a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AdminKBClient;