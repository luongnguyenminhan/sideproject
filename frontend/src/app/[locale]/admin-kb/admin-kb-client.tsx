/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';
import { useState, useCallback, useEffect } from 'react';
import { globalKBAPI } from '@/apis/global-kb-api';
import type {
  AdminDocumentData,
  GlobalKBResponse,
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
  const [searchResults, setSearchResults] = useState<GlobalKBResponse[]>([]);
  const [stats, setStats] = useState<GlobalKBStats | null>(null);
  const [, setSelectedFile] = useState<File | null>(null);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
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

  // Fetch all documents
  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await globalKBAPI.list();
      if (response.error_code === 0) {
        setDocuments(response.data || []);
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
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
          id: uploaded.id,
          title: uploaded.title,
          file_name: uploaded.file_name,
          file_type: uploaded.file_type,
          category: uploaded.category,
          source: uploaded.source,
          indexed: uploaded.indexed,
          index_status: uploaded.index_status,
          create_date: uploaded.create_date,
          update_date: uploaded.update_date,
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
        setSearchResults(response.data || []);
        showMessage('success', `Tìm thấy ${response.data?.length || 0} kết quả`);
      } else {
        showMessage('error', response.message);
      }
    } catch (error: any) {
      showMessage('error', error.message || translations.error);
    } finally {
      setLoading(false);
    }
  };

  // Remove document (local only)
  const removeDocument = (index: number) => {
    setDocuments(documents.filter((_, i) => i !== index));
  };

  // Update document (local only)
  const updateDocument = (index: number, field: keyof AdminDocumentData, value: any) => {
    const updatedDocs = [...documents];
    (updatedDocs[index] as any)[field] = value;
    setDocuments(updatedDocs);
  };

  useEffect(() => {
    fetchStats();
    fetchDocuments();
  }, []);

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
        </div>
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-[color:var(--muted)] rounded-lg">
              <p className="text-sm text-[color:var(--muted-foreground)]">Total Documents</p>
              <p className="font-semibold text-[color:var(--foreground)]">{stats.total_documents}</p>
            </div>
            <div className="p-4 bg-[color:var(--muted)] rounded-lg">
              <p className="text-sm text-[color:var(--muted-foreground)]">Indexed Documents</p>
              <p className="font-semibold text-[color:var(--foreground)]">{stats.indexed_documents || 0}</p>
            </div>
            <div className="p-4 bg-[color:var(--muted)] rounded-lg">
              <p className="text-sm text-[color:var(--muted-foreground)]">Pending Documents</p>
              <p className="font-semibold text-[color:var(--foreground)]">{stats.pending_documents || 0}</p>
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
                  value={doc.file_name}
                  onChange={(e) => updateDocument(index, 'file_name', e.target.value)}
                  className="w-full px-3 py-2 border border-[color:var(--border)] rounded-lg bg-[color:var(--background)] text-[color:var(--foreground)]"
                  placeholder="File name"
                />
              </div>
              <div className="mb-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-[color:var(--muted-foreground)]">Index Status:</label>
                  <span className={`ml-2 px-2 py-1 rounded text-xs ${
                    doc.index_status === 'success' ? 'bg-green-100 text-green-800' :
                    doc.index_status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {doc.index_status || 'pending'}
                  </span>
                </div>
                <div>
                  <label className="text-sm text-[color:var(--muted-foreground)]">File Type:</label>
                  <span className="ml-2 text-sm">{doc.file_type || 'Unknown'}</span>
                </div>
              </div>
              <div className="mb-2">
                {doc.source && (
                  <a href={doc.source} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                    {translations.source}
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="flex gap-4 mt-6">
          <button
            onClick={() => setDocuments([...documents, { 
              title: '', 
              file_name: '', 
              file_type: '', 
              category: 'general', 
              source: '',
              indexed: false,
              index_status: 'pending'
            }])}
            className="px-4 py-2 border border-[color:var(--border)] text-[color:var(--foreground)] rounded-lg hover:bg-[color:var(--muted)]"
          >
            {translations.addDocument}
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
                  <div className="font-semibold mb-2">{result.title}</div>
                  <div className="text-sm mb-2">
                    <span className="font-medium">File:</span> {result.file_name}
                    {result.file_type && <span className="ml-2 text-[color:var(--muted-foreground)]">({result.file_type})</span>}
                  </div>
                  <div className="text-sm mb-2">
                    <span className="font-medium">Category:</span> {result.category}
                    <span className={`ml-4 px-2 py-1 rounded text-xs ${
                      result.index_status === 'success' ? 'bg-green-100 text-green-800' :
                      result.index_status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {result.index_status}
                    </span>
                  </div>
                  <div className="text-sm text-[color:var(--muted-foreground)]">
                    {translations.source}: {result.source && (
                      <a href={result.source} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                        View File
                      </a>
                    )}
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