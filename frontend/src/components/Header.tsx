import React from 'react'
import Link from 'next/link'

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <Link href="/" className="text-xl font-bold text-gray-900">
          Voice Agent Platform
        </Link>
        <nav className="flex items-center space-x-4">
          <Link 
            href="/dashboard" 
            className="text-gray-600 hover:text-gray-900"
          >
            Dashboard
          </Link>
          <Link 
            href="/tenants" 
            className="text-gray-600 hover:text-gray-900"
          >
            Tenants
          </Link>
          <Link 
            href="/settings" 
            className="text-gray-600 hover:text-gray-900"
          >
            Settings
          </Link>
        </nav>
      </div>
    </header>
  )
}