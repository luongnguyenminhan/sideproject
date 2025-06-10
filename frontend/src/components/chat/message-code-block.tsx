'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCopy, faCheck, faDownload, faEye, faTimes } from '@fortawesome/free-solid-svg-icons';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useTranslation } from '@/contexts/TranslationContext';
import DOMPurify from 'dompurify';
import { Modal } from 'antd';

interface MessageCodeBlockProps {
  code: string;
  language: string;
  variant?: 'header' | 'floating' | 'inline';
}

export function MessageCodeBlock({
  code,
  language,
  variant = 'header'
}: MessageCodeBlockProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);

  // Check if the language is HTML or HTML-related
  const isHtmlCode = ['html', 'htm', 'xhtml', 'xml'].includes(language.toLowerCase());

  // Map common language names to file extensions
  const getFileExtension = (lang: string): string => {
    const extensionMap: Record<string, string> = {
      javascript: 'js',
      typescript: 'ts',
      python: 'py',
      java: 'java',
      cpp: 'cpp',
      'c++': 'cpp',
      c: 'c',
      csharp: 'cs',
      'c#': 'cs',
      php: 'php',
      ruby: 'rb',
      go: 'go',
      rust: 'rs',
      swift: 'swift',
      kotlin: 'kt',
      scala: 'scala',
      html: 'html',
      css: 'css',
      scss: 'scss',
      sass: 'sass',
      less: 'less',
      json: 'json',
      xml: 'xml',
      yaml: 'yml',
      yml: 'yml',
      markdown: 'md',
      sql: 'sql',
      bash: 'sh',
      shell: 'sh',
      powershell: 'ps1',
      dockerfile: 'dockerfile',
      tsx: 'tsx',
      jsx: 'jsx'
    };
    return extensionMap[lang.toLowerCase()] || 'txt';
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code block:', err);
    }
  };

  const handleDownload = () => {
    try {
      const extension = getFileExtension(language);
      const fileName = `code.${extension}`;
      const blob = new Blob([code], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download code:', err);
    }
  };

  // Function to render HTML content for the modal
  const renderModalHtmlContent = () => {
    if (!isHtmlCode) return null;
    
    try {
      // For complete HTML documents (with DOCTYPE, html, head, body), use iframe
      const isCompleteHtmlDoc = code.trim().toLowerCase().includes('<!doctype') || 
                                code.trim().toLowerCase().includes('<html');
      
      if (isCompleteHtmlDoc) {
        // Inject styles to hide scrollbars completely in iframe content
        const scrollbarStyles = `
          <style>
            /* Hide scrollbar for webkit browsers */
            ::-webkit-scrollbar {
              width: 0px;
              height: 0px;
              background: transparent;
            }
            
            ::-webkit-scrollbar-track {
              background: transparent;
            }
            
            ::-webkit-scrollbar-thumb {
              background: transparent;
            }
            
            ::-webkit-scrollbar-corner {
              background: transparent;
            }
            
            /* Hide scrollbar for Firefox */
            * {
              scrollbar-width: none;
              -ms-overflow-style: none;
            }
            
            /* Hide scrollbar for IE and Edge */
            body {
              -ms-overflow-style: none;
              overflow: -moz-scrollbars-none;
            }
            
            /* Ensure content is still scrollable but scrollbar is hidden */
            html, body {
              overflow: auto;
            }
          </style>
        `;
        
        // Inject scrollbar styles into the HTML content
        let enhancedCode = code;
        if (code.toLowerCase().includes('<head>')) {
          enhancedCode = code.replace(/<\/head>/i, `${scrollbarStyles}</head>`);
        } else if (code.toLowerCase().includes('<html>')) {
          enhancedCode = code.replace(/<html[^>]*>/i, match => `${match}${scrollbarStyles}`);
        } else {
          enhancedCode = `${scrollbarStyles}${code}`;
        }
        
        const blob = new Blob([enhancedCode], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        
        return (
          <iframe
            src={url}
            className="w-full border-0 rounded"
            style={{
              height: '70vh',
              minHeight: '500px',
              overflow: 'hidden'
            }}
            sandbox="allow-same-origin"
            title="HTML Preview"
          />
        );
      } else {
        // For HTML fragments, use sanitized innerHTML
        const sanitizedHtml = DOMPurify.sanitize(code, {
          ADD_TAGS: ['style', 'link'],
          ADD_ATTR: ['style', 'class', 'id', 'href', 'rel', 'type'],
          ALLOW_DATA_ATTR: true,
          FORBID_TAGS: ['script'],
          FORBID_ATTR: ['onload', 'onerror', 'onclick']
        });
        
        return (
          <div 
            className="rendered-html-content h-full overflow-auto"
            dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
            style={{
              isolation: 'isolate',
              all: 'initial',
              fontFamily: 'inherit',
              fontSize: '14px',
              lineHeight: '1.5',
              color: '#000',
              minHeight: '500px',
              padding: '16px'
            }}
          />
        );
      }
    } catch (error) {
      console.error('Error rendering HTML:', error);
      return (
        <div className="p-4 bg-red-50 text-red-600 text-center">
          {t('chat.htmlRenderError')}
        </div>
      );
    }
  };

  // This component now only handles block code, inline code is handled in chat-message.tsx
  // Remove inline handling since it's now processed upstream

  if (variant === 'header') {
    return (
      <>
        <div className="contain-inline-size rounded-md border-[0.5px] border-[color:var(--border)] relative bg-[color:var(--card)] my-4 w-full max-w-full overflow-hidden">
          {/* Header with language and actions */}
          <div className="flex items-center text-[color:var(--muted-foreground)] px-4 py-2 text-xs font-sans justify-between h-9 bg-[color:var(--card)] dark:bg-[color:var(--muted)] select-none rounded-t-[5px] border-b border-[color:var(--border)]">
            <span className="font-medium">{language}</span>
            <div className="flex items-center gap-1">
              {isHtmlCode && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsPreviewModalOpen(true)}
                  className="flex gap-1 items-center select-none px-3 py-1 h-auto text-xs hover:bg-[color:var(--accent)] transition-colors"
                >
                  <FontAwesomeIcon 
                    icon={faEye} 
                    className="w-3 h-3" 
                  />
                  {t('chat.preview')}
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDownload}
                className="flex gap-1 items-center select-none px-3 py-1 h-auto text-xs hover:bg-[color:var(--accent)] transition-colors"
              >
                <FontAwesomeIcon 
                  icon={faDownload} 
                  className="w-3 h-3" 
                />
                {t('common.download')}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopy}
                className="flex gap-1 items-center select-none px-3 py-1 h-auto text-xs hover:bg-[color:var(--accent)] transition-colors"
              >
                <FontAwesomeIcon 
                  icon={copied ? faCheck : faCopy} 
                  className="w-3 h-3" 
                />
                {copied ? (t('chat.copied')) : (t('chat.copy'))}
              </Button>
            </div>
          </div>
          
          {/* Code content with syntax highlighting */}
          <div className="overflow-y-auto" dir="ltr">
            <SyntaxHighlighter
              language={language}
              style={oneDark}
              customStyle={{
                margin: 0,
                padding: '1rem',
                background: 'rgba(0, 0, 0, 0.05)',
                fontSize: '14px',
                lineHeight: '1.5',
                backgroundColor: 'rgba(0, 0, 0, 0.05)'
              }}
              showLineNumbers={true}
              wrapLines={true}
              codeTagProps={{
                style: {
                  background: 'transparent',
                  backgroundColor: 'transparent'
                }
              }}
            >
              {code}
            </SyntaxHighlighter>
          </div>
        </div>

        {/* HTML Preview Modal */}
        {isHtmlCode && (
          <Modal
            open={isPreviewModalOpen}
            onCancel={() => setIsPreviewModalOpen(false)}
            footer={null}
            centered
            width="90vw"
            style={{ maxWidth: '1200px' }}
            closeIcon={
              <FontAwesomeIcon 
                icon={faTimes} 
                className="text-gray-500 hover:text-gray-700 text-lg" 
              />
            }
            styles={{
              content: {
                borderRadius: '20px',
                padding: '50px',
                background: 'var(--auth-card-bg)',
                border: '1px solid var(--auth-card-border)',
                maxHeight: '90vh'
              },
              mask: {
                backdropFilter: 'blur(8px)',
                backgroundColor: 'rgba(0, 0, 0, 0.5)'
              }
            }}
          >
            <div className="h-full">
              {renderModalHtmlContent()}
            </div>
          </Modal>
        )}
      </>
    );
  }

  if (variant === 'floating') {
    return (
      <div className="contain-inline-size rounded-md border border-[color:var(--border)] relative bg-[color:var(--muted)] my-4 w-full max-w-full overflow-hidden group">
        <div className="relative">
          <SyntaxHighlighter
            language={language}
            style={oneDark}
            customStyle={{
              margin: 0,
              padding: '1rem',
              background: 'transparent',
              fontSize: '14px',
              lineHeight: '1.5'
            }}
            showLineNumbers={false}
            wrapLines={true}
            codeTagProps={{
              style: {
                background: 'transparent',
                backgroundColor: 'transparent'
              }
            }}
          >
            {code}
          </SyntaxHighlighter>
          
          {/* Floating action buttons */}
          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-1">
            {isHtmlCode && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsPreviewModalOpen(true)}
                className="text-xs bg-[color:var(--background)]/90 backdrop-blur-sm border border-[color:var(--border)] hover:bg-[color:var(--muted)] px-2 py-1 h-auto"
              >
                <FontAwesomeIcon 
                  icon={faEye} 
                  className="w-3 h-3"
                />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDownload}
              className="text-xs bg-[color:var(--background)]/90 backdrop-blur-sm border border-[color:var(--border)] hover:bg-[color:var(--muted)] px-2 py-1 h-auto"
            >
              <FontAwesomeIcon 
                icon={faDownload} 
                className="w-3 h-3"
              />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="text-xs bg-[color:var(--background)]/90 backdrop-blur-sm border border-[color:var(--border)] hover:bg-[color:var(--muted)] px-2 py-1 h-auto"
            >
              <FontAwesomeIcon 
                icon={copied ? faCheck : faCopy} 
                className="w-3 h-3 mr-1"
              />
              {copied ? (t('chat.copied')) : (t('chat.copy'))}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Default inline variant
  return (
    <>
      <div className="contain-inline-size rounded border border-[color:var(--border)] bg-[color:var(--muted)] my-2 relative overflow-hidden group">
        <SyntaxHighlighter
          language={language}
          style={oneDark}
          customStyle={{
            margin: 0,
            padding: '0.75rem',
            background: 'transparent',
            fontSize: '13px',
            lineHeight: '1.4'
          }}
          showLineNumbers={false}
          wrapLines={true}
          codeTagProps={{
                style: {
                  background: 'transparent',
                  backgroundColor: 'transparent'
                }
              }}
        >
          {code}
        </SyntaxHighlighter>
        
        {/* Action buttons for inline variant */}
        <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDownload}
            className="text-xs px-2 py-1 h-auto bg-[color:var(--background)]/80 hover:bg-[color:var(--background)]"
          >
            <FontAwesomeIcon 
              icon={faDownload} 
              className="w-3 h-3"
            />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="text-xs px-2 py-1 h-auto bg-[color:var(--background)]/80 hover:bg-[color:var(--background)]"
          >
            <FontAwesomeIcon 
              icon={copied ? faCheck : faCopy} 
              className="w-3 h-3"
            />
          </Button>
        </div>
      </div>

      {/* HTML Preview Modal */}
      {isHtmlCode && (
        <Modal
          open={isPreviewModalOpen}
          onCancel={() => setIsPreviewModalOpen(false)}
          footer={null}
          centered
          width="90vw"
          style={{ maxWidth: '1200px' }}
          closeIcon={
            <FontAwesomeIcon 
              icon={faTimes} 
              className="text-gray-500 hover:text-gray-700 text-lg" 
            />
          }
          styles={{
            content: {
              borderRadius: '20px',
              padding: '50px',
              background: 'var(--auth-card-bg)',
              border: '1px solid var(--auth-card-border)',
              maxHeight: '90vh'
            },
            mask: {
              backdropFilter: 'blur(8px)',
              backgroundColor: 'rgba(0, 0, 0, 0.5)'
            }
          }}
        >
          <div className="h-full">
            {renderModalHtmlContent()}
          </div>
        </Modal>
      )}
    </>
  );
}
