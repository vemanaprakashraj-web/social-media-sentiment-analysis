/** Typed API client for the SocialScope AI backend. */

import type {
  Analysis,
  CommentsPage,
  DetectResult,
  HistoryItem,
  PlatformInfo,
  PlatformKey,
  ProfileStats,
} from '../types'

const CONFIGURED_BASE = import.meta.env.VITE_API_URL as string | undefined
const BASE = CONFIGURED_BASE || '/api'

/**
 * A single request-target message, so a connection failure tells the user which
 * URL was actually attempted instead of guessing at a port.
 */
function unreachableMessage(): string {
  if (!CONFIGURED_BASE) {
    return (
      'Cannot reach the SocialScope AI API. No API base URL is configured for this ' +
      'deployment — set the VITE_API_URL environment variable (for example ' +
      'https://your-backend.onrender.com/api) and redeploy.'
    )
  }
  return (
    `Cannot reach the SocialScope AI API at ${CONFIGURED_BASE}. The backend may be ` +
    'sleeping, still deploying, or rejecting this origin — check CORS_ORIGINS on the backend.'
  )
}

/** An error carrying the backend's user-safe message. */
export class ApiError extends Error {
  code: string
  status: number
  detail: Record<string, unknown>

  constructor(message: string, code = 'error', status = 0, detail: Record<string, unknown> = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.detail = detail
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    })
  } catch {
    throw new ApiError(unreachableMessage(), 'network_error')
  }

  if (!response.ok) {
    let message = 'The request could not be completed.'
    let code = 'http_error'
    let detail: Record<string, unknown> = {}
    try {
      const body = await response.json()
      if (body?.error) {
        message = body.error.message ?? message
        code = body.error.code ?? code
        detail = body.error.detail ?? {}
      }
    } catch {
      /* non-JSON error body; keep the generic message */
    }
    throw new ApiError(message, code, response.status, detail)
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

const post = <T,>(path: string, body: unknown) =>
  request<T>(path, { method: 'POST', body: JSON.stringify(body) })

/* ------------------------------------------------------------------ system */

export const getHealth = () => request<Record<string, unknown>>('/health')

export const getPlatforms = () =>
  request<{ platforms: PlatformInfo[]; demo_mode_enabled: boolean }>('/platforms')

export const detectPlatform = (url: string) =>
  post<DetectResult>('/detect', { url })

/* ---------------------------------------------------------------- analysis */

export const analyzeUrl = (url: string, userName?: string) =>
  post<Analysis>('/analyze', { url, user_name: userName ?? null })

export const runDemo = (platform: PlatformKey, userName?: string) =>
  post<Analysis>('/demo', { platform, user_name: userName ?? null })

export const getAnalysis = (analysisId: string) =>
  request<Analysis>(`/analysis/${analysisId}`)

export interface CommentQuery {
  search?: string
  sentiment?: string
  date_from?: string
  date_to?: string
  min_likes?: number
  sort?: string
  order?: string
  page?: number
  page_size?: number
}

export const getComments = (analysisId: string, query: CommentQuery = {}) => {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value))
  }
  const queryString = params.toString()
  return request<CommentsPage>(`/analysis/${analysisId}/comments${queryString ? `?${queryString}` : ''}`)
}

/* ----------------------------------------------------------------- history */

export const getHistory = (userName?: string) =>
  request<{ analyses: HistoryItem[] }>(
    `/history${userName ? `?user_name=${encodeURIComponent(userName)}` : ''}`,
  )

export const deleteAnalysis = (analysisId: string) =>
  request<{ deleted: boolean }>(`/history/${analysisId}`, { method: 'DELETE' })

export const getProfile = (userName?: string) =>
  request<ProfileStats>(`/profile${userName ? `?user_name=${encodeURIComponent(userName)}` : ''}`)

export const renameProfile = (userName: string, previousName?: string) =>
  post<{ renamed: boolean; user_name: string; analyses_moved?: number }>('/profile/rename', {
    user_name: userName,
    previous_name: previousName ?? null,
  })

/* ----------------------------------------------------------------- exports */

/**
 * Export endpoints return files, so they are fetched as blobs and saved via a
 * temporary object URL. The server sets Content-Disposition, but the filename
 * is built client-side so the browser never has to parse headers.
 */
export async function downloadExport(
  analysisId: string,
  kind: 'csv' | 'excel' | 'report',
  options: { dataset?: 'clean' | 'raw'; format?: 'html' | 'pdf'; platform?: string } = {},
): Promise<void> {
  const params = new URLSearchParams()
  if (kind === 'csv' && options.dataset) params.set('dataset', options.dataset)
  if (kind === 'report' && options.format) params.set('format', options.format)
  const query = params.toString()

  const path =
    kind === 'csv'
      ? `/analysis/${analysisId}/export/csv${query ? `?${query}` : ''}`
      : kind === 'excel'
        ? `/analysis/${analysisId}/export/excel`
        : `/analysis/${analysisId}/export/report${query ? `?${query}` : ''}`

  let response: Response
  try {
    response = await fetch(`${BASE}${path}`)
  } catch {
    throw new ApiError(unreachableMessage(), 'network_error')
  }

  if (!response.ok) {
    let message = 'The export could not be generated.'
    try {
      const body = await response.json()
      if (body?.error?.message) message = body.error.message
    } catch {
      /* keep generic message */
    }
    throw new ApiError(message, 'export_failed', response.status)
  }

  const extension = kind === 'csv' ? 'csv' : kind === 'excel' ? 'xlsx' : (options.format ?? 'html')
  const platform = options.platform ?? 'analysis'
  const filename = `socialscope_${platform}_${analysisId}.${extension}`

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  // Give the browser a moment to start the download before revoking.
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}
