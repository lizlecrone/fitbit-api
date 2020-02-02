##############
Authentication
##############

There are two ways to initialize a client with fitbit_api:

1. :ref:`oauth2-dance`
2. :ref:`create-using-token`

.. _oauth2-dance:

OAuth2 Dance
============

Initiate the OAuth2 dance by calling the class method :any:`FitbitClient.OAuth2_step_one`. ::

    from fitbit_api import FitbitClient

    CLIENT_ID = 'your Fitbit app Client ID'
    CLIENT_SECRET = 'your Fitbit app Client Secret'
    CALLBACK_URI = 'your Fitbit app Callback URI'

    authorization_uri = FitbitClient.OAuth2_step_one(
        client_id=CLIENT_ID,
        redirect_uri=CALLBACK_URI,
    )

The user will need to navigate to ``authorization_uri`` to grant your app access to their data. Once the user logs into their Fitbit account and grants permission, they'll be redirected to a new URI with an appended code. You'll need this for :any:`FitbitClient.OAuth2_step_two`. ::

    redirect_uri = 'address the user was redirected to'

    def new_token_callback(token):
        # save the token somewhere so the user doesn't have to log in again.

    client = FitbitClient.OAuth2_step_two(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        callback_uri=CALLBACK_URI,
        redirect_uri=redirect_uri,
        new_token_callback=new_token_callback,
    )

Fitbit provides refresh tokens, so when this token expires, the client will automatically use the refresh token to request a new one.

If you want to save the session token, :any:`FitbitClient.OAuth2_step_two` takes an optional argument called ``new_token_callback``. The callback will also be called on subsequent tokens created whenever the session token expires.

.. _create-using-token:

Create Using Token
==================

If you have an existing token, you can initialize a client without the user needing to log in again. ::

    from fitbit_api import FitbitClient

    CLIENT_ID = 'your Fitbit app Client ID'
    CALLBACK_URI = 'your Fitbit app Callback URI'

    def new_token_callback(token):
        # save subsequent tokens somewhere so the user doesn't have to log in again.

    token = {}  # some token retrieved from some place
    client = FitbitClient.create_using_token(
        token=token,
        client_id=CLIENT_ID,
        callback_uri=CALLBACK_URI,
        new_token_callback=new_token_callback
    )

Fitbit provides refresh tokens, so when this token expires, the client will automatically use the refresh token to request a new one.

If you want to save subsequent tokens, :any:`FitbitClient.create_using_token` takes an optional argument called ``new_token_callback``.