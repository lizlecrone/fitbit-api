##########
Quickstart
##########

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Register a Fitbit app
=====================

If you haven't already done so, register your app at https://dev.fitbit.com/apps/new. This will give you your app's Client ID and Client Secret.

Install fitbit_api
==================

fitbit_api can be installed using pip or by cloning the repository `here <https://github.com/lizlecrone/fitbit-api>`_. ::

    pip install fitbit_api

Example
=======

Once you have a Fitbit app registered, you need to initiate an OAuth2 dance to authorize pulling data. For this you'll need your Client ID from the Fitbit app and your Callback URI, which should be the address of whatever page you want to redirect to after authentication. ::

    from fitbit_api import FitbitClient

    CLIENT_ID = 'your Fitbit app Client ID'
    CLIENT_SECRET = 'your Fitbit app Client Secret'
    CALLBACK_URI = 'your Fitbit app Callback URI'

    my_auth_url = FitbitClient.OAuth2_step_one(
        CLIENT_ID,
        CALLBACK_URI,
    )

This will return an address that the user should go to to authorize your app to access their Fitbit data. Once they log in, the page will redirect to the callback URL you indicated when you registered your app, appended with a unique code. ``FitbitClient.OAuth2_step_two`` will take the entire URL as an argument and initialize a client. Note that each user will need a separate client. ::


    callback_uri_with_unique_code = 'address the user was redirected to'

    client = FitbitClient.OAuth2_step_two(
        CLIENT_ID,
        CLIENT_SECRET,
        CALLBACK_URI,
        callback_uri_with_unique_code,
    )

You now have a Fitbit client! You can now access that user's Fitbit data. ::

    client.get_recent_activities()

Go to :doc:`/classapi` for the full list of available methods. Check out :doc:`/authentication` for a deeper dive on authentication methods.