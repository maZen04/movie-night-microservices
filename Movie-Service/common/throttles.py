from rest_framework.throttling import UserRateThrottle

class SearchThrottle(UserRateThrottle):
    rate = "60/min"


class MovieDetailThrottle(UserRateThrottle):
    rate = "120/min"


class RecommendationThrottle(UserRateThrottle):
    rate = "30/min"