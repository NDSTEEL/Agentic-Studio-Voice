import React from 'react'

interface LoadingProps {
  size?: 'small' | 'medium' | 'large'
  message?: string
  fullScreen?: boolean
}

export default function Loading({ size = 'medium', message = 'Loading...', fullScreen = false }: LoadingProps) {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12'
  }

  const textSizeClasses = {
    small: 'text-sm',
    medium: 'text-base',
    large: 'text-lg'
  }

  const containerClasses = fullScreen 
    ? 'fixed inset-0 flex items-center justify-center bg-gray-50 bg-opacity-75 z-50'
    : 'flex items-center justify-center p-4'

  return (
    <div className={containerClasses}>
      <div className="flex flex-col items-center space-y-2">
        <div className={`${sizeClasses[size]} border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin`}></div>
        {message && (
          <p className={`${textSizeClasses[size]} text-gray-600 font-medium`}>
            {message}
          </p>
        )}
      </div>
    </div>
  )
}