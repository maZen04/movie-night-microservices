from locust import HttpUser, task, between


class MovieUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def search_movies(self):
        self.client.get(
            "/api/movies/search?query=batman",
            name="Search movies"
        )