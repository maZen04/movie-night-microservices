def get_openapi_schema():
    # ============================================================
    # Reusable schemas
    # ============================================================

    schemas = {

        # Generic DRF `raise ValidationError({...})` body.
        # NOTE: the codebase raises ValidationError with different keys
        # in different places (e.g. {"query": [...]}, {"user_id": [...]}),
        # and in a couple of spots even passes a bare set/string instead
        # of a dict (e.g. `raise ValidationError({"There're no movies found."})`).
        # There is no single fixed shape, so this is intentionally open.
        "ValidationErrorResponse": {
            "type": "object",
            "description": (
                "Default DRF validation error body. Shape varies by "
                "endpoint/field — shown as an open object because the "
                "code raises ValidationError with different keys in "
                "different views."
            ),
            "additionalProperties": True,
            "example": {"field_name": ["Error message."]},
        },

        # Used only by LogoutView's manual 400 branch, which returns
        # `{"error": "..."}` directly (no "message" key).
        "SimpleErrorResponse": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                    "example": "Refresh token required",
                },
            },
        },

        # FIXED: confirmed against UserSerializer. `display_name` is
        # required (min_length=3, max_length=50, trimmed) — the original
        # doc was missing it entirely. `email` is validated unique.
        "RegisterRequest": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "Must be unique.",
                    "example": "mazen@example.com",
                },
                "password": {
                    "type": "string",
                    "format": "password",
                    "description": (
                        "Validated by Django's validate_password "
                        "(standard strength rules)."
                    ),
                    "example": "StrongPassword123!",
                },
                "display_name": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50,
                    "example": "Mazen",
                },
            },
            "required": [
                "email",
                "password",
                "display_name",
            ],
        },

        "LoginRequest": {
            "type": "object",
            "description": (
                "LoginView uses TokenObtainPairSerializer as-is; email "
                "is the registration identifier per UserSerializer, "
                "consistent with it being the USERNAME_FIELD."
            ),
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "example": "mazen@example.com",
                },
                "password": {
                    "type": "string",
                    "format": "password",
                    "example": "StrongPassword123!",
                },
            },
            "required": [
                "email",
                "password",
            ],
        },

        "RefreshRequest": {
            "type": "object",
            "properties": {
                "refresh": {
                    "type": "string",
                    "example": "your-refresh-token",
                },
            },
            "required": [
                "refresh",
            ],
        },

        # FIXED: LogoutView actually reads `refresh` from the request body
        # and blacklists it. The original doc had no requestBody at all.
        "LogoutRequest": {
            "type": "object",
            "properties": {
                "refresh": {
                    "type": "string",
                    "example": "your-refresh-token",
                },
            },
            "required": [
                "refresh",
            ],
        },

        # FIXED: confirmed against UpdateProfileSerializer. `id`, `email`,
        # `created_at`, `updated_at` are read_only there (so sending
        # `email` is silently ignored, not an error) — only
        # `display_name` and `password` are actually writable.
        # `display_name` is additionally required by the view logic
        # (ProfileView.perform_update).
        "ProfileUpdateRequest": {
            "type": "object",
            "description": (
                "Only `display_name` and `password` are writable here "
                "(email/id/created_at/updated_at are read_only on "
                "UpdateProfileSerializer). `display_name` is required "
                "by ProfileView.perform_update."
            ),
            "properties": {
                "display_name": {
                    "type": "string",
                    "example": "New Display Name",
                },
                "password": {
                    "type": "string",
                    "format": "password",
                    "description": (
                        "Optional. NOTE: unlike UserSerializer, "
                        "UpdateProfileSerializer does not mark this "
                        "write_only, so the stored password value is "
                        "also included in the 200 response body below "
                        "(see ProfileUpdateResponse) — appears to be "
                        "an oversight in the code, documented as-is."
                    ),
                },
            },
            "required": [
                "display_name",
            ],
        },

        "WatchHistoryRequest": {
            "type": "object",
            "description": (
                "NOTE: the view does not actually validate `rating` "
                "(no min/max check, no required check at the view level "
                "— it is passed straight to `Watched.objects.get_or_create` "
                "as `defaults={'rating': request.data.get('rating')}`). "
                "Constraints below reflect the field's declared shape only, "
                "not enforced behavior confirmed in code."
            ),
            "properties": {
                "rating": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "example": 8,
                },
            },
        },

        "JoinSessionRequest": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "pattern": "^[0-9]{6}$",
                    "example": "123456",
                },
            },
            "required": [
                "code",
            ],
        },

        # FIXED: EndSessionView actually requires `movie_tmdb_id` in the
        # body. The original doc had no requestBody at all for /end.
        "EndSessionRequest": {
            "type": "object",
            "properties": {
                "movie_tmdb_id": {
                    "type": "integer",
                    "example": 27205,
                },
            },
            "required": [
                "movie_tmdb_id",
            ],
        },

        "RecommendationAnswerRequest": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": (
                        "Must match one of the option strings for the "
                        "session's current question (validated against "
                        "`current_question['options']`)."
                    ),
                    "example": "I want something funny and light.",
                },
            },
            "required": [
                "answer",
            ],
        },

        "AuthResponse": {
            "type": "object",
            "properties": {
                "access": {
                    "type": "string",
                    "example": "eyJhbGciOiJIUzI1NiIs...",
                },
                "refresh": {
                    "type": "string",
                    "example": "eyJhbGciOiJIUzI1NiIs...",
                },
            },
        },

        # FIXED: RefreshTokenView uses TokenRefreshSerializer's default
        # validated_data, which normally only contains "access" (a new
        # "refresh" only appears if token rotation is enabled elsewhere,
        # which is not visible in the provided code).
        "RefreshResponseData": {
            "type": "object",
            "properties": {
                "access": {
                    "type": "string",
                    "example": "eyJhbGciOiJIUzI1NiIs...",
                },
            },
        },

        "MessageResponse": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "example": "Operation completed successfully.",
                },
            },
        },

        # FIXED: RegisterView/LoginView/RefreshTokenView all return via
        # `success_response(data=..., message=..., status=...)`. The
        # implementation of `success_response` itself is not in the
        # provided code, so this wrapper shape is inferred from the call
        # signature, not confirmed against its source.
        "WrappedResponse": {
            "type": "object",
            "description": (
                "Inferred wrapper shape used by common.response."
                "success_response(data=..., message=..., status=...). "
                "The helper's implementation was not provided, so this "
                "is an assumption, not a confirmed shape."
            ),
            "properties": {
                "data": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "message": {
                    "type": "string",
                },
            },
        },

        # FIXED: confirmed against UserSerializer's `fields`. `password`
        # is write_only there (extra_kwargs), so it never appears here.
        # Returned by: register (wrapped), GET /profile.
        "UserProfile": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "example": 1,
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "example": "mazen@example.com",
                },
                "display_name": {
                    "type": "string",
                    "example": "Mazen",
                },
                "created_at": {
                    "type": "string",
                    "format": "date-time",
                },
                "updated_at": {
                    "type": "string",
                    "format": "date-time",
                },
            },
        },

        # FIXED: PATCH /profile uses UpdateProfileSerializer, which
        # (unlike UserSerializer) does not mark `password` write_only,
        # so it comes back in the response body as the stored hash.
        "ProfileUpdateResponse": {
            "type": "object",
            "description": (
                "Same as UserProfile, but also includes `password` "
                "(the hashed value) since UpdateProfileSerializer "
                "doesn't set write_only on it. Likely unintentional, "
                "documented as the code actually behaves."
            ),
            "properties": {
                "id": {
                    "type": "integer",
                    "example": 1,
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "example": "mazen@example.com",
                },
                "display_name": {
                    "type": "string",
                    "example": "Mazen",
                },
                "password": {
                    "type": "string",
                    "description": "Hashed password value.",
                },
                "created_at": {
                    "type": "string",
                    "format": "date-time",
                },
                "updated_at": {
                    "type": "string",
                    "format": "date-time",
                },
            },
        },

        # FIXED: confirmed against MovieSerializer's `fields`.
        # `genres` is a SerializerMethodField that returns
        # GenreSerializer(many=True).data, and GenreSerializer only
        # exposes `name` — so each genre entry is just {"name": "..."},
        # not a full genre object with an id.
        "Movie": {
            "type": "object",
            "description": "Full movie details, returned by GET /api/movies/{movie_id}.",
            "properties": {
                "id": {
                    "type": "integer",
                    "example": 1,
                },
                "tmdb_id": {
                    "type": "integer",
                    "example": 27205,
                },
                "title": {
                    "type": "string",
                    "example": "Inception",
                },
                "overview": {
                    "type": "string",
                },
                "poster_path": {
                    "type": "string",
                    "nullable": True,
                },
                "release_date": {
                    "type": "string",
                    "format": "date",
                    "nullable": True,
                },
                "runtime": {
                    "type": "integer",
                    "nullable": True,
                },
                "original_language": {
                    "type": "string",
                    "example": "en",
                },
                "vote_average": {
                    "type": "number",
                    "example": 8.36,
                },
                "genres": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "example": "Science Fiction",
                            },
                        },
                    },
                },
            },
        },

        # FIXED: confirmed against MovieCard — the nested `movie` shown
        # inside watchlist/watched entries is a smaller shape than the
        # full Movie above (no tmdb_id, runtime, original_language, or
        # genres).
        "MovieCard": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "example": 1,
                },
                "title": {
                    "type": "string",
                    "example": "Inception",
                },
                "overview": {
                    "type": "string",
                },
                "poster_path": {
                    "type": "string",
                    "nullable": True,
                },
                "release_date": {
                    "type": "string",
                    "format": "date",
                    "nullable": True,
                },
                "vote_average": {
                    "type": "number",
                    "example": 8.36,
                },
            },
        },

        # FIXED: confirmed against WatchlistSerializer's `fields`.
        "WatchlistItem": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": (
                        "Stored as-is from the X-User-ID header; not "
                        "necessarily numeric."
                    ),
                },
                "movie": {
                    "$ref": "#/components/schemas/MovieCard",
                },
                "added_at": {
                    "type": "string",
                    "format": "date-time",
                },
            },
        },

        # FIXED: confirmed against WatchedSerializer's `fields`.
        "WatchedItem": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                },
                "movie": {
                    "$ref": "#/components/schemas/MovieCard",
                },
                "watched_at": {
                    "type": "string",
                    "format": "date-time",
                },
                "rating": {
                    "type": "integer",
                    "nullable": True,
                    "example": 8,
                },
            },
        },

        # NOTE: SessionSerializer uses `fields = "__all__"`, and the
        # Session model itself is not in the provided code, so the
        # complete field list can't be confirmed. `created_at`,
        # `started_at`, `ended_at` are included below because they're
        # explicitly named on the same model by SessionDetailsSerializer
        # (a serializer that exists in serializers.py but isn't used by
        # any of the given views). Any field that would store the movie
        # picked in EndSessionView (movie_tmdb_id) is real but its exact
        # column name is unconfirmed — kept out of `properties` and
        # covered by `additionalProperties` instead of guessing a name.
        "Session": {
            "type": "object",
            "description": (
                "Movie Night collaborative session. Fields shown are "
                "confirmed or strongly implied; `additionalProperties` "
                "covers the rest of `fields = \"__all__\"` since the "
                "Session model wasn't provided."
            ),
            "properties": {
                "id": {
                    "type": "integer",
                    "example": 15,
                },
                "code": {
                    "type": "string",
                    "example": "123456",
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "waiting",
                        "active",
                        "ended",
                    ],
                    "example": "waiting",
                },
                "created_at": {
                    "type": "string",
                    "format": "date-time",
                },
                "started_at": {
                    "type": "string",
                    "format": "date-time",
                    "nullable": True,
                },
                "ended_at": {
                    "type": "string",
                    "format": "date-time",
                    "nullable": True,
                },
            },
            "additionalProperties": True,
        },

        # FIXED: StartSessionView/EndSessionView don't return the Session
        # object directly — they wrap it as {"message": ..., "data": ...}.
        "SessionActionResponse": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "example": "Session started successfully.",
                },
                "data": {
                    "$ref": "#/components/schemas/Session",
                },
            },
        },

        # FIXED: AnswerRecommendationView returns one of two shapes
        # depending on whether more questions remain.
        "AnswerRecommendationResponse": {
            "type": "object",
            "properties": {
                "completed": {
                    "type": "boolean",
                },
                "question": {
                    "type": "object",
                    "description": (
                        "Present when completed=false. Shape comes from "
                        "the QUESTIONS list, which is not in the provided "
                        "code."
                    ),
                    "additionalProperties": True,
                },
                "message": {
                    "type": "string",
                    "description": "Present when completed=true.",
                    "example": "All questions answered.",
                },
            },
        },

        # FIXED: StartRecommendationView's real success body.
        "StartRecommendationResponse": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "integer",
                    "example": 1,
                },
                "question": {
                    "type": "object",
                    "description": (
                        "Shape comes from QUESTIONS[0], which is not in "
                        "the provided code."
                    ),
                    "additionalProperties": True,
                },
            },
        },

        # FIXED: CompleteRecommendationView's real success/failure bodies.
        "CompleteRecommendationResponse": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "example": "completed",
                },
                "recommendation": {
                    "type": "object",
                    "description": (
                        "Raw output of LLMService.recommend_movie(); "
                        "known to contain at least 'movie_title' since "
                        "the view reads recommendation['movie_title']. "
                        "Full shape unverified (LLMService not provided)."
                    ),
                    "additionalProperties": True,
                },
                "movie": {
                    "type": "object",
                    "description": (
                        "Output of MovieService.get_movie_details(); not "
                        "provided in code."
                    ),
                    "additionalProperties": True,
                },
            },
        },

        "CompleteRecommendationFailedResponse": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "example": "failed",
                },
                "message": {
                    "type": "string",
                    "example": "Could not find the recommended movie.",
                },
            },
        },
    }

    # ============================================================
    # Helper functions
    # ============================================================

    def json_request_body(schema_name, description=None):
        body = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": f"#/components/schemas/{schema_name}"
                    }
                }
            },
        }

        if description:
            body["description"] = description

        return body

    def json_response(schema_name, description):
        return {
            "description": description,
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": f"#/components/schemas/{schema_name}"
                    }
                }
            },
        }

    def empty_response(description):
        return {
            "description": description
        }

    def validation_error_response(description):
        return {
            "description": description,
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/ValidationErrorResponse"
                    }
                }
            },
        }

    def simple_error_response(description):
        return {
            "description": description,
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/SimpleErrorResponse"
                    }
                }
            },
        }

    def path_parameter(name, parameter_type="integer", example=None, description=None):
        parameter = {
            "name": name,
            "in": "path",
            "required": True,
            "schema": {
                "type": parameter_type,
            },
        }

        if example is not None:
            parameter["example"] = example

        if description is not None:
            parameter["description"] = description

        return parameter

    # ============================================================
    # OpenAPI document
    # ============================================================

    return {
        "openapi": "3.0.3",

        "info": {
            "title": "Movie Night API",
            "description": (
                "API Gateway documentation for the "
                "Movie Night microservices platform.\n\n"
                "NOTE: none of the downstream services (Movie-Service, "
                "Session-Service, Chat-Service) enforce authentication "
                "themselves — they trust an `X-User-ID` header on the "
                "request. `bearerAuth` below is documented at the "
                "gateway level assuming the Gateway validates the JWT "
                "and injects that header; this could not be confirmed "
                "from the provided code, since the Gateway itself isn't "
                "included."
            ),
            "version": "1.0.0",
        },

        "servers": [
            {
                "url": "/",
                "description": "Movie Night API Gateway",
            }
        ],

        # ========================================================
        # Components
        # ========================================================

        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            },

            "schemas": schemas,
        },

        # ========================================================
        # Global security
        # ========================================================

        "security": [
            {
                "bearerAuth": []
            }
        ],

        # ========================================================
        # Paths
        # ========================================================

        "paths": {

            # ====================================================
            # AUTHENTICATION
            # ====================================================

            "/api/auth/register": {
                "post": {
                    "tags": [
                        "Authentication"
                    ],

                    "summary": "Register a new user",

                    "description": (
                        "Create a new user account. Subject to "
                        "RegisterThrottle (no explicit 429 documented — "
                        "throttle response body/behavior not shown in "
                        "the provided code)."
                    ),

                    "security": [],

                    "requestBody": json_request_body(
                        "RegisterRequest",
                        "User registration data.",
                    ),

                    "responses": {
                        # FIXED: wrapped via success_response(), not the
                        # bare UserProfile object.
                        "201": json_response(
                            "WrappedResponse",
                            "User created successfully. `data` holds "
                            "the serialized user (UserProfile shape, "
                            "via UserSerializer).",
                        ),

                        "400": validation_error_response(
                            "Invalid registration data."
                        ),
                    },
                }
            },

            "/api/auth/login": {
                "post": {
                    "tags": [
                        "Authentication"
                    ],

                    "summary": "Login",

                    "description": (
                        "Authenticate a user and return JWT tokens. "
                        "Subject to LoginThrottle."
                    ),

                    "security": [],

                    "requestBody": json_request_body(
                        "LoginRequest",
                        "User login credentials.",
                    ),

                    "responses": {
                        # FIXED: wrapped via success_response().
                        "200": json_response(
                            "WrappedResponse",
                            "Login successful. `data` holds "
                            "{access, refresh} (AuthResponse).",
                        ),

                        "401": validation_error_response(
                            "Invalid credentials."
                        ),
                    },
                }
            },

            "/api/auth/refresh": {
                "post": {
                    "tags": [
                        "Authentication"
                    ],

                    "summary": "Refresh access token",

                    "description": (
                        "Generate a new access token using "
                        "a valid refresh token."
                    ),

                    "security": [],

                    "requestBody": json_request_body(
                        "RefreshRequest",
                        "JWT refresh token.",
                    ),

                    "responses": {
                        # FIXED: wrapped via success_response(); data is
                        # TokenRefreshSerializer's default output
                        # ({"access": ...} only).
                        "200": json_response(
                            "WrappedResponse",
                            "New access token generated. `data` holds "
                            "{access} (RefreshResponseData).",
                        ),

                        "401": validation_error_response(
                            "Invalid or expired refresh token "
                            "(raised as InvalidToken)."
                        ),
                    },
                }
            },

            "/api/auth/logout": {
                "post": {
                    "tags": [
                        "Authentication"
                    ],

                    "summary": "Logout",

                    "description": (
                        "Log out the currently authenticated user by "
                        "blacklisting their refresh token."
                    ),

                    # FIXED: LogoutView requires `refresh` in the body —
                    # the original doc had no requestBody at all.
                    "requestBody": json_request_body(
                        "LogoutRequest",
                        "Refresh token to blacklist.",
                    ),

                    "responses": {
                        "204": empty_response(
                            "Logged out successfully."
                        ),

                        # FIXED: two distinct 400 cases actually exist —
                        # missing refresh (`{"error": ...}`) and an
                        # invalid/already-blacklisted refresh
                        # (raised as ValidationError -> `{"refresh": [...]}`).
                        "400": simple_error_response(
                            "Refresh token missing from the request body."
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                }
            },

            # ====================================================
            # PROFILE
            # ====================================================

            "/api/profile": {

                "get": {
                    "tags": [
                        "Profile"
                    ],

                    "summary": "Get current user profile",

                    "responses": {
                        "200": json_response(
                            "UserProfile",
                            "Current user profile.",
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                },

                "patch": {
                    "tags": [
                        "Profile"
                    ],

                    "summary": "Update current user profile",

                    "description": (
                        "NOTE: only `display_name` is actively validated "
                        "by ProfileView.perform_update. If `display_name` "
                        "is provided but unchanged from the current "
                        "value, the view's own 400 branch "
                        "(`return Response(...)` inside perform_update) "
                        "is never actually sent to the client — DRF's "
                        "default update() ignores perform_update's "
                        "return value and still responds 200 with the "
                        "serializer data (unsaved)."
                    ),

                    "requestBody": json_request_body(
                        "ProfileUpdateRequest",
                        "Profile fields to update.",
                    ),

                    "responses": {
                        "200": json_response(
                            "ProfileUpdateResponse",
                            "Profile updated successfully.",
                        ),

                        "400": validation_error_response(
                            "display_name is required."
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                },

                "delete": {
                    "tags": [
                        "Profile"
                    ],

                    "summary": "Delete current user profile",

                    "responses": {
                        "204": empty_response(
                            "Profile deleted successfully."
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                },
            },

            # ====================================================
            # MOVIES
            # ====================================================

            "/api/movies/search": {
                "get": {
                    "tags": [
                        "Movies"
                    ],

                    "summary": "Search movies",

                    "parameters": [
                        {
                            "name": "query",
                            "in": "query",
                            "required": True,
                            "description": "Movie search query.",
                            "schema": {
                                "type": "string",
                            },
                            "example": "Inception",
                        },
                        {
                            "name": "page",
                            "in": "query",
                            "required": False,
                            "description": "Result page number.",
                            "schema": {
                                "type": "integer",
                                "minimum": 1,
                                "default": 1,
                            },
                            "example": 1,
                        },
                    ],

                    "responses": {
                        "200": {
                            "description": (
                                "Movie search results. Raw pass-through "
                                "of MovieService.search_movie(); exact "
                                "shape not in provided code."
                            ),
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "additionalProperties": True,
                                    }
                                }
                            },
                        },

                        # FIXED: both "query missing" and "no results
                        # found" raise ValidationError -> 400. There is
                        # no dedicated "query required" vs other case
                        # split at the HTTP-status level.
                        "400": validation_error_response(
                            "Query is missing, or no movies were found "
                            "for the given query."
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                }
            },

            "/api/movies/{movie_id}": {
                "get": {
                    "tags": [
                        "Movies"
                    ],

                    "summary": "Get movie details",

                    "description": (
                        "Returns the locally cached Movie if it exists; "
                        "otherwise fetches it from TMDBService, persists "
                        "it, and returns it.\n\n"
                        "NOTE: there is no explicit 404 handling in "
                        "MovieDetailView — if the TMDB call fails to "
                        "find the movie, the resulting exception is not "
                        "caught in the provided code, so it would "
                        "surface as an unhandled server error rather "
                        "than a clean 404."
                    ),

                    "parameters": [
                        path_parameter(
                            "movie_id",
                            "integer",
                            27205,
                            "TMDB movie ID.",
                        )
                    ],

                    "responses": {
                        "200": json_response(
                            "Movie",
                            "Movie details.",
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                }
            },

            "/api/movies/{movie_id}/recommendations": {
                "get": {
                    "tags": [
                        "Movies"
                    ],

                    "summary": "Get movie recommendations",

                    "parameters": [
                        # FIXED: urls.py declares this as <str:movie_id>,
                        # not <int:movie_id>.
                        path_parameter(
                            "movie_id",
                            "string",
                            "27205",
                        )
                    ],

                    "responses": {
                        "200": {
                            "description": (
                                "Recommended movies. Raw pass-through of "
                                "MovieService.get_movie_recommendations(); "
                                "exact shape not in provided code."
                            ),
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "additionalProperties": True,
                                    }
                                }
                            },
                        },

                        # FIXED: empty results raise ValidationError -> 400,
                        # not 404.
                        "400": validation_error_response(
                            "No movies found for this ID."
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                }
            },

            # ====================================================
            # WATCHLIST
            # ====================================================

            "/api/watchlist": {
                "get": {
                    "tags": [
                        "Watchlist"
                    ],

                    "summary": "Get current user's watchlist",

                    "description": (
                        "NOTE: WatchlistView declares DjangoFilterBackend "
                        "but `filterset_fields` is commented out in the "
                        "provided code, so no query-parameter filtering "
                        "is actually active on this endpoint."
                    ),

                    "responses": {
                        "200": {
                            "description": "Current user's watchlist.",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        # FIXED: WatchlistSerializer output,
                                        # not a plain Movie.
                                        "items": {
                                            "$ref": "#/components/schemas/WatchlistItem"
                                        },
                                    }
                                }
                            },
                        },

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                }
            },

            "/api/movies/{movie_id}/watchlist": {
                "post": {
                    "tags": [
                        "Watchlist"
                    ],

                    "summary": "Add movie to watchlist",

                    "description": (
                        "Add the specified movie to the "
                        "current user's watchlist. `movie_id` here is "
                        "the Movie's own ID (Movie.objects.filter(id=...))."
                    ),

                    "parameters": [
                        path_parameter(
                            "movie_id",
                            "integer",
                            27205,
                        )
                    ],

                    "responses": {
                        "201": json_response(
                            "MessageResponse",
                            "Movie added to watchlist.",
                        ),

                        # FIXED: "movie not found" and "already in
                        # watchlist" are both raised as ValidationError
                        # -> 400, not 404.
                        "400": validation_error_response(
                            "Movie not found, or already in the "
                            "user's watchlist."
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                },

                "delete": {
                    "tags": [
                        "Watchlist"
                    ],

                    "summary": "Remove movie from watchlist",

                    "description": (
                        "NOTE: unlike POST, this endpoint filters "
                        "`Watchlist.objects.filter(id=movie_id, ...)` — "
                        "i.e. `movie_id` here actually refers to the "
                        "Watchlist row's own primary key, not the "
                        "movie's ID. This is an inconsistency in the "
                        "code, not a documentation choice."
                    ),

                    "parameters": [
                        path_parameter(
                            "movie_id",
                            "integer",
                            1,
                            "Watchlist entry ID (not the movie's ID — "
                            "see description).",
                        )
                    ],

                    "responses": {
                        # FIXED: no explicit status is set in the view,
                        # so DRF defaults to 200, not 204. The body also
                        # contains a message, so it isn't empty.
                        "200": json_response(
                            "MessageResponse",
                            "Movie removed from watchlist.",
                        ),

                        # FIXED: "not in watchlist" is ValidationError -> 400.
                        "400": validation_error_response(
                            "Movie is not in the watchlist."
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                },
            },

            # ====================================================
            # WATCHED
            # ====================================================

            "/api/watched": {
                "get": {
                    "tags": [
                        "Watched"
                    ],

                    "summary": "Get watched history",

                    "parameters": [
                        {
                            "name": "rating",
                            "in": "query",
                            "required": False,
                            "description": (
                                "Filter watched movies by rating. "
                                "(This one IS active — WatchedHistoryView "
                                "declares filterset_fields = ['rating'].)"
                            ),
                            "schema": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                            },
                            "example": 8,
                        }
                    ],

                    "responses": {
                        "200": {
                            "description": "Watched movie history.",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        # FIXED: WatchedSerializer output,
                                        # not a plain Movie.
                                        "items": {
                                            "$ref": "#/components/schemas/WatchedItem"
                                        },
                                    }
                                }
                            },
                        },

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                }
            },

            "/api/movies/{movie_id}/watched": {
                "post": {
                    "tags": [
                        "Watched"
                    ],

                    "summary": "Add movie to watched history",

                    "description": (
                        "Mark a movie as watched with an optional "
                        "rating.\n\n"
                        "NOTE: as a side effect, this also deletes any "
                        "matching Watchlist entry for the same "
                        "movie/user — not documented anywhere else in "
                        "the API surface, but it is real behavior in "
                        "WatchedEditView.post."
                    ),

                    "parameters": [
                        path_parameter(
                            "movie_id",
                            "integer",
                            27205,
                        )
                    ],

                    "requestBody": json_request_body(
                        "WatchHistoryRequest",
                        "Optional rating for the watched movie.",
                    ),

                    "responses": {
                        "201": json_response(
                            "MessageResponse",
                            "Movie added to watched history.",
                        ),

                        # FIXED: "movie not found" and "already watched"
                        # are both ValidationError -> 400, not 404.
                        # The previously documented "invalid rating"
                        # case does not exist — rating is not validated
                        # at the view level.
                        "400": validation_error_response(
                            "Movie not found, or already marked as "
                            "watched by this user."
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                },

                "delete": {
                    "tags": [
                        "Watched"
                    ],

                    "summary": "Remove movie from watched history",

                    "description": (
                        "NOTE: this appears to be a bug in the provided "
                        "code — WatchedEditView.delete actually queries "
                        "the Watchlist model (`Watchlist.objects.filter"
                        "(id=movie_id, user_id=user_id)`), not Watched. "
                        "So calling this endpoint deletes a Watchlist "
                        "row (by its own ID, same caveat as the "
                        "watchlist DELETE endpoint), not a Watched row, "
                        "despite the success message saying 'removed "
                        "from watched history'. Documented here as the "
                        "code actually behaves."
                    ),

                    "parameters": [
                        path_parameter(
                            "movie_id",
                            "integer",
                            1,
                            "Watchlist entry ID (see description — "
                            "this endpoint queries Watchlist, not "
                            "Watched).",
                        )
                    ],

                    "responses": {
                        # FIXED: no explicit status -> defaults to 200.
                        "200": json_response(
                            "MessageResponse",
                            "Row removed (see description for the "
                            "Watchlist/Watched mismatch).",
                        ),

                        "400": validation_error_response(
                            "Matching row not found."
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                },
            },

            # ====================================================
            # SESSIONS
            # ====================================================

            "/api/sessions": {
                "post": {
                    "tags": [
                        "Sessions"
                    ],

                    "summary": "Create a movie session",

                    "description": (
                        "Create a new collaborative movie session. "
                        "The authenticated user (via X-User-ID) becomes "
                        "the leader."
                    ),

                    "responses": {
                        "201": json_response(
                            "Session",
                            "Session created successfully.",
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),

                        "400": validation_error_response(
                            "user_id missing (X-User-ID not resolved)."
                        ),
                    },
                }
            },

            "/api/sessions/join": {
                "post": {
                    "tags": [
                        "Sessions"
                    ],

                    "summary": "Join a movie session",

                    "description": (
                        "Join an existing session using its "
                        "6-digit session code."
                    ),

                    "requestBody": json_request_body(
                        "JoinSessionRequest",
                        "6-digit session code.",
                    ),

                    "responses": {
                        # FIXED: actual status is 201, and the body is
                        # just a message, not the full Session object.
                        "201": json_response(
                            "MessageResponse",
                            "Joined session successfully.",
                        ),

                        # FIXED: covers all of: invalid code, session
                        # not in WAITING status, already joined.
                        "400": validation_error_response(
                            "Invalid code, session not joinable "
                            "(not waiting), or already a member."
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                }
            },

            "/api/sessions/{session_id}": {
                "get": {
                    "tags": [
                        "Sessions"
                    ],

                    "summary": "Get session details",

                    "description": (
                        "Only returns sessions the current user "
                        "participates in (queryset filtered by "
                        "participants__user_id)."
                    ),

                    "parameters": [
                        path_parameter(
                            "session_id",
                            "integer",
                            15,
                        )
                    ],

                    "responses": {
                        "200": json_response(
                            "Session",
                            "Session details.",
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),

                        # This one IS a genuine 404 — SessionDetailView
                        # is a plain generics.RetrieveAPIView, so
                        # get_object() raises Http404 normally.
                        "404": empty_response(
                            "Session not found, or the user is not a "
                            "participant."
                        ),
                    },
                }
            },

            "/api/sessions/{session_id}/start": {
                "post": {
                    "tags": [
                        "Sessions"
                    ],

                    "summary": "Start movie session",

                    "description": (
                        "Start the session. Requires: the caller is a "
                        "leader-role participant, at least 2 members, "
                        "the session is currently WAITING, and at least "
                        "one participant has a non-empty watchlist."
                    ),

                    "parameters": [
                        path_parameter(
                            "session_id",
                            "integer",
                            15,
                        )
                    ],

                    "responses": {
                        # FIXED: real status is 201, and the body wraps
                        # the Session under "data" alongside "message".
                        "201": json_response(
                            "SessionActionResponse",
                            "Session started successfully.",
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),

                        # FIXED: every failure case here (session not
                        # found, not a member, not a leader, fewer than
                        # 2 members, already started, no movies in any
                        # watchlist) is raised as ValidationError -> 400.
                        # There is no 403 or 404 in this view.
                        "400": validation_error_response(
                            "Session not found, caller is not a member, "
                            "caller is not the leader, fewer than 2 "
                            "members, session already started, or no "
                            "participant has any movies in their "
                            "watchlist."
                        ),
                    },
                }
            },

            "/api/sessions/{session_id}/end": {
                "post": {
                    "tags": [
                        "Sessions"
                    ],

                    "summary": "End movie session",

                    "description": (
                        "End the session and record the selected movie. "
                        "Requires: the caller is a leader-role "
                        "participant and the session is currently ACTIVE."
                    ),

                    "parameters": [
                        path_parameter(
                            "session_id",
                            "integer",
                            15,
                        )
                    ],

                    # FIXED: EndSessionView reads movie_tmdb_id from the
                    # body and 400s if it's missing — not documented at
                    # all in the original.
                    "requestBody": json_request_body(
                        "EndSessionRequest",
                        "ID of the movie the group selected.",
                    ),

                    "responses": {
                        # FIXED: no explicit status -> defaults to 200,
                        # not the previously documented 200-with-bare-
                        # Session (it's wrapped under "data").
                        "200": json_response(
                            "SessionActionResponse",
                            "Session ended successfully.",
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),

                        # FIXED: session not found, not a member, not a
                        # leader, session not ACTIVE, and missing
                        # movie_tmdb_id are all ValidationError -> 400.
                        # There is no 403 or 404 in this view.
                        "400": validation_error_response(
                            "Session not found, caller is not a member, "
                            "caller is not the leader, session is not "
                            "active, or movie_tmdb_id missing."
                        ),
                    },
                }
            },

            # ====================================================
            # AI RECOMMENDATIONS
            # ====================================================

            "/api/recommendations/start": {
                "post": {
                    "tags": [
                        "AI Recommendations"
                    ],

                    "summary": "Start AI movie recommendation",

                    "description": (
                        "Start a conversational AI movie "
                        "recommendation session."
                    ),

                    "responses": {
                        # FIXED: real status is 201, body is
                        # {session_id, question}, not a generic
                        # RecommendationResponse.
                        "201": json_response(
                            "StartRecommendationResponse",
                            "Recommendation session started.",
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),

                        "400": validation_error_response(
                            "user_id missing (X-User-ID not resolved)."
                        ),

                        # NOTE: removed the previously documented 500 —
                        # this view has no try/except, so there is no
                        # purpose-built error response here (any
                        # exception would just be an unhandled server
                        # error, same as it would be for any endpoint).
                    },
                }
            },

            "/api/recommendations/{session_id}/answer": {
                "post": {
                    "tags": [
                        "AI Recommendations"
                    ],

                    "summary": "Answer recommendation question",

                    "description": (
                        "Submit an answer to the current AI "
                        "recommendation question."
                    ),

                    "parameters": [
                        path_parameter(
                            "session_id",
                            "integer",
                            1,
                        )
                    ],

                    "requestBody": json_request_body(
                        "RecommendationAnswerRequest",
                        "Answer to the current recommendation question.",
                    ),

                    "responses": {
                        # FIXED: real body has `completed` plus either
                        # `question` or `message`, not a generic
                        # RecommendationResponse.
                        "200": json_response(
                            "AnswerRecommendationResponse",
                            "Answer processed successfully.",
                        ),

                        # FIXED: "session not found" (active session with
                        # this id/user not found), missing answer, and
                        # invalid answer are all ValidationError -> 400.
                        # There is no 404 in this view.
                        "400": validation_error_response(
                            "No active recommendation session for this "
                            "id/user, answer missing, or answer not one "
                            "of the current question's options."
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),
                    },
                }
            },

            "/api/recommendations/{session_id}/complete": {
                "post": {
                    "tags": [
                        "AI Recommendations"
                    ],

                    "summary": "Complete AI recommendation",

                    "description": (
                        "Complete the recommendation conversation, ask "
                        "the LLM for a movie title, then look it up via "
                        "the Movie Service."
                    ),

                    "parameters": [
                        path_parameter(
                            "session_id",
                            "integer",
                            1,
                        )
                    ],

                    "responses": {
                        "200": json_response(
                            "CompleteRecommendationResponse",
                            "Movie recommendation generated.",
                        ),

                        # FIXED: "session not found" and "not all
                        # questions answered" are both ValidationError
                        # -> 400.
                        "400": validation_error_response(
                            "No active recommendation session for this "
                            "id/user, or not all questions have been "
                            "answered yet."
                        ),

                        "401": validation_error_response(
                            "Unauthorized."
                        ),

                        # FIXED: this 404 is real, but means "TMDB
                        # search for the LLM's recommended title "
                        # returned no results" — not "session not
                        # found" as the original doc implied.
                        "404": json_response(
                            "CompleteRecommendationFailedResponse",
                            "The movie title recommended by the LLM "
                            "could not be found via TMDB search.",
                        ),

                        # FIXED: any other exception during the LLM/
                        # movie-lookup flow returns 503, not 500.
                        "503": json_response(
                            "CompleteRecommendationFailedResponse",
                            "LLM call or movie lookup failed "
                            "(caught generic exception).",
                        ),
                    },
                }
            },
        },
    }