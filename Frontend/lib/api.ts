const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_BASE_URL || API_BASE_URL.replace(/^http/, 'ws')

export type ApiOptions = RequestInit & { auth?: boolean }

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const token = typeof window !== 'undefined' ? sessionStorage.getItem('movie-night-access') : null
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (options.auth !== false && token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  const body = await response.json().catch(() => null)
  if (!response.ok) throw new Error(body?.detail || body?.error || body?.message || `Request failed (${response.status})`)
  return body as T
}

type AuthResponse = {
  access?: string
  refresh?: string
  access_token?: string
  refresh_token?: string
  token?: string
  data?: { access?: string; refresh?: string; access_token?: string; refresh_token?: string; token?: string }
  tokens?: { access?: string; refresh?: string; access_token?: string; refresh_token?: string; token?: string }
}

function getAuthTokens(result: AuthResponse) {
  const source = result.data || result.tokens || result
  return {
    access: source.access || source.access_token || source.token,
    refresh: source.refresh || source.refresh_token,
  }
}

export async function authenticate(path: '/api/auth/login' | '/api/auth/register', payload: Record<string, string>) {
  const result = await api<AuthResponse>(path, { method: 'POST', body: JSON.stringify(payload), auth: false })
  const { access, refresh } = getAuthTokens(result)
  if (!access) throw new Error('Login succeeded but the API did not return an access token.')
  if (typeof window !== 'undefined') {
    sessionStorage.setItem('movie-night-access', access)
    if (refresh) sessionStorage.setItem('movie-night-refresh', refresh)
  }
  return result
}

export async function logout() {
  const refresh = typeof window !== 'undefined' ? sessionStorage.getItem('movie-night-refresh') : null
  return api('/api/auth/logout', {
    method: 'POST',
    body: JSON.stringify(refresh ? { refresh } : {}),
  })
}

export type BackendMovie = {
  id?: number | string
  database_id?: number | string
  movie_id?: number | string
  tmdb_id?: number | string
  tmdbId?: number | string
  tmdb_movie_id?: number | string
  movie?: BackendMovie
  title?: string
  name?: string
  poster_path?: string | null
  poster?: string | null
  overview?: string
  release_date?: string
  year?: string | number
  vote_average?: number | string
  rating?: number | string
  user_rating?: number | string
  genre?: string
  genres?: Array<string | { id?: number | string; name?: string; title?: string }>
  backdrop_path?: string | null
}

type PaginatedMovies = {
  count?: number
  next?: string | null
  previous?: string | null
  results?: Array<BackendMovie & { movie?: BackendMovie }>
}

function normalizeMovieResults(payload: BackendMovie[] | PaginatedMovies) {
  if (Array.isArray(payload)) return payload
  return (payload.results || []).map((item) => {
    if (!item.movie) return item

    // Collection records expose the backend movie directly under `movie`.
    // Keep its `id` for mutations and its `tmdb_id` for detail requests.
    return {
      ...item.movie,
      // Collection serializers put the database movie ID on the wrapper record.
      // Keep that ID for mutations and use the nested movie's TMDB ID for details.
      id: item.id ?? item.movie.id ?? item.movie.movie_id,
      tmdb_id: item.movie.tmdb_id ?? item.movie.tmdbId ?? item.movie.tmdb_movie_id,
      user_rating: item.rating,
    }
  })
}

export async function searchMovies(query: string) {
  const payload = await api<BackendMovie[] | PaginatedMovies>(`/api/movies/search?query=${encodeURIComponent(query)}`)
  return normalizeMovieResults(payload)
}

export async function getMovieDetails(tmdbId: number | string) {
  return api<BackendMovie>(`/api/movies/${encodeURIComponent(tmdbId)}`)
}

export async function getWatchlist() {
  const payload = await api<BackendMovie[] | PaginatedMovies>('/api/watchlist')
  return normalizeMovieResults(payload)
}

export async function addToWatchlist(movie: BackendMovie) {
  const movieId = movie.id
  if (!movieId) throw new Error('This movie is missing its backend movie ID.')
  return api<BackendMovie>(`/api/movies/${encodeURIComponent(movieId)}/watchlist`, {
    method: 'POST',
  })
}

export async function removeFromWatchlist(movieId: number | string) {
  return api(`/api/movies/${encodeURIComponent(movieId)}/watchlist`, { method: 'DELETE' })
}

export async function removeFromWatched(movieId: number | string) {
  return api(`/api/movies/${encodeURIComponent(movieId)}/watched`, { method: 'DELETE' })
}

export async function getWatchedHistory() {
  const payload = await api<BackendMovie[] | PaginatedMovies>('/api/watched')
  return normalizeMovieResults(payload)
}

export type RecommendationQuestion = {
  id: string
  question: string
  options?: string[]
}

export type RecommendationStartResponse = {
  session_id: number | string
  question: RecommendationQuestion
}

export type RecommendationAnswerResponse = {
  completed: boolean
  message?: string
  question?: RecommendationQuestion
}

export type RecommendationCompleteResponse = {
  status: string
  recommendation?: { movie_title?: string }
  movie: BackendMovie
}

export async function startRecommendation() {
  return api<RecommendationStartResponse>('/api/recommendations/start', { method: 'POST' })
}

export async function answerRecommendation(sessionId: number | string, answer: string) {
  return api<RecommendationAnswerResponse>(`/api/recommendations/${encodeURIComponent(sessionId)}/answer`, {
    method: 'POST',
    body: JSON.stringify({ answer }),
  })
}

export async function completeRecommendation(sessionId: number | string) {
  return api<RecommendationCompleteResponse>(`/api/recommendations/${encodeURIComponent(sessionId)}/complete`, { method: 'POST' })
}

export async function markMovieWatched(movie: BackendMovie, rating: number) {
  const movieId = movie.id
  if (!movieId) throw new Error('This movie is missing its backend movie ID.')
  return api<BackendMovie>(`/api/movies/${encodeURIComponent(movieId)}/watched`, {
    method: 'POST',
    body: JSON.stringify({ rating: String(rating) }),
  })
}

export function sessionSocket(sessionId: string, onMessage: (data: unknown) => void, onStatus: (status: 'connected' | 'disconnected' | 'reconnecting') => void) {
  const token = typeof window !== 'undefined' ? sessionStorage.getItem('movie-night-access') : null
  const url = `${WS_BASE_URL}/ws/sessions/${sessionId}/?token=${encodeURIComponent(token || '')}`
  let socket: WebSocket | null = null
  let retry = 0
  let stopped = false
  const connect = () => {
    if (stopped) return
    onStatus(retry ? 'reconnecting' : 'reconnecting')
    socket = new WebSocket(url)
    socket.onopen = () => { retry = 0; onStatus('connected') }
    socket.onmessage = (event) => { try { onMessage(JSON.parse(event.data)) } catch { onMessage(event.data) } }
    socket.onclose = () => { onStatus('disconnected'); if (!stopped) { retry += 1; window.setTimeout(connect, Math.min(1000 * retry, 8000)) } }
  }
  connect()
  return () => { stopped = true; socket?.close() }
}

export { API_BASE_URL }
