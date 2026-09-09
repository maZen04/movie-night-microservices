import requests
from django.conf import settings


class MovieService:

    def get_user_watchlist(self, user_id):

        response = requests.get(
            f"{settings.MOVIE_SERVICE_URL}/api/watchlist",
            headers={
                "X-User-ID": str(user_id),
            },
            timeout=5,
        )

        response.raise_for_status()

        data = response.json()

        print("WATCHLIST RESPONSE:", data)

        return data["results"]
        # return [
        #     item["movie"]["id"]
        #     for item in data["results"]
        # ]