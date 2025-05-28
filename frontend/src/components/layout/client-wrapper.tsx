'use client'

import { useLoading } from '@/hooks/useLoading'
import LoadingScreen from '../ui/loading-screen'

interface ClientWrapperProps {
  children: React.ReactNode
  loadingDelay?: number
}

export default function ClientWrapper({ children, loadingDelay = 1500 }: ClientWrapperProps) {
  const isLoading = useLoading(loadingDelay)

  if (isLoading) {
    return <LoadingScreen />
  }

  return <>{children}</>
}
