from locust import HttpUser, task, between
import random
import itertools


# Real test user IDs that already exist in your database
TEST_USER_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Give each Locust user a unique index
_user_counter = itertools.count()


class MovieUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Give every Locust user a different test user ID
        index = next(_user_counter)

        if index >= len(TEST_USER_IDS):
            raise RuntimeError(
                "Not enough TEST_USER_IDS for the number of Locust users."
            )

        self.user_id = TEST_USER_IDS[index]

        self.headers = {
            "X-User-ID": str(self.user_id)
        }

        self.movie_id = None

    @task
    def movie_user_flow(self):

        # ==========================================
        # 1. Search movies
        # ==========================================

        response = self.client.get(
            "/api/movies/search?query=harry%20potter",
            name="1. Search movies"
        )

        if response.status_code != 200:
            return

        results = response.json().get("results", [])

        if not results:
            return

        # Search result ID = TMDB ID
        movie = random.choice(results)
        tmdb_id = movie["id"]

        # ==========================================
        # 2. Get movie details
        # ==========================================

        response = self.client.get(
            f"/api/movies/{tmdb_id}",
            name="2. Get movie details"
        )

        if response.status_code != 200:
            return

        movie_data = response.json()

        # Internal Movie database ID
        self.movie_id = movie_data["id"]

        # ==========================================
        # 3. Add to watchlist
        # ==========================================

        response = self.client.post(
            f"/api/movies/{self.movie_id}/watchlist",
            headers=self.headers,
            name="3. Add to watchlist"
        )

        if response.status_code != 201:
            return

        # ==========================================
        # 4. View watchlist
        # ==========================================

        response = self.client.get(
            "/api/watchlist",
            headers=self.headers,
            name="4. View watchlist"
        )

        if response.status_code != 200:
            return

        # ==========================================
        # 5. Remove from watchlist
        # ==========================================

        response = self.client.delete(
            f"/api/movies/{self.movie_id}/watchlist",
            headers=self.headers,
            name="5. Remove from watchlist"
        )

        if response.status_code != 200:
            return

        # ==========================================
        # 6. Mark as watched
        # ==========================================

        response = self.client.post(
            f"/api/movies/{self.movie_id}/watched",
            headers=self.headers,
            json={
                "rating": random.randint(1, 10)
            },
            name="6. Mark as watched"
        )

        if response.status_code != 201:
            return

        # ==========================================
        # 7. View watched history
        # ==========================================

        response = self.client.get(
            "/api/watched",
            headers=self.headers,
            name="7. View watched history"
        )

        if response.status_code != 200:
            return

        # ==========================================
        # 8. Cleanup
        # ==========================================

        # Remove the movie so the next iteration
        # starts from a clean state.
        self.client.delete(
            f"/api/movies/{self.movie_id}/watched",
            headers=self.headers,
            name="8. Cleanup watched"
        )

        self.movie_id = None