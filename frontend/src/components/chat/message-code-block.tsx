'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCopy, faCheck, faDownload, faCode, faEye } from '@fortawesome/free-solid-svg-icons';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useTranslation } from '@/contexts/TranslationContext';
import DOMPurify from 'dompurify';

interface MessageCodeBlockProps {
  code: string;
  language: string;
  inline?: boolean;
  children?: React.ReactNode;
  variant?: 'header' | 'floating' | 'inline';
}

export function MessageCodeBlock({
  code,
  language,
  inline = false,
  children,
  variant = 'header'
}: MessageCodeBlockProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const [showRendered, setShowRendered] = useState(false);

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

  const renderHtmlContent = () => {
    if (!isHtmlCode) return null;
    
    try {
      // Sanitize the HTML to prevent XSS attacks
      const sanitizedHtml = DOMPurify.sanitize(code, {
        ADD_TAGS: ['style'],
        ADD_ATTR: ['style', 'class', 'id']
      });
      
      return (
        <div className="p-4 bg-white border-t border-[color:var(--border)]">
          <div 
            className="rendered-html-content"
            dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
            style={{
              // Reset some styles to ensure proper rendering
              fontSize: '14px',
              lineHeight: '1.5',
              color: '#000'
            }}
          />
        </div>
      );
    } catch (error) {
      console.error('Error rendering HTML:', error);
      return (
        <div className="p-4 bg-red-50 border-t border-[color:var(--border)] text-red-600">
          {t('chat.htmlRenderError') || 'Error rendering HTML content'}
        </div>
      );
    }
  };

  if (inline) {
    return (
      <code 
        className="bg-[color:var(--muted)] !background-transparent text-[color:var(--foreground)] px-1.5 py-0.5 rounded text-sm font-mono border border-[color:var(--border)]/50 shadow-sm" 
      >
        {children}
      </code>
    );
  }

  if (variant === 'header') {
    return (
      <div className="contain-inline-size rounded-md border-[0.5px] border-[color:var(--border)] relative bg-[color:var(--card)] my-4 w-full max-w-full overflow-hidden">
        {/* Header with language and actions */}
        <div className="flex items-center text-[color:var(--muted-foreground)] px-4 py-2 text-xs font-sans justify-between h-9 bg-[color:var(--card)] dark:bg-[color:var(--muted)] select-none rounded-t-[5px] border-b border-[color:var(--border)]">
          <span className="font-medium">{language}</span>
          <div className="flex items-center gap-1">
            {isHtmlCode && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowRendered(!showRendered)}
                className="flex gap-1 items-center select-none px-3 py-1 h-auto text-xs hover:bg-[color:var(--accent)] transition-colors"
              >
                <FontAwesomeIcon 
                  icon={showRendered ? faCode : faEye} 
                  className="w-3 h-3" 
                />
                {showRendered ? (t('chat.showCode') || 'Code') : (t('chat.preview') || 'Preview')}
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
              {t('common.download') || 'Download'}
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
              {copied ? (t('chat.copied') || 'Copied!') : (t('chat.copy') || 'Copy')}
            </Button>
          </div>
        </div>
        
        {/* Code content with syntax highlighting or rendered HTML */}
        {showRendered && isHtmlCode ? (
          renderHtmlContent()
        ) : (
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
        )}
      </div>
    );
  }

  if (variant === 'floating') {
    return (
      <div className="contain-inline-size rounded-md border border-[color:var(--border)] relative bg-[color:var(--muted)] my-4 w-full max-w-full overflow-hidden group">
        <div className="relative">
          {showRendered && isHtmlCode ? (
            <div className="p-4 bg-white">
              <div 
                className="rendered-html-content"
                dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(code) }}
              />
            </div>
          ) : (
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
          )}
          
          {/* Floating action buttons */}
          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-1">
            {isHtmlCode && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowRendered(!showRendered)}
                className="text-xs bg-[color:var(--background)]/90 backdrop-blur-sm border border-[color:var(--border)] hover:bg-[color:var(--muted)] px-2 py-1 h-auto"
              >
                <FontAwesomeIcon 
                  icon={showRendered ? faCode : faEye} 
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
              {copied ? (t('chat.copied') || 'Copied!') : (t('chat.copy') || 'Copy')}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Default inline variant
  return (
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
  );
}
