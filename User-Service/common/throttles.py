from rest_framework.throttling import AnonRateThrottle


class RegisterThrottle(AnonRateThrottle):
    rate = "5/min"


class LoginThrottle(AnonRateThrottle):
    rate = "10/min"