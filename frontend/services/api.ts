import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const BASE_URL = `${API_URL}/api/v1`

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface QueryRequest {
  query: string
  top_k?: number
  threshold?: number
}

export interface QueryResponse {
  answer: string
  sources: Array<{
    chunk: string
    similarity: number
    metadata: Record<string, any>
  }>
  query: string
}

export interface IngestResponse {
  message: string
  chunks_added: number
  total_chunks: number
}

export async function queryDocuments(
  query: string,
  topK?: number,
  threshold?: number
): Promise<QueryResponse> {
  try {
    const response = await api.post<QueryResponse>('/query', {
      query,
      top_k: topK,
      threshold,
    })
    return response.data
  } catch (error: any) {
    throw new Error(
      error.response?.data?.detail || error.message || 'Failed to query documents'
    )
  }
}

export async function uploadDocument(file: File): Promise<IngestResponse> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post<IngestResponse>(
      '/ingest/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  } catch (error: any) {
    throw new Error(
      error.response?.data?.detail || error.message || 'Failed to upload file'
    )
  }
}

export async function ingestText(text: string): Promise<IngestResponse> {
  try {
    const response = await api.post<IngestResponse>('/ingest', {
      text,
    })
    return response.data
  } catch (error: any) {
    throw new Error(
      error.response?.data?.detail || error.message || 'Failed to ingest text'
    )
  }
}

export async function getHealth(): Promise<any> {
  try {
    const response = await api.get('/health')
    return response.data
  } catch (error: any) {
    throw new Error(
      error.response?.data?.detail || error.message || 'Health check failed'
    )
  }
}











