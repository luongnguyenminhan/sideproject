'use client'

import { useState, useEffect } from 'react'

export function useLoading(initialDelay: number = 1500) {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, initialDelay)

    return () => clearTimeout(timer)
  }, [initialDelay])

  return isLoading
}
