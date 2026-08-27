import redis.asyncio as redis
from django.conf import settings

class VoteStorageService:

    def __init__(self):
        self.redis = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
    
    def _movies_key(self, session_id, user_id):
        return f"session:{session_id}:user:{user_id}:movies"

    def _index_key(self, session_id, user_id):
        return f"session:{session_id}:user:{user_id}:index"

    def _likes_key(self, session_id):
        return f"session:{session_id}:movies:likes"
        
    async def initialize_session(self, session_id, users_movies):
        """
        users_movies:
        {
            1: [10, 20, 30],
            2: [30, 10, 20]
        }
        """

        for user_id, movies in users_movies.items():
            await self.set_movies_for_user(
                session_id,
                user_id,
                movies,
            )

    async def set_movies_for_user(self, session_id, user_id, movies):
        movies_key = self._movies_key(session_id, user_id)
        index_key = self._index_key(session_id, user_id)

        if movies:
            await self.redis.rpush(movies_key, *movies)

        await self.redis.set(index_key, 0)
    
    async def get_movies_for_user(self, session_id, user_id):
        return await self.redis.lrange(
            self._movies_key(session_id, user_id),
            0,
            -1,
        )

    async def get_current_movie(self, session_id, user_id):
        movies = await self.get_movies_for_user(
            session_id,
            user_id,
        )

        index = await self.get_user_index(
            session_id,
            user_id,
        )

        if index >= len(movies):
            return None

        return movies[index]

    async def get_user_index(self, session_id, user_id):
        index = await self.redis.get(
            self._index_key(session_id, user_id)
        )

        return int(index or 0)
    
    async def increment_index(self, session_id, user_id):
        return await self.redis.incr(
            self._index_key(session_id, user_id)
        )

    async def get_movie_likes(self, session_id, movie_id):
        likes = await self.redis.hget(
            self._likes_key(session_id),
            movie_id,
        )

        return int(likes or 0)

    async def like_movie(self, session_id, movie_id):
        return await self.redis.hincrby(
            self._likes_key(session_id),
            movie_id,
            1,
        )

    async def is_user_finished(self, session_id, user_id):
        movies = await self.get_movies_for_user(
            session_id,
            user_id,
        )

        index = await self.get_user_index(
            session_id,
            user_id,
        )

        return index >= len(movies)
    
    async def all_users_finished(self, session_id, user_ids):
        for user_id in user_ids:
            finished = await self.is_user_finished(
                session_id,
                user_id,
            )

            if not finished:
                return False

        return True
    
    async def get_all_likes(self, session_id):
        likes = await self.redis.hgetall(
            self._likes_key(session_id)
        )

        return {
            int(movie_id): int(count)
            for movie_id, count in likes.items()
        }

    async def get_winner(self, session_id):
        likes = await self.get_all_likes(
            session_id,
        )

        if not likes:
            return None

        movie_id = max(
            likes,
            key=likes.get,
        )

        if likes[movie_id] == 0:
            return None

        return movie_id

    async def clear_session(self, session_id, user_ids):
        keys = [
            self._likes_key(session_id),
        ]

        for user_id in user_ids:
            keys.append(
                self._movies_key(session_id, user_id)
            )

            keys.append(
                self._index_key(session_id, user_id)
            )

        if keys:
            await self.redis.delete(*keys)