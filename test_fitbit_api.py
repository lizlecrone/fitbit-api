import mock
from datetime import datetime
from fitbit_api import FitbitClient, ALL_SCOPES, RateLimitException


class FakeOAuth2Session:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def authorization_url(self, url):
        return (url + '?state=123', '123')

    def fetch_token(self, url, authorization_response, client_secret):
        return '123456789'


FitbitClient._OAuth2Session = FakeOAuth2Session


class TestFitbitClient:

    def test_create_using_token(self):
        client_id = 'ABC123'
        callback_uri = 'www.example.com/callback'
        token = '123456789'

        client = FitbitClient.create_using_token(
            client_id=client_id, callback_uri=callback_uri, token=token)

        assert client.session.client_id == 'ABC123'
        assert client.session.redirect_uri == 'www.example.com/callback'
        assert client.session.token == '123456789'

    def test_OAuth2_step_one(self):
        client_id = 'ABC123'
        callback_uri = 'www.example.com/callback'

        authorization_url = FitbitClient.OAuth2_step_one(
            client_id=client_id, callback_uri=callback_uri)

        assert authorization_url == 'https://www.fitbit.com/oauth2/authorize?state=123'

    def test_OAuth2_step_two(self):
        callback = mock.Mock()
        client_id = 'ABC123'
        callback_uri = 'www.example.com/callback'
        client_secret = 'secretthings'
        redirect_uri = 'www.example.com/redirect'

        client = FitbitClient.OAuth2_step_two(
            client_id=client_id,
            callback_uri=callback_uri,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            new_token_callback=callback
            )

        assert callback.call_args.args == ('123456789',)
        assert client.session.client_id == 'ABC123'
        assert client.session.redirect_uri == 'www.example.com/callback'
        assert client.session.token_updater == callback
