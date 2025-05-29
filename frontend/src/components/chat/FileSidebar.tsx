'use client'

import { useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faFile, faTrash, faDownload, faFolder, faPlus } from '@fortawesome/free-solid-svg-icons'

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  uploadDate: Date
}

interface FileSidebarProps {
  uploadedFiles: UploadedFile[]
  onDeleteFile: (id: string) => void
  onUploadFiles?: (files: File[]) => void
  translations: {
    uploadedFiles: string
    noFilesUploaded: string
    uploadFilesDescription: string
    download: string
    delete: string
    uploadFiles?: string
  }
}

export function FileSidebar({ uploadedFiles, onDeleteFile, onUploadFiles, translations }: FileSidebarProps) {
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

  return (
    <div className="h-full flex flex-col bg-[color:var(--card)]/50 backdrop-blur-sm border-l border-[color:var(--border)]">
      {/* Header */}
      <div className="p-4 border-b border-[color:var(--border)]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-r from-[color:var(--gradient-text-from)] to-[color:var(--gradient-text-to)] rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faFolder} className="text-white text-sm" />
            </div>
            <h2 className="text-lg font-semibold text-[color:var(--foreground)]">{translations.uploadedFiles}</h2>
          </div>
          
          {/* Upload Button */}
          <Button
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            className="bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] hover:shadow-[var(--button-hover-shadow)] transition-all duration-200"
          >
            <FontAwesomeIcon icon={faPlus} className="mr-2" />
            Upload
          </Button>
        </div>
        
        <p className="text-sm text-[color:var(--muted-foreground)]">
          {uploadedFiles.length} {uploadedFiles.length === 1 ? 'file' : 'files'}
        </p>

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
        {uploadedFiles.length === 0 ? (
          <div className="text-center text-[color:var(--muted-foreground)] mt-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-[color:var(--muted)] rounded-full flex items-center justify-center">
              <FontAwesomeIcon icon={faFile} className="text-2xl" />
            </div>
            <p>{translations.noFilesUploaded}</p>
            <p className="text-sm">{translations.uploadFilesDescription}</p>
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
                    title={translations.download}
                  >
                    <FontAwesomeIcon icon={faDownload} className="text-xs text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)]" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onDeleteFile(file.id)}
                    className="h-6 w-6 p-0 hover:bg-[color:var(--destructive)]/10"
                    title={translations.delete}
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
