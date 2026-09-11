# Movie Night API

API Gateway documentation for the Movie Night microservices platform.

> **⚠️ Auth note:** None of the downstream services (Movie-Service, Session-Service, Chat-Service) enforce authentication themselves — they trust an `X-User-ID` header on the request. `bearerAuth` is documented at the gateway level assuming the Gateway validates the JWT and injects that header, but this could not be confirmed since the Gateway's own code wasn't provided.

**Base URL:** `/`
**Version:** 1.0.0
**Default security:** Bearer JWT (`Authorization: Bearer <token>`) unless noted otherwise.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Profile](#profile)
3. [Movies](#movies)
4. [Watchlist](#watchlist)
5. [Watched History](#watched-history)
6. [Sessions](#sessions)
7. [AI Recommendations](#ai-recommendations)
8. [Known Bugs & Quirks](#known-bugs--quirks)

---

## Authentication

### `POST /api/auth/register`
Create a new user account. 🔓 No auth required. Rate-limited by `RegisterThrottle` (429 response shape not documented in code).

**Request body**
| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string (email) | ✅ | Must be unique |
| `password` | string | ✅ | Validated by Django's `validate_password` |
| `display_name` | string | ✅ | 3–50 chars |

**Responses**
| Status | Meaning |
|---|---|
| 201 | User created — `data` holds the serialized user |
| 400 | Validation error |

---

### `POST /api/auth/login`
Authenticate and receive JWT tokens. 🔓 No auth required. Rate-limited by `LoginThrottle`.

**Request body**
| Field | Type | Required |
|---|---|---|
| `email` | string (email) | ✅ |
| `password` | string | ✅ |

**Responses**
| Status | Meaning |
|---|---|
| 200 | `data` holds `{ access, refresh }` |
| 401 | Invalid credentials |

---

### `POST /api/auth/refresh`
Exchange a refresh token for a new access token. 🔓 No auth required.

**Request body**
| Field | Type | Required |
|---|---|---|
| `refresh` | string | ✅ |

**Responses**
| Status | Meaning |
|---|---|
| 200 | `data` holds `{ access }` |
| 401 | Invalid/expired refresh token |

---

### `POST /api/auth/logout`
Log out the current user by blacklisting their refresh token. 🔒 Auth required.

**Request body**
| Field | Type | Required |
|---|---|---|
| `refresh` | string | ✅ |

**Responses**
| Status | Meaning |
|---|---|
| 204 | Logged out successfully |
| 400 | Refresh token missing from body |
| 401 | Unauthorized |

---

## Profile

### `GET /api/profile`
Get the current user's profile.

**Responses:** `200` (UserProfile) · `401` Unauthorized

---

### `PATCH /api/profile`
Update the current user's profile.

> ⚠️ Only `display_name` is actively validated. If provided but unchanged, the view's internal 400 check never actually reaches the client — DRF's default `update()` ignores it and still returns 200 with unsaved serializer data.

**Request body**
| Field | Type | Required | Notes |
|---|---|---|---|
| `display_name` | string | ✅ | |
| `password` | string | ❌ | ⚠️ Not marked `write_only` — the (hashed) value is echoed back in the 200 response body |

**Responses:** `200` (ProfileUpdateResponse, includes `password`) · `400` display_name required · `401` Unauthorized

---

### `DELETE /api/profile`
Delete the current user's profile.

**Responses:** `204` Deleted · `401` Unauthorized

---

## Movies

### `GET /api/movies/search`
Search for movies.

**Query parameters**
| Param | Type | Required | Default | Notes |
|---|---|---|---|---|
| `query` | string | ✅ | — | Search text |
| `page` | integer | ❌ | 1 | Result page |

**Responses:** `200` raw pass-through of `MovieService.search_movie()` (shape not confirmed) · `400` missing query or no results · `401` Unauthorized

---

### `GET /api/movies/{movie_id}`
Get movie details (TMDB ID). Returns the locally cached `Movie` if it exists, otherwise fetches from TMDB, persists it, and returns it.

> ⚠️ No explicit 404 handling — if TMDB can't find the movie, the exception is unhandled and surfaces as a server error rather than a clean 404.

**Responses:** `200` (Movie) · `401` Unauthorized

---

### `GET /api/movies/{movie_id}/recommendations`
Get related-movie recommendations for a given TMDB ID.

**Responses:** `200` raw pass-through of `MovieService.get_movie_recommendations()` (shape not confirmed) · `400` no movies found · `401` Unauthorized

---

## Watchlist

### `GET /api/watchlist`
Get the current user's watchlist.

> ⚠️ `DjangoFilterBackend` is declared but `filterset_fields` is commented out, so **no query filtering is actually active** on this endpoint.

**Responses:** `200` array of `WatchlistItem` · `401` Unauthorized

---

### `POST /api/movies/{movie_id}/watchlist`
Add a movie to the watchlist. `movie_id` = the **Movie's own ID**.

**Responses:** `201` Added · `400` movie not found or already on watchlist · `401` Unauthorized

---

### `DELETE /api/movies/{movie_id}/watchlist`
Remove a movie from the watchlist.

> ⚠️ Inconsistent with POST: this filters `Watchlist.objects.filter(id=movie_id, ...)` — here `movie_id` actually refers to the **Watchlist row's own primary key**, not the movie's ID.

**Responses:** `200` Removed · `400` not in watchlist · `401` Unauthorized

---

## Watched History

### `GET /api/watched`
Get the current user's watched history.

**Query parameters**
| Param | Type | Required | Notes |
|---|---|---|---|
| `rating` | integer (1–10) | ❌ | This filter **is** active (`filterset_fields = ['rating']`) |

**Responses:** `200` array of `WatchedItem` · `401` Unauthorized

---

### `POST /api/movies/{movie_id}/watched`
Mark a movie as watched, with an optional rating.

> ℹ️ Side effect: also deletes any matching Watchlist entry for the same movie/user.
> ⚠️ `rating` isn't actually validated at the view level (no min/max or required check) — it's passed straight through to `get_or_create`.

**Request body**
| Field | Type | Required | Notes |
|---|---|---|---|
| `rating` | integer | ❌ | Declared 1–10, not enforced in code |

**Responses:** `201` Added · `400` movie not found or already marked watched · `401` Unauthorized

---

### `DELETE /api/movies/{movie_id}/watched`
Remove a movie from watched history.

> 🐛 **Likely bug:** this endpoint actually queries the `Watchlist` model (`Watchlist.objects.filter(id=movie_id, ...)`), not `Watched`. So it deletes a Watchlist row (by its own ID) despite the success message saying "removed from watched history."

**Responses:** `200` Removed (see bug above) · `400` not found · `401` Unauthorized

---

## Sessions

### `POST /api/sessions`
Create a new collaborative movie session. The caller (via `X-User-ID`) becomes the leader.

**Responses:** `201` Session created · `400` user_id missing · `401` Unauthorized

---

### `POST /api/sessions/join`
Join an existing session via its 6-digit code.

**Request body**
| Field | Type | Required |
|---|---|---|
| `code` | string, pattern `^[0-9]{6}$` | ✅ |

**Responses:** `201` Joined · `400` invalid code, session not joinable, or already a member · `401` Unauthorized

---

### `GET /api/sessions/{session_id}`
Get session details. Only returns sessions the caller participates in.

**Responses:** `200` (Session) · `401` Unauthorized · `404` not found / not a participant

---

### `POST /api/sessions/{session_id}/start`
Start a session.

**Requirements:** caller is a leader-role participant · session has ≥2 members · session status is `waiting` · at least one participant has a non-empty watchlist

**Responses:** `201` Started · `400` various validation failures (see requirements) · `401` Unauthorized

---

### `POST /api/sessions/{session_id}/end`
End a session and record the selected movie.

**Requirements:** caller is a leader-role participant · session status is `active`

**Request body**
| Field | Type | Required |
|---|---|---|
| `movie_tmdb_id` | integer | ✅ |

**Responses:** `200` Ended · `400` various validation failures · `401` Unauthorized

---

## AI Recommendations

### `POST /api/recommendations/start`
Start a conversational AI movie-recommendation session.

**Responses:** `201` `{ session_id, question }` (question shape comes from `QUESTIONS[0]`) · `400` user_id missing · `401` Unauthorized

---

### `POST /api/recommendations/{session_id}/answer`
Submit an answer to the session's current question.

**Request body**
| Field | Type | Required | Notes |
|---|---|---|---|
| `answer` | string | ✅ | Must exactly match one of the current question's `options` |

**Responses**
| Status | Meaning |
|---|---|
| 200 | `{ completed, question }` if more questions remain, or `{ completed: true, message }` when done |
| 400 | No active session, missing answer, or answer not a valid option |
| 401 | Unauthorized |

---

### `POST /api/recommendations/{session_id}/complete`
Complete the recommendation flow: ask the LLM for a movie title, then look it up via the Movie Service.

**Responses**
| Status | Meaning |
|---|---|
| 200 | `{ status: "completed", recommendation, movie }` |
| 400 | No active session, or not all questions answered yet |
| 401 | Unauthorized |
| 404 | `{ status: "failed", message }` — LLM's recommended title not found via TMDB search |
| 503 | `{ status: "failed", message }` — LLM call or movie lookup failed |

---

## Known Bugs & Quirks

A quick-reference list of the non-obvious behaviors called out above:

1. **Password leak in PATCH /api/profile** — `UpdateProfileSerializer` doesn't mark `password` `write_only`, so the hashed password comes back in the response.
2. **Silent no-op on unchanged display_name** — the PATCH view's 400 branch for "no change" never reaches the client due to DRF's default `update()` behavior.
3. **Watchlist DELETE / Watched DELETE use the Watchlist row ID, not the movie ID** — inconsistent with the corresponding POST endpoints, which use the Movie ID.
4. **`DELETE /api/movies/{movie_id}/watched` queries the wrong table** — it operates on `Watchlist`, not `Watched`, despite its name and success message.
5. **No validation on `rating`** in `POST /api/movies/{movie_id}/watched` — declared 1–10 in the schema, not enforced in code.
6. **`GET /api/movies/{movie_id}` has no clean 404** — a TMDB lookup miss surfaces as an unhandled server error.
7. **Watchlist filtering is dead code** — `filterset_fields` is commented out on `GET /api/watchlist`, so query params there do nothing (unlike `GET /api/watched`, where `rating` filtering does work).
