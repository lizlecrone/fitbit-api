class FitbitException(Exception):
    """All other exceptions subclass this FitbitException."""
    pass


class InsufficientScope(FitbitException):
    """Thrown when your client was not initialized with the necessary scopes to make this request"""
    pass


class RateLimitException(FitbitException):
    """Thrown when you've exceeded the limit

    Fitbit only allows 150 requests per hour per client. ::

        try:
            client.get_foods_goal()
        except RateLimitException as e:
            print('Seconds until we can try again:' e.retry_after)
    """

    def __init__(self, retry_after, *args, **kwargs):
        self.retry_after = retry_after
        super().__init__(*args, **kwargs)

