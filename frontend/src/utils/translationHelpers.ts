// Shared utilities có thể dùng cả client và server

// Dictionary type definitions
export type Dictionary = Record<string, unknown>

// Helper function để lấy nested value
export function getNestedValue(obj: Dictionary, path: string): string {
  const result = path.split('.').reduce((current: Dictionary | unknown, key: string): unknown => {
    if (current && typeof current === 'object' && current !== null) {
      return (current as Record<string, unknown>)[key]
    }
    return undefined
  }, obj)
  
  return typeof result === 'string' ? result : path
} 