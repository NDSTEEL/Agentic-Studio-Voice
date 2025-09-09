import React from 'react'
import Layout from '../../components/Layout'

export default function Tenants() {
  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">Tenant Management</h1>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-gray-900">Tenants</h2>
            <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
              Add New Tenant
            </button>
          </div>
          
          <div className="space-y-4">
            <p className="text-gray-500">No tenants found. Create your first tenant to get started.</p>
          </div>
        </div>
      </div>
    </Layout>
  )
}