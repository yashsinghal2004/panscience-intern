'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getDocuments, deleteDocument } from '@/services/analytics'
import { format } from 'date-fns'

export default function DocumentsPage() {
  const router = useRouter()
  const [documents, setDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<number | null>(null)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const docs = await getDocuments()
      setDocuments(docs)
    } catch (error: any) {
      console.error('Error loading documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (docId: number) => {
    if (!confirm('Are you sure you want to delete this document?')) {
      return
    }

    try {
      setDeleting(docId)
      await deleteDocument(docId)
      await loadDocuments()
    } catch (error: any) {
      alert('Failed to delete document: ' + error.message)
    } finally {
      setDeleting(null)
    }
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading documents...</div>
      </div>
    )
  }

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1>Document Management</h1>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button onClick={() => router.push('/dashboard')} style={{ padding: '0.5rem 1rem' }}>
            📊 Dashboard
          </button>
          <button onClick={() => router.push('/')} style={{ padding: '0.5rem 1rem' }}>
            Back to Q&A
          </button>
        </div>
      </div>

      <div className="card">
        <h2>Uploaded Documents ({documents.length})</h2>
        
        {documents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
            No documents uploaded yet. Upload documents from the main page.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e0e0e0' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Filename</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Type</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Size</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Pages</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Chunks</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Vectors</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Queries</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Upload Date</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} style={{ borderBottom: '1px solid #e0e0e0' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 500 }}>{doc.filename}</td>
                    <td style={{ padding: '0.75rem' }}>{doc.file_type.toUpperCase()}</td>
                    <td style={{ padding: '0.75rem' }}>{doc.file_size_mb} MB</td>
                    <td style={{ padding: '0.75rem' }}>{doc.pages || '-'}</td>
                    <td style={{ padding: '0.75rem' }}>{doc.chunks_count}</td>
                    <td style={{ padding: '0.75rem' }}>{doc.vectors_count}</td>
                    <td style={{ padding: '0.75rem' }}>{doc.query_count}</td>
                    <td style={{ padding: '0.75rem', fontSize: '0.9rem' }}>
                      {format(new Date(doc.upload_date), 'MMM d, yyyy HH:mm')}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        disabled={deleting === doc.id}
                        style={{
                          padding: '0.4rem 0.8rem',
                          fontSize: '0.85rem',
                          background: '#fee',
                          color: '#c33',
                          border: '1px solid #c33',
                          borderRadius: '6px',
                          cursor: deleting === doc.id ? 'not-allowed' : 'pointer'
                        }}
                      >
                        {deleting === doc.id ? 'Deleting...' : 'Delete'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}









