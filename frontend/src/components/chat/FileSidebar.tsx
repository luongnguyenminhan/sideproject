'use client'

import { useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faFile, faTrash, faDownload, faPlus, faChevronRight } from '@fortawesome/free-solid-svg-icons'
import { useTranslation } from '@/contexts/TranslationContext'

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  uploadDate: Date
}

interface FileSidebarProps {
  uploadedFiles: UploadedFile[]
  isLoading?: boolean
  conversationId?: string | null
  onDeleteFile: (id: string) => void
  onUploadFiles?: (files: File[]) => void
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

export function FileSidebar({ 
  uploadedFiles, 
  isLoading = false,
  conversationId,
  onDeleteFile, 
  onUploadFiles,
  isCollapsed = false,
  onToggleCollapse
}: FileSidebarProps) {
  const { t } = useTranslation()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return '🖼️'
    if (type.startsWith('video/')) return '🎥'
    if (type.startsWith('audio/')) return '🎵'
    if (type.includes('pdf')) return '📄'
    if (type.includes('document') || type.includes('word')) return '📝'
    if (type.includes('spreadsheet') || type.includes('excel')) return '📊'
    return '📎'
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0 && onUploadFiles) {
      onUploadFiles(files)
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // No expand button here; handled in chat-interface.tsx

  return (
    <div className="h-full flex flex-col bg-[color:var(--card)]/50 backdrop-blur-sm relative">
      {/* Header */}
      <div className="p-4 border-b border-[color:var(--border)]">
        <div className="flex items-center justify-between mb-4">
          {/* Upload Button */}
          <Button
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            className="bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] hover:shadow-[var(--button-hover-shadow)] transition-all duration-200 flex-1 mr-2"
          >
            <FontAwesomeIcon icon={faPlus} className="mr-2 text-white" />
            <span className="text-white">{t('common.upload')}</span>
          </Button>

          {/* Collapse button */}
          {!isCollapsed && (
            <Button
              onClick={onToggleCollapse}
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0 hover:bg-[color:var(--accent)] transition-all duration-200"
              title={t('chat.tooltips.collapseSidebar') || 'Collapse sidebar'}
            >
              <FontAwesomeIcon icon={faChevronRight} className="text-sm text-[color:var(--muted-foreground)]" />
            </Button>
          )}
        </div>
        
        {conversationId && (
          <div className="flex items-center gap-2">
            {conversationId && (
              <span className="text-xs text-[color:var(--muted-foreground)] bg-[color:var(--muted)] px-2 py-1 rounded">
                {t('chat.thisConversation')}
              </span>
            )}
            {isLoading && (
              <span className="text-xs text-[color:var(--muted-foreground)]">
                {t('common.loading')}
              </span>
            )}
          </div>
        )}
        
        {/* Hidden File Input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          multiple
          className="hidden"
        />
      </div>

      {/* Files List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-[color:var(--muted)] rounded animate-pulse"></div>
            ))}
          </div>
        ) : uploadedFiles.length === 0 ? (
          <div className="text-center text-[color:var(--muted-foreground)] mt-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-[color:var(--muted)] rounded-full flex items-center justify-center">
              <FontAwesomeIcon icon={faFile} className="text-2xl" />
            </div>
            <p>{t('chat.noFilesUploaded')}</p>
            <p className="text-sm">{t('chat.uploadFilesDescription')}</p>
            {conversationId && (
              <p className="text-xs mt-2 text-[color:var(--muted-foreground)]">
                {t('chat.filesAssociated')}
              </p>
            )}
          </div>
        ) : (
          uploadedFiles.map((file) => (
            <Card key={file.id} className="p-3 hover:shadow-md transition-all duration-200 bg-[color:var(--card)] border-[color:var(--border)] backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <div className="text-2xl">{getFileIcon(file.type)}</div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-sm text-[color:var(--foreground)] truncate" title={file.name}>
                    {file.name}
                  </h3>
                  <p className="text-xs text-[color:var(--muted-foreground)]">
                    {formatFileSize(file.size)}
                  </p>
                  <p className="text-xs text-[color:var(--muted-foreground)]">
                    {file.uploadDate.toLocaleDateString()}
                  </p>
                </div>
                <div className="flex flex-col gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 w-6 p-0 hover:bg-[color:var(--accent)]"
                    title={t('common.download')}
                    onClick={() => {
                      // Download logic will be implemented
                      console.log('Download file:', file.id)
                    }}
                  >
                    <FontAwesomeIcon icon={faDownload} className="text-xs text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)]" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onDeleteFile(file.id)}
                    className="h-6 w-6 p-0 hover:bg-[color:var(--destructive)]/10"
                    title={t('common.delete')}
                  >
                    <FontAwesomeIcon icon={faTrash} className="text-xs text-[color:var(--destructive)]" />
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
