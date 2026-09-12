'use client'

import { useEffect, useRef, useState } from 'react'
import { addToWatchlist, answerRecommendation, api, authenticate, completeRecommendation, createSession, endSession, getMovieDetails, getMovieRecommendations, getWatchedHistory, getWatchlist, joinSession, logout, markMovieWatched, removeFromWatched, removeFromWatchlist, searchMovies, sessionSocket, startRecommendation, startSession, type BackendMovie, type RecommendationQuestion, type Session } from '@/lib/api'
import {
  ArrowLeft,
  Bot,
  Check,
  ChevronRight,
  Clock3,
  Film,
  Heart,
  LogOut,
  Menu,
  Search,
  Send,
  Sparkles,
  Star,
  ThumbsDown,
  ThumbsUp,
  Users,
  X,
} from 'lucide-react'

const movies = [
  { id: 1, tmdb_id: 1, title: 'The Quiet Hours', year: '2024', rating: '8.4', genre: 'Drama · Mystery', overview: 'A pianist returns to the coast where she grew up and finds a forgotten recording that changes everything.', image: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=900&q=85', backdrop: 'https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?auto=format&fit=crop&w=1800&q=85' },
  { id: 2, tmdb_id: 2, title: 'After Midnight', year: '2023', rating: '8.1', genre: 'Thriller · Romance', overview: 'Two strangers share one long night across a city that refuses to sleep.', image: 'https://images.unsplash.com/photo-1518930259200-8d8cd3f3a34f?auto=format&fit=crop&w=900&q=85', backdrop: 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1800&q=85' },
  { id: 3, tmdb_id: 3, title: 'The Last Light', year: '2024', rating: '7.9', genre: 'Sci-fi · Adventure', overview: 'On the edge of a fading world, one final signal asks for an answer.', image: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=900&q=85', backdrop: 'https://images.unsplash.com/photo-1519608487953-e999c86e7455?auto=format&fit=crop&w=1800&q=85' },
  { id: 4, tmdb_id: 4, title: 'Velvet Season', year: '2022', rating: '8.7', genre: 'Comedy · Romance', overview: 'A sharp, tender story about a summer that arrives ten years too late.', image: 'https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=900&q=85', backdrop: 'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?auto=format&fit=crop&w=1800&q=85' },
]

const participants: { name: string; initials: string; color: string }[] = []

function toMovie(item: BackendMovie): typeof movies[number] {
  const source = item.movie || item
  const tmdbId = source.tmdb_id || source.tmdbId || source.tmdb_movie_id || (source as BackendMovie & { tmdb?: { id?: number | string } }).tmdb?.id || (source as BackendMovie & { external_id?: number | string }).external_id || source.id || source.movie_id
  const title = typeof source.title === 'string' ? source.title : typeof source.name === 'string' ? source.name : 'Untitled movie'
  const poster = typeof source.poster === 'string' ? source.poster : source.poster_path?.startsWith('http') ? source.poster_path : source.poster_path ? `https://image.tmdb.org/t/p/w500${source.poster_path}` : movies[0].image
  const year = String(source.year || source.release_date?.slice(0, 4) || '—')
  const genreValue = source.genre || source.genres || 'Movie'
  const genre = Array.isArray(genreValue)
    ? genreValue.map((item) => typeof item === 'string' ? item : item?.name || item?.title || '').filter(Boolean).join(' · ') || 'Movie'
    : typeof genreValue === 'string' ? genreValue : 'Movie'
  const userRatingValue = source.user_rating ?? (item.movie ? item.rating : undefined)
  const ratingValue = source.vote_average ?? (source.user_rating == null && !item.movie ? source.rating : undefined)
  const rating = typeof ratingValue === 'object' ? ratingValue?.value || ratingValue?.average || '—' : ratingValue || '—'
  return {
    // Never fall back to TMDB IDs for mutations. The backend `id` is required.
    id: source.id ?? source.movie_id,
    database_id: source.id ?? source.movie_id,
    tmdb_id: tmdbId,
    title,
    year,
    rating: String(rating),
    userRating: userRatingValue == null ? undefined : String(userRatingValue),
    genre,
    overview: source.overview || 'No overview available yet.',
    image: poster,
    backdrop: source.backdrop_path ? `https://image.tmdb.org/t/p/w1280${source.backdrop_path}` : poster,
  }
}

type View = 'home' | 'search' | 'details' | 'watchlist' | 'history' | 'waiting' | 'voting' | 'result' | 'login' | 'register'

export default function Page() {
  const [view, setView] = useState<View>('login')
  const [menuOpen, setMenuOpen] = useState(false)
  const [sessionModal, setSessionModal] = useState<'create' | 'join' | null>(null)
  const [activeSession, setActiveSession] = useState<Session | null>(null)
  const [sessionRole, setSessionRole] = useState<'leader' | 'participant'>('participant')
  const [socketStatus, setSocketStatus] = useState<'connected' | 'disconnected' | 'reconnecting' | null>(null)
  const sessionCleanupRef = useRef<(() => void) | null>(null)
  const sessionSocketRef = useRef<WebSocket | null>(null)
  const [sessionMovie, setSessionMovie] = useState<typeof movies[number] | null>(null)
  const [sessionResult, setSessionResult] = useState<typeof movies[number] | null>(null)
  const [sessionParticipantCount, setSessionParticipantCount] = useState<number | null>(null)
  const [chatOpen, setChatOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<typeof movies>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [selectedMovie, setSelectedMovie] = useState(movies[0])
  const [detailCollection, setDetailCollection] = useState<'watchlist' | 'history' | null>(null)
  const [voteIndex, setVoteIndex] = useState(0)
  const [chatMessages, setChatMessages] = useState<{ from: 'ai' | 'user'; text: string }[]>([])
  const [chatInput, setChatInput] = useState('')
  const [recommendationSessionId, setRecommendationSessionId] = useState<number | string | null>(null)
  const [recommendationQuestion, setRecommendationQuestion] = useState<RecommendationQuestion | null>(null)
  const [recommendationMovie, setRecommendationMovie] = useState<typeof movies[number] | null>(null)
  const [recommendationLoading, setRecommendationLoading] = useState(false)
  const [recommendationError, setRecommendationError] = useState('')
  const [saved, setSaved] = useState<string[]>([])
  const [watchlistMovies, setWatchlistMovies] = useState<typeof movies>([])
  const [watchedMovies, setWatchedMovies] = useState<typeof movies>([])
  const [collectionLoading, setCollectionLoading] = useState(false)
  const [collectionError, setCollectionError] = useState('')
  const [actionLoading, setActionLoading] = useState<'watchlist' | 'watched' | 'delete-watchlist' | 'delete-watched' | null>(null)
  const [ratingMovie, setRatingMovie] = useState<typeof movies[number] | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState('')
  const [recommendations, setRecommendations] = useState<Array<{ id: number | string; title: string; release_date?: string; poster_path?: string | null }>>([])
  const [recommendationsLoading, setRecommendationsLoading] = useState(false)

  useEffect(() => {
    if (!activeSession?.id || activeSession.status === 'waiting') return
    sessionCleanupRef.current?.()
    sessionCleanupRef.current = sessionSocket(String(activeSession.id), (message) => {
      const event = message as { type?: string; status?: string; session?: Session; movie?: BackendMovie; movie_id?: number | string; participant_count?: number; participants?: unknown[] }
      if (event.session) setActiveSession(event.session)
      if (typeof event.participant_count === 'number') setSessionParticipantCount(event.participant_count)
      else if (Array.isArray(event.participants)) setSessionParticipantCount(event.participants.length)
      if (event.status && ['waiting', 'started', 'active', 'voting', 'completed'].includes(event.status)) setActiveSession((current) => current ? { ...current, status: event.status! } : current)
      if (event.type === 'next_movie' && event.movie_id != null) getMovieDetails(event.movie_id).then((movie) => setSessionMovie(toMovie(movie))).catch(() => undefined)
      if (event.type === 'movie_selected' && event.movie) { setSessionResult(toMovie(event.movie)); setView('result') }
      if (event.type === 'no_winner') { setSessionResult(null); setView('home') }
      if (event.type === 'session_started') setView('voting')
    }, setSocketStatus, (socket) => { sessionSocketRef.current = socket })
    return () => { sessionCleanupRef.current?.(); sessionCleanupRef.current = null }
  }, [activeSession?.id, activeSession?.status])

  useEffect(() => () => { sessionCleanupRef.current?.() }, [])

  useEffect(() => {
    if (view !== 'home' && view !== 'watchlist' && view !== 'history') return
    let active = true
    setCollectionLoading(true)
    Promise.all([getWatchlist(), getWatchedHistory()]).then(([watchlist, history]) => {
      if (!active) return
      setWatchlistMovies(watchlist.map(toMovie))
      setWatchedMovies(history.map(toMovie))
      setSaved(watchlist.map((movie) => movie.title || movie.name || '').filter(Boolean))
      setCollectionError('')
    }).catch((error) => {
      if (active) setCollectionError(error instanceof Error ? error.message : 'Could not load your movies.')
    }).finally(() => { if (active) setCollectionLoading(false) })
    return () => { active = false }
  }, [view])

  useEffect(() => {
    const query = searchQuery.trim()
    if (!query) {
      setSearchResults([])
      setSearchError('')
      return
    }
    let active = true
    setSearchLoading(true)
    searchMovies(query).then((results) => {
      if (active) {
        setSearchResults(results.map(toMovie))
        setSearchError('')
      }
    }).catch((error) => {
      if (active) setSearchError(error instanceof Error ? error.message : 'Could not search movies.')
    }).finally(() => { if (active) setSearchLoading(false) })
    return () => { active = false }
  }, [searchQuery])

  const filteredMovies = searchQuery.trim() ? searchResults : []

  async function openMovie(movie: typeof movies[number], collection?: 'watchlist' | 'history') {
    setDetailCollection(collection ?? null)
    setSelectedMovie(movie)
    setDetailError('')
    setRecommendations([])
    setRecommendationsLoading(true)
    setDetailLoading(true)
    setView('details')
    try {
      const detail = await getMovieDetails(movie.tmdb_id)
      // Details use TMDB IDs, while collection mutations use the database movie ID.
      // Keep the collection ID when the detail response does not include it.
      const detailMovie = toMovie(detail)
      setSelectedMovie({
        ...detailMovie,
        // Detail responses provide the backend movie `id` used by mutations.
        // Only fall back to the originating collection ID when details omit it.
        // Keep the originating collection/search record ID for mutations.
        // The detail endpoint is keyed by TMDB ID and may return that value as `id`.
        id: detailMovie.id ?? movie.id,
        database_id: detailMovie.database_id ?? detailMovie.id ?? movie.id,
        tmdb_id: movie.tmdb_id,
      })
      getMovieRecommendations(movie.tmdb_id).then(setRecommendations).catch(() => setRecommendations([])).finally(() => setRecommendationsLoading(false))
    } catch (error) {
      setRecommendationsLoading(false)
      setDetailError(error instanceof Error ? error.message : 'Could not load movie details.')
    } finally {
      setDetailLoading(false)
    }
  }

  async function handleSessionStart() {
    if (!activeSession?.id || sessionRole !== 'leader') return
    try {
      const started = await startSession(activeSession.id)
      // The start response may omit the ID; retain the ID used in the request.
      setActiveSession({ ...activeSession, ...started, id: started.id ?? activeSession.id, code: started.code ?? activeSession.code })
    } catch (error) {
      setCollectionError(error instanceof Error ? error.message : 'Could not start the session.')
    }
  }

  function sendSessionVote(type: 'like' | 'dislike') {
    sessionSocketRef.current?.send(JSON.stringify({ type }))
  }

  async function handleSessionEnd() {
    if (!activeSession || sessionRole !== 'leader') return
    try {
      const ended = await endSession(activeSession.id)
      setActiveSession(ended)
      leaveSession()
    } catch (error) {
      setCollectionError(error instanceof Error ? error.message : 'Could not end the session.')
    }
  }

  function leaveSession() {
    sessionCleanupRef.current?.()
    sessionCleanupRef.current = null
    setActiveSession(null)
    setSocketStatus(null)
    setView('home')
  }

  async function handleLogout() {
    try { await logout() } catch { /* Clear local auth even if the server is unavailable. */ }
    sessionStorage.removeItem('movie-night-access')
    sessionStorage.removeItem('movie-night-refresh')
    setWatchlistMovies([])
    setWatchedMovies([])
    setSaved([])
    setChatOpen(false)
    setSessionModal(null)
    setMenuOpen(false)
    setView('login')
  }

  async function handleWatchlist(movie: typeof movies[number]) {
    if (actionLoading) return
    const isSaved = saved.includes(movie.title)
    setCollectionError('')
    setActionLoading('watchlist')
    try {
      if (isSaved) {
        await removeFromWatchlist(movie.id || movie.title)
        setWatchlistMovies((items) => items.filter((item) => item.title !== movie.title))
        setSaved((items) => items.filter((item) => item !== movie.title))
      } else {
        await addToWatchlist({         id: movie.id, database_id: movie.database_id, title: movie.title, year: movie.year, rating: movie.rating, overview: movie.overview, poster: movie.image, genre: movie.genre })
        setWatchlistMovies((items) => items.some((item) => item.title === movie.title) ? items : [...items, movie])
        setSaved((items) => items.includes(movie.title) ? items : [...items, movie.title])
      }
    } catch (error) {
      setCollectionError(error instanceof Error ? error.message : 'Could not update your watchlist.')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleWatched(movie: typeof movies[number], rating: number) {
    if (actionLoading) return
    setCollectionError('')
    setActionLoading('watched')
    try {
      await markMovieWatched({ id: movie.id, database_id: movie.database_id, title: movie.title, year: movie.year, rating: movie.rating, overview: movie.overview, poster: movie.image, genre: movie.genre }, rating)
      setWatchedMovies((items) => items.some((item) => item.title === movie.title) ? items : [...items, movie])
      setRatingMovie(null)
      setView('history')
    } catch (error) {
      setCollectionError(error instanceof Error ? error.message : 'Could not mark this movie as watched.')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleDelete(movie: typeof movies[number], collection: 'watchlist' | 'history') {
    if (actionLoading || !movie.id) return
    const loadingState = collection === 'watchlist' ? 'delete-watchlist' : 'delete-watched'
    setCollectionError('')
    setActionLoading(loadingState)
    try {
      if (collection === 'watchlist') {
        await removeFromWatchlist(movie.id)
        setWatchlistMovies((items) => items.filter((item) => item.id !== movie.id))
        setSaved((items) => items.filter((title) => title !== movie.title))
      } else {
        await removeFromWatched(movie.id)
        setWatchedMovies((items) => items.filter((item) => item.id !== movie.id))
      }
    } catch (error) {
      setCollectionError(error instanceof Error ? error.message : 'Could not remove this movie.')
    } finally {
      setActionLoading(null)
    }
  }

  async function startChat() {
    setRecommendationLoading(true)
    setRecommendationError('')
    setRecommendationMovie(null)
    try {
      const result = await startRecommendation()
      setRecommendationSessionId(result.session_id)
      setRecommendationQuestion(result.question)
      setChatMessages([{ from: 'ai', text: result.question.question }])
    } catch (error) {
      setRecommendationError(error instanceof Error ? error.message : 'Could not start recommendations.')
    } finally {
      setRecommendationLoading(false)
    }
  }

  async function sendChat(selectedAnswer?: string) {
    const answer = (selectedAnswer ?? chatInput).trim()
    if (!answer || !recommendationSessionId || recommendationLoading) return
    setChatMessages((messages) => [...messages, { from: 'user', text: answer }])
    setChatInput('')
    setRecommendationLoading(true)
    setRecommendationError('')
    try {
      const result = await answerRecommendation(recommendationSessionId, answer)
      if (result.completed) {
        setChatMessages((messages) => [...messages, { from: 'ai', text: result.message || 'All questions answered. Finding your movie…' }])
        const completed = await completeRecommendation(recommendationSessionId)
        const movie = toMovie(completed.movie)
        setRecommendationMovie(movie)
        setChatMessages((messages) => [...messages, { from: 'ai', text: `I found a film for you: ${movie.title}.` }])
        setRecommendationQuestion(null)
      } else if (result.question) {
        setRecommendationQuestion(result.question)
        setChatMessages((messages) => [...messages, { from: 'ai', text: result.question!.question }])
      }
    } catch (error) {
      setRecommendationError(error instanceof Error ? error.message : 'Could not continue recommendations.')
    } finally {
      setRecommendationLoading(false)
    }
  }

  return (
    <main className="min-h-screen overflow-hidden bg-background text-foreground">
      {view !== 'login' && view !== 'register' && <Header onNavigate={setView} onLogout={handleLogout} menuOpen={menuOpen} setMenuOpen={setMenuOpen} onChat={() => setChatOpen(true)} />}
      {view === 'home' && <><Home onCreate={() => setSessionModal('create')} onJoin={() => setSessionModal('join')} onBrowse={() => setView('search')} />{collectionLoading && <p className="fixed bottom-5 left-1/2 z-30 -translate-x-1/2 rounded-full border border-border bg-card px-4 py-2 text-xs text-muted-foreground">Loading your films…</p>}{collectionError && <p role="alert" className="fixed bottom-5 left-1/2 z-30 -translate-x-1/2 rounded-full border border-destructive/40 bg-card px-4 py-2 text-xs text-destructive">{collectionError}</p>}</>}
      {view === 'search' && <SearchView query={searchQuery} setQuery={setSearchQuery} movies={filteredMovies} onBack={() => setView('home')} onMovie={openMovie} />}
      {view === 'details' && <Details movie={selectedMovie} loading={detailLoading} error={detailError || collectionError} onBack={() => setView(detailCollection ?? 'search')} saved={saved.includes(selectedMovie.title)} actionLoading={actionLoading} onSave={() => handleWatchlist(selectedMovie)} onWatched={() => setRatingMovie(selectedMovie)} hideWatchlist={detailCollection === 'watchlist'} hideWatched={detailCollection === 'history'} recommendations={recommendations} recommendationsLoading={recommendationsLoading} onRecommendation={(recommendation) => openMovie({ id: recommendation.id, tmdb_id: recommendation.id, title: recommendation.title, year: recommendation.release_date?.slice(0, 4) || '—', rating: '—', genre: '—', overview: '', image: recommendation.poster_path || movies[0].image, backdrop: recommendation.poster_path || movies[0].image })} />}
      {view === 'watchlist' && <Collection title="Watchlist" subtitle="Films you’ve saved for later." items={watchlistMovies} empty="Your watchlist is waiting for its first great find." onBack={() => setView('home')} onMovie={(movie) => openMovie(movie, 'watchlist')} onDelete={(movie) => handleDelete(movie, 'watchlist')} actionLoading={actionLoading} />}
      {view === 'history' && <Collection title="Watched history" subtitle="A quiet record of nights well spent." items={watchedMovies} empty="Your watched history is waiting for its first movie." onBack={() => setView('home')} onMovie={(movie) => openMovie(movie, 'history')} showRatings onDelete={(movie) => handleDelete(movie, 'history')} actionLoading={actionLoading} />}
      {view === 'waiting' && activeSession && <Waiting session={activeSession} role={sessionRole} participantCount={sessionParticipantCount} socketStatus={socketStatus} onStart={handleSessionStart} onLeave={leaveSession} />}
{view === 'voting' && <Voting movie={sessionMovie || movies[voteIndex % movies.length]} index={voteIndex} onLike={() => sendSessionVote('like')} onDislike={() => sendSessionVote('dislike')} />}
  {view === 'result' && <Result movie={sessionResult || movies[3]} onHome={() => setView('home')} onEnd={activeSession && sessionRole === 'leader' ? handleSessionEnd : undefined} />}
      {(view === 'login' || view === 'register') && <Auth register={view === 'register'} onSwitch={() => setView(view === 'login' ? 'register' : 'login')} onEnter={() => setView('home')} />}

      {sessionModal && <SessionModal mode={sessionModal} onClose={() => setSessionModal(null)} onDone={(session, role) => { setActiveSession(session); setSessionRole(role); setSessionModal(null); setView('waiting') }} />}
      {chatOpen && <Chat onClose={() => setChatOpen(false)} messages={chatMessages} input={chatInput} setInput={setChatInput} onSend={sendChat} onStart={startChat} started={recommendationSessionId !== null} question={recommendationQuestion} movie={recommendationMovie} loading={recommendationLoading} error={recommendationError} />}
      {ratingMovie && <RatingModal movie={ratingMovie} loading={actionLoading === 'watched'} onClose={() => setRatingMovie(null)} onSubmit={(rating) => handleWatched(ratingMovie, rating)} />}
    </main>
  )
}

function Header({ onNavigate, onLogout, onChat, menuOpen, setMenuOpen }: { onNavigate: (view: View) => void; onLogout: () => void; onChat: () => void; menuOpen: boolean; setMenuOpen: (open: boolean) => void }) {
  return <header className="relative z-20 mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-12">
    <button onClick={() => onNavigate('home')} className="flex items-center gap-3" aria-label="Movie Night home"><span className="flex size-9 items-center justify-center rounded-full bg-accent text-accent-foreground"><Film className="size-4" /></span><span className="font-serif text-xl tracking-tight">Movie Night</span></button>
    <nav className="hidden items-center gap-7 text-sm text-muted-foreground md:flex"><button onClick={() => onNavigate('search')} className="transition hover:text-foreground">Search</button><button onClick={onChat} className="flex items-center gap-2 transition hover:text-foreground"><Sparkles className="size-3.5 text-accent" /> AI Chat</button><button onClick={() => onNavigate('watchlist')} className="transition hover:text-foreground">Watchlist</button><button onClick={() => onNavigate('history')} className="transition hover:text-foreground">History</button><button onClick={onLogout} className="flex items-center gap-2 transition hover:text-foreground"><LogOut className="size-3.5" /> Logout</button></nav>
    <button className="rounded-md p-2 md:hidden" onClick={() => setMenuOpen(!menuOpen)} aria-label="Open menu"><Menu className="size-5" /></button>
    {menuOpen && <div className="absolute right-5 top-16 flex min-w-44 flex-col gap-1 rounded-lg border border-border bg-card p-2 shadow-2xl md:hidden"><button className="p-3 text-left text-sm" onClick={() => onNavigate('search')}>Search</button><button className="p-3 text-left text-sm" onClick={onChat}>AI Chat</button><button className="p-3 text-left text-sm" onClick={() => onNavigate('watchlist')}>Watchlist</button><button className="p-3 text-left text-sm" onClick={() => onNavigate('history')}>History</button></div>}
  </header>
}

function Home({ onCreate, onJoin, onBrowse }: { onCreate: () => void; onJoin: () => void; onBrowse: () => void }) {
  return <section className="relative mx-auto flex min-h-[calc(100vh-80px)] max-w-7xl flex-col justify-center px-5 pb-20 pt-10 sm:px-8 lg:px-12"><div className="pointer-events-none absolute right-[-9%] top-1/2 hidden h-[560px] w-[390px] -translate-y-1/2 rotate-[7deg] overflow-hidden rounded-2xl opacity-30 lg:block"><img src={movies[0].backdrop} alt="" className="h-full w-full object-cover" /><div className="absolute inset-0 bg-gradient-to-l from-transparent via-background/35 to-background" /></div><div className="relative max-w-3xl"><p className="mb-6 flex items-center gap-3 text-xs font-medium uppercase tracking-[0.28em] text-accent"><span className="h-px w-8 bg-accent" /> A better way to pick a movie</p><h1 className="max-w-2xl font-serif text-5xl leading-[1.02] tracking-[-0.04em] text-balance sm:text-7xl lg:text-8xl">What are we watching <em className="text-accent">tonight?</em></h1><p className="mt-7 max-w-md text-base leading-7 text-muted-foreground">Gather your people, find a film everyone can agree on, and make the decision part of the night.</p><div className="mt-12 flex flex-col gap-3 sm:flex-row"><button onClick={onCreate} className="group flex h-14 items-center justify-between gap-12 rounded-md bg-accent px-5 text-sm font-semibold uppercase tracking-[0.14em] text-accent-foreground transition hover:brightness-110"><span>Create session</span><ChevronRight className="size-4 transition group-hover:translate-x-1" /></button><button onClick={onJoin} className="flex h-14 items-center justify-between gap-16 rounded-md border border-border bg-card/60 px-5 text-sm font-semibold uppercase tracking-[0.14em] transition hover:border-accent/60"><span>Join session</span><ChevronRight className="size-4" /></button></div><button onClick={onBrowse} className="mt-12 flex items-center gap-2 text-sm text-muted-foreground transition hover:text-foreground">Or browse movies <ArrowLeft className="size-3 rotate-180" /></button></div><div className="relative mt-24 flex items-center gap-5 border-t border-border pt-5 text-xs text-muted-foreground"><span className="flex items-center gap-2"><Users className="size-3.5" /> Made for movie nights</span><span className="h-1 w-1 rounded-full bg-border" /><span>One decision. Together.</span></div></section>
}

function SearchView({ query, setQuery, movies, onBack, onMovie }: { query: string; setQuery: (v: string) => void; movies: typeof import('./page').movies; onBack: () => void; onMovie: (m: typeof import('./page').movies[number]) => void }) {
  return <section className="mx-auto max-w-7xl px-5 pb-20 pt-10 sm:px-8 lg:px-12"><button onClick={onBack} className="mb-14 flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="size-4" /> Back</button><div className="flex flex-col justify-between gap-7 border-b border-border pb-8 sm:flex-row sm:items-end"><div><p className="mb-3 text-xs uppercase tracking-[0.24em] text-accent">The library</p><h1 className="font-serif text-5xl tracking-tight">Find your next film.</h1></div><div className="relative w-full sm:w-80"><Search className="absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search movies" className="h-12 w-full rounded-md border border-border bg-card pl-11 pr-4 text-sm outline-none transition placeholder:text-muted-foreground focus:border-accent" /></div></div>{movies.length ? <div className="mt-10 grid grid-cols-2 gap-x-4 gap-y-10 sm:grid-cols-3 lg:grid-cols-4">{movies.map((movie, index) => <MovieCard key={`${movie.tmdb_id ?? movie.id ?? movie.title}-${index}`} movie={movie} onClick={() => onMovie(movie)} />)}</div> : <div className="flex min-h-60 flex-col items-center justify-center text-center"><Search className="mb-4 size-8 text-muted-foreground" /><p className="font-serif text-2xl">No films found</p><p className="mt-2 text-sm text-muted-foreground">Try another title.</p></div>}</section>
}

function MovieCard({ movie, onClick }: { movie: typeof movies[number]; onClick: () => void }) { return <button onClick={onClick} className="group text-left"><div className="relative aspect-[2/3] overflow-hidden rounded-md bg-card"><img src={movie.image} alt={`${movie.title} poster`} className="h-full w-full object-cover transition duration-500 group-hover:scale-105" /><div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 transition group-hover:opacity-100" /><span className="absolute bottom-3 left-3 flex items-center gap-1 text-xs opacity-0 transition group-hover:opacity-100"><Star className="size-3 fill-accent text-accent" /> {movie.rating}</span></div><h3 className="mt-3 font-medium">{movie.title}</h3><p className="mt-1 text-xs text-muted-foreground">{movie.year} · {movie.genre.split(' · ')[0]}</p></button> }

  function RatingModal({ movie, loading, onClose, onSubmit }: { movie: typeof movies[number]; loading: boolean; onClose: () => void; onSubmit: (rating: number) => void }) {
    const [rating, setRating] = useState(10)
    return <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 px-5 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="rating-title">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl sm:p-8">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div><p className="mb-2 text-xs uppercase tracking-[0.24em] text-accent">One last thing</p><h2 id="rating-title" className="font-serif text-3xl">How would you rate it?</h2><p className="mt-2 text-sm text-muted-foreground">Give {movie.title} a rating out of 10 before saving it to your watched history.</p></div>
          <button type="button" onClick={onClose} className="rounded-full p-2 text-muted-foreground transition hover:bg-muted hover:text-foreground" aria-label="Close rating dialog"><X className="size-5" /></button>
        </div>
        <div className="mb-7 flex items-center justify-between gap-1" aria-label={`Rating ${rating} out of 10`} role="radiogroup">
          {Array.from({ length: 10 }, (_, index) => index + 1).map((value) => <button type="button" key={value} onClick={() => setRating(value)} className={`flex size-8 items-center justify-center rounded-full transition hover:scale-110 sm:size-9 ${value <= rating ? 'text-accent' : 'text-muted-foreground/30'}`} aria-label={`${value} out of 10`} aria-checked={value === rating} role="radio"><Star className="size-5 fill-current" /></button>)}
        </div>
        <div className="mb-6 flex items-center justify-between text-sm"><span className="text-muted-foreground">Your rating</span><span className="font-medium text-accent">{rating}/10</span></div>
        <button type="button" disabled={loading} onClick={() => onSubmit(rating)} className="w-full rounded-md bg-accent px-4 py-3 text-sm font-medium text-accent-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50">{loading ? 'Saving…' : 'Save to watched history'}</button>
      </div>
    </div>
  }

  function Details({ movie, loading, error, onBack, saved, actionLoading, onSave, onWatched, hideWatchlist = false, hideWatched = false, recommendations, recommendationsLoading, onRecommendation }: { movie: typeof movies[number]; loading: boolean; error: string; saved: boolean; onBack: () => void; actionLoading: 'watchlist' | 'watched' | 'delete-watchlist' | 'delete-watched' | null; onSave: () => void; onWatched: () => void; hideWatchlist?: boolean; hideWatched?: boolean; recommendations: Array<{ id: number | string; title: string; release_date?: string; poster_path?: string | null }>; recommendationsLoading: boolean; onRecommendation: (recommendation: { id: number | string; title: string; release_date?: string; poster_path?: string | null }) => void }) { const [showAllRecommendations, setShowAllRecommendations] = useState(false); const visibleRecommendations = showAllRecommendations ? recommendations : recommendations.slice(0, 5); return <section className="relative min-h-[calc(100vh-80px)]"><div className="pointer-events-none absolute inset-0 h-[70vh] overflow-hidden opacity-45"><img src={movie.backdrop} alt="" className="h-full w-full object-cover" /><div className="absolute inset-0 bg-gradient-to-b from-background/20 via-background/70 to-background" /></div><div className="relative z-10 mx-auto max-w-7xl px-5 pb-20 pt-10 sm:px-8 lg:px-12">{loading && <p className="mb-4 text-sm text-muted-foreground">Loading movie details…</p>}{error && <p role="alert" className="mb-4 text-sm text-destructive">{error}</p>}<button type="button" onClick={onBack} className="mb-20 flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="size-4" /> Back to search</button><div className="flex flex-col items-start gap-9 md:flex-row md:items-end"><img src={movie.image} alt={`${movie.title} poster`} className="w-40 rounded-lg shadow-2xl sm:w-52" /><div className="max-w-2xl"><div className="mb-4 flex items-center gap-4 text-xs text-muted-foreground"><span className="flex items-center gap-1 text-accent"><Star className="size-3 fill-accent" /> {movie.rating}</span><span>{movie.year}</span><span>{movie.genre}</span></div><h1 className="font-serif text-5xl tracking-tight sm:text-7xl">{movie.title}</h1><p className="mt-6 max-w-lg text-base leading-7 text-muted-foreground">{movie.overview}</p><div className="mt-8 flex flex-wrap gap-3">{!hideWatchlist && <button type="button" disabled={actionLoading !== null} onClick={onSave} className={`flex h-11 items-center gap-2 rounded-md px-4 text-sm font-medium transition disabled:cursor-wait disabled:opacity-60 ${saved ? 'bg-accent text-accent-foreground' : 'border border-border bg-card'}`}><Heart className={`size-4 ${saved ? 'fill-current' : ''}`} /> {actionLoading === 'watchlist' ? 'Saving…' : saved ? 'In watchlist' : 'Add to watchlist'}</button>}{!hideWatched && <button type="button" disabled={actionLoading !== null} onClick={onWatched} className="flex h-11 items-center gap-2 rounded-md border border-border px-4 text-sm font-medium transition disabled:cursor-wait disabled:opacity-60"><Check className="size-4" /> {actionLoading === 'watched' ? 'Saving…' : 'Mark as watched'}</button>}</div></div></div></div><div className="mx-auto mt-16 max-w-7xl px-5 pb-16 sm:px-8 lg:px-12"><div className="mb-6"><p className="text-xs uppercase tracking-[0.24em] text-accent">You may also like</p><h2 className="mt-2 font-serif text-3xl">More films to explore</h2></div>{recommendationsLoading ? <p className="text-sm text-muted-foreground">Finding recommendations…</p> : recommendations.length ? <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-5">{visibleRecommendations.map((recommendation) => <button key={recommendation.id} type="button" onClick={() => onRecommendation(recommendation)} className="group overflow-hidden rounded-lg border border-border bg-card text-left transition hover:-translate-y-1 hover:border-accent hover:shadow-lg hover:shadow-accent/10"><img src={recommendation.poster_path || movies[0].image} alt={`${recommendation.title} poster`} className="aspect-[2/3] w-full object-cover transition duration-300 group-hover:scale-105" /><span className="block p-3"><span className="line-clamp-2 text-sm font-medium">{recommendation.title}</span><span className="mt-1 block text-xs text-muted-foreground">{recommendation.release_date?.slice(0, 4) || '—'}</span><span className="mt-3 block text-xs text-accent opacity-0 transition group-hover:opacity-100">View details</span></span></button>)}</div> : <p className="text-sm text-muted-foreground">No recommendations available.</p>}{recommendations.length > 5 && !showAllRecommendations && <button type="button" onClick={() => setShowAllRecommendations(true)} className="mt-6 rounded-md border border-border px-5 py-2.5 text-sm transition hover:border-accent hover:text-accent">Show more</button>}</div></section> }

function Collection({ title, subtitle, items, empty, onBack, onMovie, onDelete, actionLoading, showRatings = false }: { title: string; subtitle: string; items: typeof movies; empty?: string; onBack: () => void; onMovie: (m: typeof movies[number]) => void; onDelete: (m: typeof movies[number]) => void; actionLoading: 'watchlist' | 'watched' | 'delete-watchlist' | 'delete-watched' | null; showRatings?: boolean }) { return <section className="mx-auto max-w-7xl px-5 pb-20 pt-10 sm:px-8 lg:px-12"><button onClick={onBack} className="mb-14 flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="size-4" /> Back</button><p className="mb-3 text-xs uppercase tracking-[0.24em] text-accent">Your films</p><h1 className="font-serif text-5xl tracking-tight">{title}</h1><p className="mt-3 text-sm text-muted-foreground">{subtitle}</p>{items.length ? <div className="mt-10 grid grid-cols-2 gap-x-4 gap-y-10 sm:grid-cols-3 lg:grid-cols-4">{items.map((movie, index) => <div key={`${movie.tmdb_id ?? movie.id ?? movie.title}-${index}`}><MovieCard movie={movie} onClick={() => onMovie(movie)} />{showRatings && (movie as typeof movie & { userRating?: string }).userRating && <p className="mt-2 flex items-center gap-1 text-xs text-accent"><Star className="size-3 fill-current" /> Your rating: {(movie as typeof movie & { userRating?: string }).userRating}/10</p>}<button type="button" disabled={actionLoading !== null} onClick={() => onDelete(movie)} className="mt-3 flex h-9 w-full items-center justify-center gap-2 rounded-md border border-destructive/40 text-xs text-destructive transition hover:bg-destructive/10 disabled:cursor-not-allowed disabled:opacity-50"><X className="size-3" />{actionLoading === (showRatings ? 'delete-watched' : 'delete-watchlist') ? 'Deleting…' : 'Delete'}</button></div>)}</div> : <div className="flex min-h-72 flex-col items-center justify-center text-center"><Film className="mb-4 size-8 text-accent" /><p className="font-serif text-2xl">Nothing here yet</p><p className="mt-2 max-w-xs text-sm leading-6 text-muted-foreground">{empty}</p></div>}</section> }

function Waiting({ session, role, participantCount, socketStatus, onStart, onLeave }: { session: Session; role: 'leader' | 'participant'; participantCount: number | null; socketStatus: 'connected' | 'disconnected' | 'reconnecting' | null; onStart: () => void; onLeave: () => void }) { return <section className="mx-auto flex min-h-[calc(100vh-80px)] max-w-3xl flex-col justify-center px-5 pb-20 sm:px-8"><button onClick={onLeave} className="mb-16 flex items-center gap-2 self-start text-sm text-muted-foreground hover:text-foreground"><X className="size-4" /> Leave session</button><div className="flex items-start justify-between gap-5"><div><p className="mb-3 text-xs uppercase tracking-[0.24em] text-accent">Movie night session</p><h1 className="font-serif text-5xl tracking-tight sm:text-6xl">{session.code}</h1><p className="mt-4 text-sm text-muted-foreground">{session.status === 'waiting' ? 'Waiting for the leader to start the session.' : 'Session started.'}</p></div><div className="rounded-md border border-border bg-card px-4 py-3 text-center"><p className="text-[10px] uppercase tracking-widest text-muted-foreground">Code</p><p className="mt-1 font-mono text-lg tracking-[0.2em]">{session.code}</p></div></div><div className="mt-14 rounded-lg border border-border bg-card/70 p-5 sm:p-7"><div className="flex items-center justify-between border-b border-border pb-5"><span className="flex items-center gap-2 text-sm font-medium"><Users className="size-4 text-accent" /> {participantCount === null ? 'Participants unavailable' : `${participantCount} ${participantCount === 1 ? 'participant' : 'participants'}`}</span><span className="flex items-center gap-2 text-xs text-accent"><span className={`size-2 rounded-full ${socketStatus === 'connected' ? 'bg-accent' : 'bg-muted-foreground'}`} /> {socketStatus === 'connected' ? 'Live connection' : session.status === 'waiting' ? 'Waiting to start' : 'Connecting…'}</span></div><div className="flex flex-col gap-4 py-6">{participants.map((person, index) => <div key={person.name} className="flex items-center justify-between"><div className="flex items-center gap-3"><span className={`flex size-10 items-center justify-center rounded-full text-xs font-semibold text-foreground ${person.color}`}>{person.initials}</span><span className="text-sm">{person.name}</span>{index === 0 && <span className="rounded-full border border-accent/30 px-2 py-1 text-[10px] uppercase tracking-wider text-accent">Leader</span>}</div><span className="text-xs text-muted-foreground">Joined</span></div>)}</div>{<button onClick={onStart} className="h-13 w-full rounded-md bg-accent text-sm font-semibold uppercase tracking-[0.16em] text-accent-foreground transition hover:brightness-110">Start session</button>}</div><p className="mt-6 text-center text-xs text-muted-foreground">Share the code with friends to invite them.</p></section> }

function Voting({ movie, index, onLike, onDislike }: { movie: typeof movies[number]; index: number; onLike: () => void; onDislike: () => void }) { return <section className="mx-auto flex min-h-[calc(100vh-80px)] max-w-3xl flex-col items-center px-5 pb-16 pt-4 text-center sm:px-8"><div className="mb-8 flex w-full items-center justify-between text-xs text-muted-foreground"><span className="flex items-center gap-2"><span className="size-2 animate-pulse rounded-full bg-accent" /> Live session</span><span>{Math.min(index + 1, 8)} <span className="text-border">/</span> 8</span></div><p className="text-xs uppercase tracking-[0.24em] text-accent">Would you watch this?</p><div className="relative mt-5 aspect-[2/3] w-[min(68vw,330px)] overflow-hidden rounded-xl shadow-2xl shadow-black/40"><img key={movie.title} src={movie.image} alt={`${movie.title} poster`} className="h-full w-full object-cover" /><div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 to-transparent p-5 pt-20 text-left"><h1 className="font-serif text-3xl text-white">{movie.title}</h1><p className="mt-1 text-xs text-white/70">{movie.year} · {movie.genre}</p></div></div><div className="mt-6 flex items-center gap-5"><button onClick={onDislike} className="flex size-14 items-center justify-center rounded-full border border-border bg-card text-muted-foreground transition hover:border-destructive hover:text-destructive" aria-label="Dislike"><ThumbsDown className="size-5" /></button><button onClick={onLike} className="flex size-[4.5rem] items-center justify-center rounded-full bg-accent text-accent-foreground shadow-lg shadow-accent/15 transition hover:scale-105" aria-label="Like"><ThumbsUp className="size-6" /></button></div><p className="mt-5 max-w-sm text-xs leading-5 text-muted-foreground">{movie.overview}</p></section> }

function Result({ movie, onHome, onEnd }: { movie: typeof movies[number]; onHome: () => void; onEnd?: () => void }) { return <section className="relative mx-auto flex min-h-[calc(100vh-80px)] max-w-5xl flex-col items-center justify-center overflow-hidden px-5 pb-20 text-center sm:px-8"><div className="pointer-events-none absolute inset-x-0 top-0 h-96 opacity-30"><img src={movie.backdrop} alt="" className="h-full w-full object-cover" /><div className="absolute inset-0 bg-gradient-to-b from-background/20 to-background" /></div><div className="relative"><p className="mb-5 text-xs uppercase tracking-[0.28em] text-accent">Decision made</p><h1 className="font-serif text-5xl tracking-tight sm:text-7xl">Tonight&apos;s movie.</h1><img src={movie.image} alt={`${movie.title} poster`} className="mx-auto mt-10 w-48 rounded-lg shadow-2xl sm:w-56" /><h2 className="mt-7 font-serif text-3xl">{movie.title}</h2><div className="mt-3 flex items-center justify-center gap-4 text-xs text-muted-foreground"><span className="flex items-center gap-1 text-accent"><Star className="size-3 fill-accent" /> {movie.rating}</span><span>{movie.year}</span></div><p className="mx-auto mt-5 max-w-md text-sm leading-6 text-muted-foreground">{movie.overview}</p><div className="mt-8 flex flex-wrap justify-center gap-3"><button onClick={onHome} className="h-12 rounded-md bg-accent px-6 text-sm font-semibold text-accent-foreground">Back home</button>{onEnd && <button onClick={onEnd} className="h-12 rounded-md border border-border px-6 text-sm font-semibold">End session</button>}</div></div></section> }

function SessionModal({ mode, onClose, onDone }: { mode: 'create' | 'join'; onClose: () => void; onDone: (session: Session, role: 'leader' | 'participant') => void }) { const [name, setName] = useState(''); const [error, setError] = useState(''); const [loading, setLoading] = useState(false); async function submit() { if (!name.trim()) return; setLoading(true); setError(''); try { if (mode === 'create') { const session = await createSession(name.trim()); onDone(session, 'leader') } else { const code = name.trim().toUpperCase(); const joined = await joinSession(code); onDone({ id: joined.id, code, status: 'waiting' }, 'participant') } } catch (e) { setError(e instanceof Error ? e.message : 'Could not connect to the session.') } finally { setLoading(false) } } return <div className="fixed inset-0 z-40 flex items-center justify-center bg-background/80 px-5 backdrop-blur-sm"><div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-2xl sm:p-8"><div className="flex items-start justify-between"><div><p className="text-xs uppercase tracking-[0.2em] text-accent">{mode === 'create' ? 'Start something' : 'You’re invited'}</p><h2 className="mt-3 font-serif text-3xl">{mode === 'create' ? 'Create a session' : 'Join a session'}</h2></div><button onClick={onClose} className="rounded-full p-2 text-muted-foreground hover:text-foreground" aria-label="Close"><X className="size-4" /></button></div><label className="mt-8 block text-xs font-medium text-muted-foreground">{mode === 'create' ? 'Session name' : 'Session code'}</label><input value={name} onChange={(e) => setName(e.target.value)} placeholder={mode === 'create' ? 'Friday at Maya’s' : 'M8K2Q'} className="mt-2 h-12 w-full rounded-md border border-border bg-background px-4 font-mono text-sm outline-none focus:border-accent" />{error && <p className="mt-3 text-sm text-destructive">{error}</p>}<button onClick={submit} disabled={loading} className="mt-5 h-12 w-full rounded-md bg-accent text-sm font-semibold uppercase tracking-[0.14em] text-accent-foreground disabled:opacity-60">{loading ? 'Connecting…' : mode === 'create' ? 'Create session' : 'Join session'}</button></div></div> }

function Chat({ onClose, messages, input, setInput, onSend, onStart, started, question, movie, loading, error }: { onClose: () => void; messages: { from: string; text: string }[]; input: string; setInput: (v: string) => void; onSend: (answer?: string) => void; onStart: () => void; started: boolean; question: RecommendationQuestion | null; movie: typeof movies[number] | null; loading: boolean; error: string }) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const panel = messagesEndRef.current
    if (panel) panel.scrollTo({ top: panel.scrollHeight, behavior: 'smooth' })
  }, [messages, question, movie, loading, error])

  return <div className="fixed inset-0 z-40 bg-background/40 backdrop-blur-[2px]"><aside className="absolute bottom-0 right-0 top-0 flex w-full max-w-md flex-col border-l border-border bg-card shadow-2xl"><div className="flex items-center justify-between border-b border-border p-5"><div className="flex items-center gap-3"><span className="flex size-9 items-center justify-center rounded-full bg-accent text-accent-foreground"><Bot className="size-4" /></span><div><p className="text-sm font-medium">The Movie Concierge</p><p className="text-xs text-muted-foreground">Guided recommendations</p></div></div><button onClick={onClose} className="p-2 text-muted-foreground hover:foreground" aria-label="Close chat"><X className="size-4" /></button></div><div className="border-b border-border p-4"><button type="button" onClick={onStart} disabled={loading} className="h-10 w-full rounded-md bg-accent text-sm font-semibold text-accent-foreground disabled:opacity-60">{started ? 'Restart session' : 'Start recommendation'}</button></div><div ref={messagesEndRef} className="flex flex-1 flex-col gap-5 overflow-y-auto p-5">{messages.map((message, i) => <div key={i} className={`max-w-[85%] rounded-lg p-4 text-sm leading-6 ${message.from === 'user' ? 'self-end bg-accent text-accent-foreground' : 'border border-border bg-background text-muted-foreground'}`}>{message.text}</div>)}{movie && <div className="max-w-[85%] rounded-lg border border-border bg-background p-4 text-sm leading-6 text-muted-foreground"><div className="border-b border-border px-4 py-3"><p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-accent">Your movie match</p><p className="mt-1 text-sm text-muted-foreground">Based on your answers, I think you&apos;ll enjoy this one.</p></div><img src={movie.image} alt={`${movie.title} poster`} className="float-left mr-4 h-24 w-16 rounded-md object-cover" /><div className="p-4"><p className="font-serif text-2xl">{movie.title}</p><p className="mt-2 flex flex-wrap gap-x-2 text-xs text-muted-foreground"><span>{movie.year}</span><span>·</span><span>{movie.genre}</span><span>·</span><span className="text-accent">{movie.rating}/10</span></p><p className="mt-3 text-sm leading-6 text-muted-foreground">{movie.overview}</p></div></div>}{error && <p role="alert" className="text-sm text-destructive">{error}</p>}</div>{started && question && <div className="border-t border-border p-4"><p className="mb-3 text-xs uppercase tracking-[0.18em] text-muted-foreground">Choose your answer</p><div className="flex flex-col gap-2">{(question.options || []).map((option) => <button key={option} type="button" disabled={loading} onClick={() => onSend(option)} className="rounded-md border border-border bg-background px-4 py-3 text-left text-sm transition hover:border-accent hover:bg-accent/10 disabled:cursor-not-allowed disabled:opacity-50">{option}</button>)}</div></div>}<div className="hidden"><form onSubmit={(e) => { e.preventDefault(); if (!e.nativeEvent.isComposing) onSend() }} className="border-t border-border p-4"><div className="flex items-center gap-2 rounded-md border border-border bg-background p-2"><input value={input} onChange={(e) => setInput(e.target.value)} disabled={!started || !question || loading} onKeyDown={(e) => { if (e.key === 'Enter' && !e.nativeEvent.isComposing && e.keyCode !== 229) { e.preventDefault(); onSend() } }} placeholder={started ? question?.question || 'Recommendation complete' : 'Start a session first'} className="min-w-0 flex-1 bg-transparent px-2 text-sm outline-none disabled:opacity-50" aria-label="Answer recommendation question" /><button type="submit" disabled={!started || !question || loading} className="flex size-9 items-center justify-center rounded-md bg-accent text-accent-foreground disabled:opacity-50" aria-label="Send answer"><Send className="size-4" /></button></div></form></div></aside></div>
}

function LegacyChat({ onClose, messages, input, setInput, onSend }: { onClose: () => void; messages: { from: string; text: string }[]; input: string; setInput: (v: string) => void; onSend: () => void }) { return <div className="fixed inset-0 z-40 bg-background/40 backdrop-blur-[2px]"><aside className="absolute bottom-0 right-0 top-0 flex w-full max-w-md flex-col border-l border-border bg-card shadow-2xl"><div className="flex items-center justify-between border-b border-border p-5"><div className="flex items-center gap-3"><span className="flex size-9 items-center justify-center rounded-full bg-accent text-accent-foreground"><Bot className="size-4" /></span><div><p className="text-sm font-medium">The Movie Concierge</p><p className="text-xs text-muted-foreground">Thoughtful picks, no endless scrolling.</p></div></div><button onClick={onClose} className="p-2 text-muted-foreground hover:text-foreground" aria-label="Close chat"><X className="size-4" /></button></div><div className="flex flex-1 flex-col gap-5 overflow-y-auto p-5">{messages.map((message, i) => <div key={i} className={`max-w-[85%] rounded-lg p-4 text-sm leading-6 ${message.from === 'user' ? 'self-end bg-accent text-accent-foreground' : 'border border-border bg-background text-muted-foreground'}`}>{message.text}</div>)}</div><form onSubmit={(e) => { e.preventDefault(); if (!e.nativeEvent.isComposing) onSend() }} className="border-t border-border p-4"><div className="flex items-center gap-2 rounded-md border border-border bg-background p-2"><input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.nativeEvent.isComposing && e.keyCode !== 229) { e.preventDefault(); onSend() } }} placeholder="A mood, a genre, a feeling..." className="min-w-0 flex-1 bg-transparent px-2 text-sm outline-none" aria-label="Message the movie concierge" /><button type="submit" className="flex size-9 items-center justify-center rounded-md bg-accent text-accent-foreground" aria-label="Send message"><Send className="size-4" /></button></div></form></aside></div> }

function Auth({ register, onSwitch, onEnter }: { register: boolean; onSwitch: () => void; onEnter: () => void }) { const [displayName, setDisplayName] = useState(''); const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [error, setError] = useState(''); const [loading, setLoading] = useState(false); async function submit() { setLoading(true); setError(''); try { await authenticate(register ? '/api/auth/register' : '/api/auth/login', register ? { display_name: displayName, email, password } : { email, password }); onEnter() } catch (e) { setError(e instanceof Error ? e.message : 'Authentication failed.') } finally { setLoading(false) } } return <section className="flex min-h-screen"><div className="relative hidden flex-1 overflow-hidden lg:block"><img src={movies[2].backdrop} alt="Cinematic film still" className="h-full w-full object-cover opacity-70" /><div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent to-background" /></div><div className="flex w-full max-w-xl flex-col justify-center px-7 py-10 sm:px-16 lg:w-[48%]"><button onClick={onEnter} className="mb-20 flex items-center gap-3 self-start"><span className="flex size-9 items-center justify-center rounded-full bg-accent text-accent-foreground"><Film className="size-4" /></span><span className="font-serif text-xl">Movie Night</span></button><p className="text-xs uppercase tracking-[0.24em] text-accent">Welcome back</p><h1 className="mt-4 font-serif text-5xl tracking-tight">{register ? 'Make room for good films.' : 'Your next movie night awaits.'}</h1><div className="mt-10 flex flex-col gap-5">{register && <label className="text-sm">Display name<input value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="mt-2 h-12 w-full rounded-md border border-border bg-card px-4 outline-none focus:border-accent" placeholder="Maya Chen" /></label>}<label className="text-sm">Email<input value={email} onChange={(e) => setEmail(e.target.value)} className="mt-2 h-12 w-full rounded-md border border-border bg-card px-4 outline-none focus:border-accent" placeholder="you@example.com" type="email" /></label><label className="text-sm">Password<input value={password} onChange={(e) => setPassword(e.target.value)} className="mt-2 h-12 w-full rounded-md border border-border bg-card px-4 outline-none focus:border-accent" placeholder="••••••••" type="password" /></label>{error && <p className="text-sm text-destructive">{error}</p>}<button onClick={submit} disabled={loading} className="mt-3 h-12 rounded-md bg-accent text-sm font-semibold uppercase tracking-[0.14em] text-accent-foreground disabled:opacity-60">{loading ? 'Connecting…' : register ? 'Register' : 'Log in'}</button></div><p className="mt-7 text-sm text-muted-foreground">{register ? 'Already have an account?' : 'New to Movie Night?'} <button onClick={onSwitch} className="text-foreground underline underline-offset-4">{register ? 'Log in' : 'Create an account'}</button></p></div></section> }
