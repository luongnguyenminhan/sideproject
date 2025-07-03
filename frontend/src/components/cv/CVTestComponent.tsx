'use client';

import React, { useState, useCallback } from 'react';
import { useTranslation } from '@/contexts/TranslationContext';
import { cvApi, CVRegenResponse } from '@/apis/cvApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const CVTestComponent: React.FC = () => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<CVRegenResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [templateType, setTemplateType] = useState('modern');
  const [colorTheme, setColorTheme] = useState('blue');
  const [customPrompt, setCustomPrompt] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
        setError(null);
      }
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
        setError(null);
      }
    }
  };

  const validateFile = (file: File): boolean => {
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type)) {
      setError('Chỉ hỗ trợ file PDF, DOCX, TXT');
      return false;
    }

    if (file.size > maxSize) {
      setError('File không được vượt quá 10MB');
      return false;
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!file) {
      setError('Vui lòng chọn file CV');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await cvApi.regenFromFile(
        file,
        templateType,
        colorTheme,
        customPrompt || undefined
      );

      if (response.error_code === 0 && response.data) {
        setResult(response.data);
      } else {
        setError(response.message || 'Có lỗi xảy ra khi tạo CV');
      }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      setError(err.message || 'Có lỗi xảy ra khi tạo CV');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (result?.pdf_download_url) {
      const link = document.createElement('a');
      link.href = result.pdf_download_url;
      link.download = `cv_generated_${Date.now()}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <Card className="bg-[color:var(--background)] rounded-3xl shadow-2xl border border-[color:var(--border)] p-8">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-[color:var(--foreground)] mb-4">
                🚀 CV Generator Test
              </h1>
              <p className="text-[color:var(--muted-foreground)] text-lg">
                Upload CV của bạn và nhận lại PDF được tạo bởi AI
              </p>
            </div>

            {/* File Upload Area */}
            <div className="mb-8">
              <div
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                  dragActive
                    ? 'border-[color:var(--primary)] bg-[color:var(--primary)]/5'
                    : 'border-[color:var(--border)] hover:border-[color:var(--primary)]/50'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <div className="space-y-4">
                  <div className="text-6xl">📄</div>
                  <div>
                    <p className="text-lg font-medium text-[color:var(--foreground)] mb-2">
                      Kéo thả file CV hoặc nhấn để chọn
                    </p>
                    <p className="text-sm text-[color:var(--muted-foreground)] mb-4">
                      Hỗ trợ PDF, DOCX, TXT (tối đa 10MB)
                    </p>
                    <input
                      type="file"
                      id="file-upload"
                      className="hidden"
                      accept=".pdf,.docx,.txt"
                      onChange={handleFileChange}
                    />
                    <label htmlFor="file-upload">
                      <Button variant="outline" className="cursor-pointer">
                        Chọn File
                      </Button>
                    </label>
                  </div>
                </div>
              </div>

              {file && (
                <div className="mt-4 p-4 bg-[color:var(--muted)]/20 rounded-lg border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="text-2xl">📎</div>
                      <div>
                        <p className="font-medium text-[color:var(--foreground)]">{file.name}</p>
                        <p className="text-sm text-[color:var(--muted-foreground)]">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setFile(null)}
                      className="text-red-500 hover:text-red-700"
                    >
                      ✕
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {/* Options */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {/* Template Type */}
              <div>
                <label className="block text-sm font-medium text-[color:var(--foreground)] mb-3">
                  Template
                </label>
                <div className="space-y-2">
                  {['modern', 'classic', 'creative'].map((template) => (
                    <label key={template} className="flex items-center space-x-3 cursor-pointer">
                      <input
                        type="radio"
                        name="template"
                        value={template}
                        checked={templateType === template}
                        onChange={(e) => setTemplateType(e.target.value)}
                        className="text-[color:var(--primary)]"
                      />
                      <span className="text-[color:var(--foreground)] capitalize">{template}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Color Theme */}
              <div>
                <label className="block text-sm font-medium text-[color:var(--foreground)] mb-3">
                  Màu sắc
                </label>
                <div className="space-y-2">
                  {['blue', 'green', 'purple', 'red'].map((color) => (
                    <label key={color} className="flex items-center space-x-3 cursor-pointer">
                      <input
                        type="radio"
                        name="color"
                        value={color}
                        checked={colorTheme === color}
                        onChange={(e) => setColorTheme(e.target.value)}
                        className="text-[color:var(--primary)]"
                      />
                      <span className="text-[color:var(--foreground)] capitalize flex items-center space-x-2">
                        <div className={`w-4 h-4 rounded-full bg-${color}-500`}></div>
                        <span>{color}</span>
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Custom Prompt */}
              <div>
                <label className="block text-sm font-medium text-[color:var(--foreground)] mb-3">
                  Prompt tùy chỉnh
                </label>
                <textarea
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="Thêm yêu cầu đặc biệt cho CV..."
                  className="w-full h-20 p-3 border border-[color:var(--border)] rounded-lg bg-[color:var(--background)] text-[color:var(--foreground)] resize-none text-sm"
                />
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <span className="text-red-500">⚠️</span>
                  <span className="text-red-700 font-medium">{error}</span>
                </div>
              </div>
            )}

            {/* Generate Button */}
            <div className="mb-8">
              <Button
                onClick={handleSubmit}
                disabled={!file || isLoading}
                className="w-full py-4 text-lg font-semibold"
                size="lg"
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Đang tạo CV...</span>
                  </div>
                ) : (
                  '🚀 Tạo CV PDF'
                )}
              </Button>
            </div>

            {/* Results */}
            {result && (
              <div className="space-y-6">
                <div className="text-center">
                  <div className="text-6xl mb-4">✅</div>
                  <h2 className="text-2xl font-bold text-[color:var(--foreground)] mb-2">
                    CV đã được tạo thành công!
                  </h2>
                  <p className="text-[color:var(--muted-foreground)]">
                    {result.message}
                  </p>
                </div>

                {/* Download Section */}
                {result.pdf_download_url && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
                    <div className="space-y-4">
                      <div className="text-4xl">📥</div>
                      <div>
                        <h3 className="text-lg font-semibold text-green-800 mb-2">
                          CV PDF sẵn sàng để tải
                        </h3>
                        <div className="space-y-2 text-sm text-green-700">
                          {result.file_size && (
                            <p>Kích thước: {formatFileSize(result.file_size)}</p>
                          )}
                          {result.generation_time && (
                            <p>Thời gian tạo: {result.generation_time.toFixed(2)}s</p>
                          )}
                        </div>
                      </div>
                      <Button onClick={handleDownload} className="bg-green-600 hover:bg-green-700">
                        📥 Tải xuống PDF
                      </Button>
                    </div>
                  </div>
                )}

                {/* CV Analysis */}
                {result.cv_analysis && (
                  <div className="bg-[color:var(--muted)]/20 border border-[color:var(--border)] rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-4">
                      📋 Phân tích CV
                    </h3>
                    <pre className="text-sm text-[color:var(--muted-foreground)] whitespace-pre-wrap overflow-auto max-h-64">
                      {JSON.stringify(result.cv_analysis, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CVTestComponent; 