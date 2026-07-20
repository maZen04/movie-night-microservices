# 🎬 Movie Night

Movie Night is a group movie-selection application that lets people discover movies, manage a personal watchlist, and **vote together in real time** to pick what to watch — no more endless scrolling and "you pick" back-and-forth.

---

## ✨ Features

- **Movie Discovery** — Search movies via [The Movie Database (TMDB)](https://www.themoviedb.org/) API and view rich details (poster, overview, release year, rating).
- **Personal Watchlist** — Add, remove, and manage movies you plan to watch.
- **Watched History** — Mark movies as watched and rate them.
- **Real-Time Voting Sessions** — Create or join a session with a 6-digit code and vote synchronously with your group until a movie wins.
- **AI Assistant** — A short conversational Q&A that recommends a movie based on your mood and preferences.

---

## 🧠 Core Concepts

| Term | Definition |
|---|---|
| **Session** | A temporary real-time group activity identified by a 6-digit code. Destroyed once it ends. |
| **Leader** | The user who creates the session. Only the Leader can start it. The session survives if the Leader disconnects mid-session. |
| **Member** | Any user who joins a session (the Leader is also a Member). |
| **Watchlist** | A user's personal list of movies they intend to watch. |
| **Pool** | The deduplicated, shuffled combination of all participants' watchlists — the candidates voted on in a session. |
| **Vote** | A yes/no response from a member on the currently displayed movie. |
| **Selected Movie** | The final outcome of a session — either unanimous agreement, or the highest vote count with a random tiebreaker. |
| **AI Assistant** | An LLM-backed feature that asks a few questions and returns a single movie suggestion. |

> 📌 Note: **Leader** and **Member** are *roles scoped to a session*, not account types. Any authenticated user can be a Leader in one session and a Member in another.

---

## 🏗️ Architecture

Movie Night is built as a **microservices architecture** behind a single entry point.

```
Client (Web / Mobile)
        │
        ▼
   API Gateway  ──►  Handles auth (JWT) + routing
        │
   ┌────┼────────────┬──────────────┐
   ▼    ▼             ▼              ▼
User   Movie       Session        AI Assistant
Svc    Svc          Svc              Svc
 │       │            │                │
Postgres Postgres,  Postgres,        LLM API
         Redis       Redis
         │
      TMDB API
```

| Service | Responsibility | Data Store | External Dependency |
|---|---|---|---|
| **User Service** | Registration, login, JWT issuance, profile | PostgreSQL | — |
| **Movie Service** | TMDB search/details, watchlist, watched history | PostgreSQL, Redis | TMDB API |
| **Session Service** | Session lifecycle, real-time synchronized voting | PostgreSQL, Redis | — |
| **AI Assistant Service** | Conversational recommendation flow | — | LLM API |

- Clients **never** talk to individual services directly — everything goes through the **API Gateway**.
- Each service **owns its own data**; there is no shared database and no cross-service foreign keys. Any cross-service communication happens via internal API calls.
- **Session state is ephemeral** and lives in Redis; if it's lost mid-session, the session cannot be recovered.

---

## 🗄️ Data Model

The relational schema spans 8 entities in PostgreSQL:

- **Users** — central identity entity. Holds no role or session-specific attributes.
- **Movies / Genres / MovieGenres** — a local mirror of TMDB data (many-to-many with genres), ensuring previously seen movies stay resolvable even if TMDB/Redis is down.
- **Watchlist** — many-to-one from Users → Movies.
- **WatchedHistory** — many-to-one from Users → Movies, with an optional `rating`.
- **Sessions** — the permanent record of a voting session (code, status, timestamps, and the final `movie_selected_id` once concluded). Live voting state itself stays in Redis.
- **SessionParticipants** — join table between Sessions and Users, storing each participant's `role` (leader/member) for that specific session.

---

## ⚙️ How a Voting Session Works

1. A user creates a session and becomes its **Leader**, receiving a unique 6-digit code.
2. Other users **join** using that code, becoming **Members**.
3. Only the Leader can **start** the session.
4. On start, the **Pool** is built: all participants' watchlists are combined, deduplicated, and shuffled.
5. The current movie is **broadcast to everyone in real time** over WebSocket.
6. Each participant casts a **yes/no vote**.
7. The session **advances** once everyone has voted, or when a voting timeout elapses.
8. The session **ends** when either:
   - Everyone votes **yes** on the current movie → it becomes the **Selected Movie**, or
   - The pool is exhausted with no unanimous pick → the movie with the **most votes wins** (ties broken randomly).
9. The **Selected Movie** (with poster) is broadcast to all participants, and the session code is **invalidated**.

If a participant's connection drops, they can **reconnect and resume** without restarting the session.

---

## 🔐 Security

- Passwords are stored using a **secure one-way hash** — never in plaintext.
- Authentication uses **JWTs**, which expire after a defined period (e.g. 24 hours).
- All endpoints except registration/login **require a valid JWT**.
- Session codes are **rate-limited** per IP/user to prevent brute-force guessing.
- All client-server traffic uses **HTTPS/WSS** in production.

---

## 📈 Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | WebSocket broadcasts (movie updates, votes, results) reach all participants within **1 second** under normal conditions. TMDB responses are cached for **24 hours**. |
| **Scalability** | Session state lives in Redis (not in-memory), so any Session Service instance can serve any active session. |
| **Availability** | Cached movie data stays available if TMDB is down. The AI Assistant fails gracefully with a user-facing message if the LLM API is unreachable. Dropped WebSocket connections can reconnect mid-session. |

---

## 🧩 Assumptions & Constraints

- Requires an active internet connection — **no offline mode**.
- Movie features degrade gracefully if **TMDB** is unreachable.
- The AI Assistant is unavailable if the **LLM API** is down.
- Deployed to a **single region** for this version — no multi-region failover yet.
- Designed for **casual, small-group** sessions — not built or tested for large-scale concurrency.

---

## 📄 Related Documentation

- **Requirements Specification** — functional & non-functional requirements (this project's source doc)
- **System Design Document** — service boundaries, database schemas, and full API contracts

---

## 🚧 Status

This README reflects the current system design and requirements specification. Implementation details, setup instructions, and API contracts will be added as development progresses.
