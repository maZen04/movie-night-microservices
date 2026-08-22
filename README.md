# 🎬 Movie Night

Movie Night is a group movie-selection application that lets people discover movies, manage a personal watchlist, and **vote together in real time** to pick what to watch — no more endless scrolling and "you pick" back-and-forth.

---

## 🚧 Build Status

This project is under active development. Not every service in the design below has code in this repo yet — see [Repository Structure](#-repository-structure) for what actually exists right now.

| Component            | Status                |
| -------------------- | --------------------- |
| User Service         | 🟢 Implemented        |
| Movie Service        | 🟢 Implemented        |
| Session Service      | 🟡 In Development     |
| API Gateway          | 🔵 Designed / Planned |
| AI Assistant Service | 🔵 Designed / Planned |

---

## ✨ Features

- **Movie Discovery** — Search movies via [The Movie Database (TMDB)](https://www.themoviedb.org/) API and view rich details (poster, overview, release year, rating).
- **Personal Watchlist** — Add, remove, and manage movies you plan to watch.
- **Watched History** — Mark movies as watched and rate them.
- **Real-Time Voting Sessions** — Create or join a session with a 6-digit code and vote synchronously with your group until a movie wins. _(🟡 in development)_
- **AI Assistant** — A short conversational Q&A that recommends a movie based on your mood and preferences. _(🔵 Planned)_

**Explicitly out of scope for this version:** push/email notifications, payments or subscriptions, in-app streaming/playback, social features beyond a session (friend lists, DMs, public profiles), asynchronous voting, and offline mode.

---

## 🧠 Core Concepts

| Term               | Definition                                                                                                                  |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| **Session**        | A temporary real-time group activity identified by a 6-digit code. Destroyed once it ends.                                  |
| **Leader**         | The user who creates the session. Only the Leader can start it. The session survives if the Leader disconnects mid-session. |
| **Member**         | Any user who joins a session (the Leader is also a Member).                                                                 |
| **Watchlist**      | A user's personal list of movies they intend to watch.                                                                      |
| **Pool**           | The deduplicated, shuffled combination of all participants' watchlists — the candidates voted on in a session.              |
| **Vote**           | A yes/no response from a member on the currently displayed movie.                                                           |
| **Selected Movie** | The final outcome of a session — either unanimous agreement, or the highest vote count with a random tiebreaker.            |
| **AI Assistant**   | An LLM-backed feature that asks a few questions and returns a single movie suggestion.                                      |

> 📌 **Leader** and **Member** are _roles scoped to a session_, not account types. Any authenticated user can be a Leader in one session and a Member in another — role lives on the session-participant relationship, not on the `User` entity.

---

## 🏗️ Architecture

Movie Night is built as a **microservices architecture** behind a single entry point. Clients — web or mobile — never talk to individual services directly; every request goes through the **API Gateway**, which validates the JWT and routes to the correct downstream service.

```
Client (Web / Mobile)
        │
        ▼
   API Gateway  ──►  Handles auth (JWT) + routing        🔵 Planned
        │
   ┌────┼────────────┬──────────────┐
   ▼    ▼             ▼              ▼
User   Movie       Session        AI Assistant
Svc    Svc          Svc              Svc
🟢     🟢            🟡              🔵
 │       │            │                │
Postgres Postgres,  Postgres,        LLM API
         Redis       Redis
         │
      TMDB API
```

| Service                  | Responsibility                                   | Data Store        | External Dependency | Status            |
| ------------------------ | ------------------------------------------------ | ----------------- | ------------------- | ----------------- |
| **User Service**         | Registration, login, JWT issuance, profile       | PostgreSQL        | —                   | 🟢 Implemented    |
| **Movie Service**        | TMDB search/details, watchlist, watched history  | PostgreSQL, Redis | TMDB API            | 🟢 Implemented    |
| **Session Service**      | Session lifecycle, real-time synchronized voting | PostgreSQL, Redis | —                   | 🟡 In development |
| **AI Assistant Service** | Conversational recommendation flow               | —                 | LLM API             | 🔵 Planned        |
| **API Gateway**          | Auth validation + request routing                | —                 | —                   | 🔵 Planned        |

- Clients **never** talk to individual services directly — everything goes through the **API Gateway**.
- Each service **owns its own data**; there is no shared database and no cross-service foreign keys. Any cross-service communication happens via internal API calls, not direct DB access.
- **Session state is ephemeral** and lives in Redis; if it's lost mid-session, the session cannot be recovered and must be restarted.

---

## 🗄️ Data Model

The relational schema spans 8 entities in PostgreSQL:

- **Users** — central identity entity. Holds no role or session-specific attributes. _(🟢 implemented — User Service)_
- **Movies / Genres / MovieGenres** — a local mirror of TMDB data (many-to-many with genres), ensuring previously-seen movies stay resolvable even if TMDB or the Redis cache is temporarily down. _(🟢 implemented — Movie Service)_
- **Watchlist** — many-to-one from Users → Movies. _(🟢 implemented — Movie Service)_
- **WatchedHistory** — many-to-one from Users → Movies, with an optional `rating`. _(🟢 implemented — Movie Service)_
- **Sessions** — the permanent record of a voting session (code, status, timestamps, and the final `movie_selected_id` once concluded). Live voting state itself stays in Redis for the duration of the session. _(🟡 in development — Session Service)_
- **SessionParticipants** — join table between Sessions and Users, storing each participant's `role` (leader/member) for that specific session. _(🟡 in development — Session Service)_

---

## ⚙️ How a Voting Session Works

> 🟡 The Session Service that implements this flow is currently in development; the flow below reflects the design, not yet a shipped feature.

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

## 🤖 AI Assistant

> 🔵 Planned. Documented here for design continuity; no code exists in this repo yet.

The AI Assistant Service will ask an authenticated user a short series of preference-related questions (mood, desired feeling), send those answers to an external LLM API, and return a single movie suggestion (title, poster, overview). If the LLM API is unreachable, the service should fail gracefully with a user-facing message instead of hanging or crashing the request.

---

## 🔐 Security

- Passwords are stored using a **secure one-way hash** — never in plaintext, never logged.
- Authentication uses **JWTs**, which expire after a defined period (e.g. 24 hours) and require re-authentication after expiry.
- All endpoints except registration/login **require a valid JWT**.
- Session codes are **rate-limited** per IP/user to prevent brute-force guessing of the 6-digit code.
- All client-server traffic uses **HTTPS/WSS** (encrypted transport) in production.

---

## 📈 Non-Functional Requirements

| Category         | Requirement                                                                                                                                                                                                                                                      |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Performance**  | WebSocket broadcasts (movie updates, votes, results) reach all participants within **1 second** under normal conditions. TMDB responses are cached for **24 hours**.                                                                                             |
| **Scalability**  | Session state lives in Redis (not in-memory), so any Session Service instance can serve any active session — required for horizontal scaling even with a single instance for the MVP.                                                                            |
| **Availability** | Cached movie data stays available if TMDB is down; only new/uncached lookups degrade. The AI Assistant fails gracefully with a user-facing message if the LLM API is unreachable. Dropped WebSocket connections can reconnect mid-session without restarting it. |

---

## 🧩 Assumptions & Constraints

- Requires an active internet connection — **no offline mode**.
- Movie features degrade gracefully if **TMDB** is unreachable.
- The AI Assistant is unavailable if the **LLM API** is down.
- Deployed to a **single region** for this version — no multi-region redundancy or failover.
- Real-time session functionality assumes a **persistent WebSocket connection**; unstable connections may see delayed updates or be treated as non-responsive within a voting round.
- Designed for **casual, small-group** sessions — not built or tested for large-scale concurrent sessions.

---

## 📂 Repository Structure

Reflects what's actually in this repo today — not every service below has a folder yet.

```
movie-night-microservices/
  User-Service/       🟢 Implemented — registration, login, JWT issuance, profile
  Movie-Service/       🟢 Implemented — TMDB search/details, watchlist, watched history
  Session-Service/     🟡 Planned — real-time synchronized voting (not yet in repo)
  AI-Assistant-Service/ 🔵 Planned — LLM-backed recommendation flow (not yet in repo)
  API-Gateway/          🔵 Planned — auth validation + routing (not yet in repo)
  docs/                Requirements & system design documentation
```

---

## 📄 Related Documentation

- **Requirements Specification** — functional & non-functional requirements ([`docs/`](./docs))
- **System Design Document** — service boundaries, database schemas, and full API contracts ([`docs/`](./docs))

---

## 🗺️ Status & Roadmap

This README reflects the current system design and requirements specification alongside real implementation progress. As Session Service, AI Assistant Service, and the API Gateway move from design to code, their sections above and the [Build Status](#-build-status) table will be updated, and their folders will be added to the repo.
