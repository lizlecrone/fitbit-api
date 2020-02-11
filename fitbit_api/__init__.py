from datetime import datetime
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
from requests.auth import HTTPBasicAuth
from fitbit_api.exceptions import FitbitException, InsufficientScope, RateLimitException

ALL_SCOPES = [
    "activity",
    "nutrition",
    "heartrate",
    "location",
    "nutrition",
    "profile",
    "settings",
    "sleep",
    "social",
    "weight",
]
"""All available scopes for initializing Fitbit client"""


class FitbitClient:
    """
    A Fitbit API client
    """

    _OAuth2Session = OAuth2Session

    def __init__(self, session, client_secret):
        self.session = session
        self.client_secret = client_secret

    @classmethod
    def create_using_token(
            cls,
            token,
            client_id,
            client_secret,
            callback_uri,
            scope=None,
            new_token_callback=None):
        '''
        Initialize a client using an existing token.

        :param token: A token provided by Fitbit. You can generate one with :ref:`oauth2-dance`.
        :type token: dict

        :param client_id: Client ID provided when you register your app with Fitbit.
        :type client_id: str

        :param client_secret: Client Secret provided when you register your app with Fitbit.
        :type client_secret: str

        :param callback_uri: Callback URI you provided when you registered your app with Fitbit.
        :type callback_uri: str

        :param scope: List of permissions requested for this client. If none, uses :any:`ALL_SCOPES`.
        :type scope: List[str], optional

        :param new_token_callback: Callback function for saving subsequent tokens provided by Fitbit.
        :type new_token_callback: func, optional

        :returns: A FitbitClient instance
        '''
        scope = scope or ALL_SCOPES
        session = cls._OAuth2Session(
            client_id=client_id,
            redirect_uri=callback_uri,
            scope=scope,
            token=token,
            token_updater=new_token_callback,
            )
        return cls(session, client_secret)

    @classmethod
    def OAuth2_step_one(cls, client_id, callback_uri, scope=None):
        '''
        Initiate the OAuth2 dance.

        :param client_id: Client ID provided when you register your app with Fitbit.
        :type client_id: str

        :param callback_uri: Callback URI you provided when you registered your app with Fitbit.
        :type callback_uri: str

        :param scope: List of permissions requested for this client. If none, uses :any:`ALL_SCOPES`.
        :type scope: List[str], optional

        :returns: Authorization URI where the user will need to navigate to grant your app access to their data.
        '''
        scope = scope or ALL_SCOPES
        session = cls._OAuth2Session(
            client_id=client_id,
            redirect_uri=callback_uri,
            scope=scope)
        authorization_url, state = session.authorization_url(
            'https://www.fitbit.com/oauth2/authorize')
        return authorization_url

    @classmethod
    def OAuth2_step_two(
            cls,
            client_id,
            client_secret,
            callback_uri,
            redirect_uri,
            scope=None,
            new_token_callback=None):
        '''
        Initialize a client by completing the OAuth2 dance.

        :param client_id: Client ID provided when you register your app with Fitbit.
        :type client_id: str

        :param client_secret: Client Secret provided when you register your app with Fitbit.
        :type client_secret: str

        :param callback_uri: Callback URI you provided when you registered your app with Fitbit.
        :type callback_uri: str

        :param redirect_uri: URI the user was redirected to after they granted your app permission.
        :type redirect_uri: str

        :param scope: List of permissions requested for this client. If none, uses :any:`ALL_SCOPES`.
        :type scope: List[str], optional

        :param new_token_callback: Callback function for saving the initial and all subsequent refresh tokens provided by Fitbit.
        :type new_token_callback: func, optional

        :returns: A FitbitClient instance
        '''
        scope = scope or ALL_SCOPES
        session = cls._OAuth2Session(
            client_id=client_id,
            redirect_uri=callback_uri,
            scope=scope,
            token_updater=new_token_callback,
            )
        token = session.fetch_token(
            'https://api.fitbit.com/oauth2/token',
            authorization_response=redirect_uri,
            client_secret=client_secret
            )
        if new_token_callback:
            new_token_callback(token)
        return cls(session, client_secret)

    def refresh_token(self):
        token = self.session.refresh_token(
            'https://api.fitbit.com/oauth2/token',
            auth=HTTPBasicAuth(self.session.client_id, self.client_secret)
            )
        if self.session.token_updater:
            self.session.token_updater(token)
        return token

    def _request(self, method, endpoint, params=None, full_response=False):
        url = 'https://api.fitbit.com' + endpoint
        params = params or {}
        try:
            response = self.session.request(method, url, params=params)
        except TokenExpiredError:
            self.refresh_token()
            response = self.session.request(method, url, params=params)
        if full_response:
            return response
        if response.ok:
            return response.json()
        elif response.status_code == 429:
            raise RateLimitException(
                retry_after=response.headers['Retry-After'])

    def _get(self, endpoint, params=None, **kwargs):
        return self._request('get', endpoint, params, **kwargs)

    def _post(self, endpoint, params=None, **kwargs):
        return self._request('post', endpoint, params, **kwargs)

    def _delete(self, endpoint, params=None, **kwargs):
        return self._request('delete', endpoint, params, **kwargs)

    def _put(self, endpoint, params=None, **kwargs):
        return self._request('put', endpoint, params, **kwargs)

    def get_activities_by_date(self, date, **kwargs):
        '''Get Activity Summary by Date

        Retrieves a summary and list of a user's activities and activity log entries for a given day.

        :param date: A datetime object.
        :type date: datetime

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/date/{date}.json'.replace(
            '{date}', date)

        return self._get(endpoint, **kwargs)

    def get_activities_resource_by_date_range(
            self, resource_path, base_date, end_date, **kwargs):
        '''Get Activity Resource by Date Range

        Returns activities time series data in the specified range for a given resource.

        :param resource_path: The resource-path; see options in the Resource Path Options section in the full documentation. Possible values: ['calories', 'caloriesBMR', 'steps', 'distance', 'floors', 'elevation', 'minutesSedentary', 'minutesLightlyActive', 'minutesFairlyActive', 'minutesVeryActive', 'activityCalories']
        :type resource_path: string
        :param base_date: A datetime object.
        :type base_date: datetime
        :param end_date: A datetime object.
        :type end_date: datetime

        '''
        if not isinstance(base_date, datetime):
            raise ValueError(
                'Argument \'base_date\' must be a datetime object.')
        base_date = base_date.strftime('%Y-%m-%d') if base_date else ''

        if not isinstance(end_date, datetime):
            raise ValueError(
                'Argument \'end_date\' must be a datetime object.')
        end_date = end_date.strftime('%Y-%m-%d') if end_date else ''

        enum = [
            'calories',
            'caloriesBMR',
            'steps',
            'distance',
            'floors',
            'elevation',
            'minutesSedentary',
            'minutesLightlyActive',
            'minutesFairlyActive',
            'minutesVeryActive',
            'activityCalories']
        if resource_path not in enum:
            raise ValueError(
                'Argument \'resource_path\' must be one of the following: {}'.format(enum))

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/{resource-path}/date/{base-date}/{end-date}.json'.replace(
            '{resource-path}',
            resource_path).replace(
            '{base-date}',
            base_date).replace(
            '{end-date}',
            end_date)

        return self._get(endpoint, **kwargs)

    def get_activities_tracker_resource_by_date_range(
            self, resource_path, base_date, end_date, **kwargs):
        '''Get Activity Tracker Resource by Date Range Time Series

        Returns time series data in the specified range for a given resource.

        :param resource_path: The resource-path; see options in the Resource Path Options section in the full documentation. Possible values: ['calories', 'caloriesBMR', 'steps', 'distance', 'floors', 'elevation', 'minutesSedentary', 'minutesLightlyActive', 'minutesFairlyActive', 'minutesVeryActive', 'activityCalories']
        :type resource_path: string
        :param base_date: A datetime object.
        :type base_date: datetime
        :param end_date: A datetime object.
        :type end_date: datetime

        '''
        if not isinstance(base_date, datetime):
            raise ValueError(
                'Argument \'base_date\' must be a datetime object.')
        base_date = base_date.strftime('%Y-%m-%d') if base_date else ''

        if not isinstance(end_date, datetime):
            raise ValueError(
                'Argument \'end_date\' must be a datetime object.')
        end_date = end_date.strftime('%Y-%m-%d') if end_date else ''

        enum = [
            'calories',
            'caloriesBMR',
            'steps',
            'distance',
            'floors',
            'elevation',
            'minutesSedentary',
            'minutesLightlyActive',
            'minutesFairlyActive',
            'minutesVeryActive',
            'activityCalories']
        if resource_path not in enum:
            raise ValueError(
                'Argument \'resource_path\' must be one of the following: {}'.format(enum))

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/tracker/{resource-path}/date/{base-date}/{end-date}.json'.replace(
            '{resource-path}', resource_path).replace('{base-date}', base_date).replace('{end-date}', end_date)

        return self._get(endpoint, **kwargs)

    def get_activities_resource_by_date_period(
            self, resource_path, date, period, **kwargs):
        '''Get Activity Time Series

        Returns time series data in the specified range for a given resource in the format requested using units in the unit system that corresponds to the Accept-Language header provided.

        :param resource_path: The resource-path; see options in the Resource Path Options section in the full documentation. Possible values: ['calories', 'caloriesBMR', 'steps', 'distance', 'floors', 'elevation', 'minutesSedentary', 'minutesLightlyActive', 'minutesFairlyActive', 'minutesVeryActive', 'activityCalories']
        :type resource_path: string
        :param date: A datetime object.
        :type date: datetime
        :param period: The range for which data will be returned. Options are 1d, 7d, 30d, 1w, 1m, 3m, 6m, 1y, or max.
        :type period: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        enum = [
            'calories',
            'caloriesBMR',
            'steps',
            'distance',
            'floors',
            'elevation',
            'minutesSedentary',
            'minutesLightlyActive',
            'minutesFairlyActive',
            'minutesVeryActive',
            'activityCalories']
        if resource_path not in enum:
            raise ValueError(
                'Argument \'resource_path\' must be one of the following: {}'.format(enum))

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/{resource-path}/date/{date}/{period}.json'.replace(
            '{resource-path}', resource_path).replace('{date}', date).replace('{period}', period)

        return self._get(endpoint, **kwargs)

    def get_activities_tracker_resource_by_date_period(
            self, resource_path, date, period, **kwargs):
        '''Get Activity Time Series

        Returns time series data in the specified range for a given resource in the format requested using units in the unit system that corresponds to the Accept-Language header provided.

        :param resource_path: The resource-path; see options in the Resource Path Options section in the full documentation. Possible values: ['calories', 'caloriesBMR', 'steps', 'distance', 'floors', 'elevation', 'minutesSedentary', 'minutesLightlyActive', 'minutesFairlyActive', 'minutesVeryActive', 'activityCalories']
        :type resource_path: string
        :param date: A datetime object.
        :type date: datetime
        :param period: The range for which data will be returned. Options are 1d, 7d, 30d, 1w, 1m, 3m, 6m, 1y, or max.
        :type period: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        enum = [
            'calories',
            'caloriesBMR',
            'steps',
            'distance',
            'floors',
            'elevation',
            'minutesSedentary',
            'minutesLightlyActive',
            'minutesFairlyActive',
            'minutesVeryActive',
            'activityCalories']
        if resource_path not in enum:
            raise ValueError(
                'Argument \'resource_path\' must be one of the following: {}'.format(enum))

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/tracker/{resource-path}/date/{date}/{period}.json'.replace(
            '{resource-path}', resource_path).replace('{date}', date).replace('{period}', period)

        return self._get(endpoint, **kwargs)

    def get_activities_resource_by_date_range_intraday(
            self, resource_path, base_date, end_date, detail_level, **kwargs):
        '''Get Activity Intraday Time Series

        Returns the Activity Intraday Time Series for a given resource in the format requested.

        :param resource_path: The resource-path; see options in the Resource Path Options section in the full documentation. Possible values: ['calories', 'steps', 'distance', 'floors', 'elevation']
        :type resource_path: string
        :param base_date: A datetime object.
        :type base_date: datetime
        :param end_date: A datetime object.
        :type end_date: datetime
        :param detail_level: Number of data points to include. Either 1min or 15min. Optional.
        :type detail_level: string

        '''
        if not isinstance(base_date, datetime):
            raise ValueError(
                'Argument \'base_date\' must be a datetime object.')
        base_date = base_date.strftime('%Y-%m-%d') if base_date else ''

        if not isinstance(end_date, datetime):
            raise ValueError(
                'Argument \'end_date\' must be a datetime object.')
        end_date = end_date.strftime('%Y-%m-%d') if end_date else ''

        enum = ['calories', 'steps', 'distance', 'floors', 'elevation']
        if resource_path not in enum:
            raise ValueError(
                'Argument \'resource_path\' must be one of the following: {}'.format(enum))

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/{resource-path}/date/{base-date}/{end-date}/{detail-level}.json'.replace(
            '{resource-path}',
            resource_path).replace(
            '{base-date}',
            base_date).replace(
            '{end-date}',
            end_date).replace(
                '{detail-level}',
            detail_level)

        return self._get(endpoint, **kwargs)

    def get_activities_resource_by_date_intraday(
            self, resource_path, date, detail_level, **kwargs):
        '''Get Intraday Time Series

        Returns the Intraday Time Series for a given resource in the format requested.

        :param resource_path: The resource-path; see options in the Resource Path Options section in the full documentation. Possible values: ['calories', 'steps', 'distance', 'floors', 'elevation']
        :type resource_path: string
        :param date: A datetime object.
        :type date: datetime
        :param detail_level: Number of data points to include. Either 1min or 15min. Optional.
        :type detail_level: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        enum = ['calories', 'steps', 'distance', 'floors', 'elevation']
        if resource_path not in enum:
            raise ValueError(
                'Argument \'resource_path\' must be one of the following: {}'.format(enum))

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/{resource-path}/date/{date}/1d/{detail-level}.json'.replace(
            '{resource-path}',
            resource_path).replace(
            '{date}',
            date).replace(
            '{detail-level}',
            detail_level)

        return self._get(endpoint, **kwargs)

    def get_activities_resource_by_date_range_time_series_intraday(
            self,
            resource_path,
            date,
            end_date,
            detail_level,
            start_time,
            end_time,
            **kwargs):
        '''Get Activity Intraday Time Series

        Returns the Intraday Time Series for a given resource in the format requested.

        :param resource_path: The resource-path; see options in the Resource Path Options section in the full documentation. Possible values: ['calories', 'steps', 'distance', 'floors', 'elevation']
        :type resource_path: string
        :param date: A datetime object.
        :type date: datetime
        :param end_date: A datetime object.
        :type end_date: datetime
        :param detail_level: Number of data points to include. Either 1min or 15min.
        :type detail_level: string
        :param start_time: The start of the period in the format HH:mm.
        :type start_time: string
        :param end_time: The end of the period in the format HH:mm.
        :type end_time: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        if not isinstance(end_date, datetime):
            raise ValueError(
                'Argument \'end_date\' must be a datetime object.')
        end_date = end_date.strftime('%Y-%m-%d') if end_date else ''

        enum = ['calories', 'steps', 'distance', 'floors', 'elevation']
        if resource_path not in enum:
            raise ValueError(
                'Argument \'resource_path\' must be one of the following: {}'.format(enum))

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/{resource-path}/date/{date}/{end-date}/{detail-level}/time/{start-time}/{end-time}.json'.replace(
            '{resource-path}',
            resource_path).replace(
            '{date}',
            date).replace(
            '{end-date}',
            end_date).replace(
                '{detail-level}',
                detail_level).replace(
                    '{start-time}',
                    start_time).replace(
                        '{end-time}',
            end_time)

        return self._get(endpoint, **kwargs)

    def get_activities_resource_by_date_time_series_intraday(
            self, resource_path, date, detail_level, start_time, end_time, **kwargs):
        '''Get Intraday Time Series

        Returns the Intraday Time Series for a given resource in the format requested.

        :param resource_path: The resource-path; see options in the Resource Path Options section in the full documentation. Possible values: ['calories', 'steps', 'distance', 'floors', 'elevation']
        :type resource_path: string
        :param date: A datetime object.
        :type date: datetime
        :param detail_level: Number of data points to include. Either 1min or 15min.
        :type detail_level: string
        :param start_time: The start of the period in the format HH:mm.
        :type start_time: string
        :param end_time: The end of the period in the format HH:mm.
        :type end_time: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        enum = ['calories', 'steps', 'distance', 'floors', 'elevation']
        if resource_path not in enum:
            raise ValueError(
                'Argument \'resource_path\' must be one of the following: {}'.format(enum))

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/{resource-path}/date/{date}/1d/{detail-level}/time/{start-time}/{end-time}.json'.replace(
            '{resource-path}',
            resource_path).replace(
            '{date}',
            date).replace(
            '{detail-level}',
            detail_level).replace(
                '{start-time}',
                start_time).replace(
                    '{end-time}',
            end_time)

        return self._get(endpoint, **kwargs)

    def add_activities_log(
            self,
            activity_id,
            manual_calories,
            start_time,
            duration_millis,
            date,
            distance,
            activity_name=None,
            distance_unit=None,
            **kwargs):
        '''Log Activity

        The Log Activity endpoint creates log entry for an activity or user's private custom activity using units in the unit system which corresponds to the Accept-Language header provided (or using optional custom distanceUnit) and get a response in the format requested.

        :param activity_id: The ID of the activity, directory activity or intensity level activity.
        :type activity_id: int
        :param manual_calories: Calories burned that are manaully specified. Required with activityName must be provided.
        :type manual_calories: int
        :param start_time: Activity start time. Hours and minutes in the format HH:mm:ss.
        :type start_time: string
        :param duration_millis: Duration in milliseconds.
        :type duration_millis: int
        :param date: A datetime object.
        :type date: datetime
        :param distance: Distance is required for logging directory activity in the format X.XX and in the selected distanceUnit.
        :type distance: int
        :param activity_name: Custom activity name. Either activityId or activityName must be provided.
        :type activity_name: string, optional
        :param distance_unit: Distance measurement unit. Steps units are available only for Walking (activityId=90013) and Running (activityId=90009) directory activities and their intensity levels.
        :type distance_unit: int, optional

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities.json'
        params = {}
        params['activityId'] = activity_id
        if activity_name:
            params['activityName'] = activity_name
        params['manualCalories'] = manual_calories
        params['startTime'] = start_time
        params['durationMillis'] = duration_millis
        params['date'] = date
        params['distance'] = distance
        if distance_unit:
            params['distanceUnit'] = distance_unit
        return self._post(endpoint, params=params, **kwargs)

    def get_activities_log(self, **kwargs):
        '''Get Lifetime Stats

        Updates a user's daily activity goals and returns a response using units in the unit system which corresponds to the Accept-Language header provided.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities.json'

        return self._get(endpoint, **kwargs)

    def delete_activities_log(self, activity_log_id, **kwargs):
        '''Delete Activity Log

        Deletes a user's activity log entry with the given ID.

        :param activity_log_id: The id of the activity log entry.
        :type activity_log_id: int

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/{activity-log-id}.json'.replace(
            '{activity-log-id}', activity_log_id)

        return self._delete(endpoint, **kwargs)

    def get_activities_log_list(
            self,
            sort,
            offset,
            limit,
            before_date=None,
            after_date=None,
            **kwargs):
        '''Get Activity Log List

        Retreives a list of user's activity log entries before or after a given day with offset and limit using units in the unit system which corresponds to the Accept-Language header provided.

        :param sort: The sort order of entries by date asc (ascending) or desc (descending).
        :type sort: string
        :param offset: The offset number of entries.
        :type offset: int
        :param limit: The maximum number of entries returned (maximum;100).
        :type limit: int
        :param before_date: A datetime object.
        :type before_date: datetime, optional
        :param after_date: A datetime object.
        :type after_date: datetime, optional

        '''
        if before_date and not isinstance(before_date, datetime):
            raise ValueError(
                'Argument \'before_date\' must be a datetime object.')
        before_date = before_date.strftime('%Y-%m-%d') if before_date else ''

        if after_date and not isinstance(after_date, datetime):
            raise ValueError(
                'Argument \'after_date\' must be a datetime object.')
        after_date = after_date.strftime('%Y-%m-%d') if after_date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/list.json'
        params = {}
        if before_date:
            params['beforeDate'] = before_date
        if after_date:
            params['afterDate'] = after_date
        params['sort'] = sort
        params['offset'] = offset
        params['limit'] = limit
        return self._get(endpoint, params=params, **kwargs)

    def get_activities_t_c_x(
            self,
            log_id,
            include_partial_t_c_x=None,
            **kwargs):
        '''Get Activity TCX

        Retreives the details of a user's location and heart rate data during a logged exercise activity.

        :param log_id: The activity's log ID.
        :type log_id: string
        :param include_partial_t_c_x: Include TCX points regardless of GPS data being present
        :type include_partial_t_c_x: bool, optional

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/{log-id}.tcx'.replace(
            '{log-id}', log_id)
        params = {}
        if include_partial_t_c_x:
            params['includePartialTCX'] = include_partial_t_c_x
        return self._get(endpoint, params=params, **kwargs)

    def get_activities_types(self, **kwargs):
        '''Browse Activity Types

        Retreives a tree of all valid Fitbit public activities from the activities catelog as well as private custom activities the user created in the format requested.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/activities.json'

        return self._get(endpoint, **kwargs)

    def get_activities_type_detail(self, activity_id, **kwargs):
        '''Get Activity Type

        Returns the detail of a specific activity in the Fitbit activities database in the format requested. If activity has levels, it also returns a list of activity level details.

        :param activity_id: The activity ID.
        :type activity_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/activities/{activity-id}.json'.replace(
            '{activity-id}', activity_id)

        return self._get(endpoint, **kwargs)

    def get_frequent_activities(self, **kwargs):
        '''Get Frequent Activities

        Retreives a list of a user's frequent activities in the format requested using units in the unit system which corresponds to the Accept-Language header provided.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/frequent.json'

        return self._get(endpoint, **kwargs)

    def get_recent_activities(self, **kwargs):
        '''Get Recent Activity Types

        Retreives a list of a user's recent activities types logged with some details of the last activity log of that type using units in the unit system which corresponds to the Accept-Language header provided.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/recent.json'

        return self._get(endpoint, **kwargs)

    def get_favorite_activities(self, **kwargs):
        '''Get Favorite Activities

        Returns a list of a user's favorite activities.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/favorite.json'

        return self._get(endpoint, **kwargs)

    def delete_favorite_activities(self, activity_id, **kwargs):
        '''Delete Favorite Activity

        Removes the activity with the given ID from a user's list of favorite activities.

        :param activity_id: The ID of the activity to be removed.
        :type activity_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/favorite/{activity-id}.json'.replace(
            '{activity-id}', activity_id)

        return self._delete(endpoint, **kwargs)

    def add_favorite_activities(self, activity_id, **kwargs):
        '''Add Favorite Activity

        Adds the activity with the given ID to user's list of favorite activities.

        :param activity_id: The encoded ID of the activity.
        :type activity_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/favorite/{activity-id}.json'.replace(
            '{activity-id}', activity_id)

        return self._post(endpoint, **kwargs)

    def get_activities_goals(self, period, **kwargs):
        '''Get Activity Goals

        Retreives a user's current daily or weekly activity goals using measurement units as defined in the unit system, which corresponds to the Accept-Language header provided.

        :param period: daily or weekly.
        :type period: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/goals/{period}.json'.replace(
            '{period}', period)

        return self._get(endpoint, **kwargs)

    def add_update_activities_goals(self, period, type, value, **kwargs):
        '''Update Activity Goals

        Updates a user's daily or weekly activity goals and returns a response using units in the unit system which corresponds to the Accept-Language header provided.

        :param period: daily or weekly.
        :type period: string
        :param type: goal type
        :type type: string
        :param value: goal value
        :type value: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/goals/{period}.json'.replace(
            '{period}', period)
        params = {}
        params['type'] = type
        params['value'] = value
        return self._post(endpoint, params=params, **kwargs)

    def get_body_fat_by_date(self, date, **kwargs):
        '''Get Body Fat Logs

        Retreives a list of all user's body fat log entries for a given day in the format requested.

        :param date: A datetime object.
        :type date: datetime

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/fat/date/{date}.json'.replace(
            '{date}', date)

        return self._get(endpoint, **kwargs)

    def get_body_fat_by_date_period(self, date, period, **kwargs):
        '''Get Body Fat Logs

        Retreives a list of all user's body fat log entries for a given day in the format requested.

        :param date: A datetime object.
        :type date: datetime
        :param period: The range for which data will be returned. Options are 1d, 7d, 30d, 1w, 1m, 3m, 6m, 1y, or max.
        :type period: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/fat/date/{date}/{period}.json'.replace(
            '{date}', date).replace('{period}', period)

        return self._get(endpoint, **kwargs)

    def get_body_fat_by_date_range(self, base_date, end_date, **kwargs):
        '''Get Body Fat Logs

        Retreives a list of all user's body fat log entries for a given day in the format requested.

        :param base_date: A datetime object.
        :type base_date: datetime
        :param end_date: A datetime object.
        :type end_date: datetime

        '''
        if not isinstance(base_date, datetime):
            raise ValueError(
                'Argument \'base_date\' must be a datetime object.')
        base_date = base_date.strftime('%Y-%m-%d') if base_date else ''

        if not isinstance(end_date, datetime):
            raise ValueError(
                'Argument \'end_date\' must be a datetime object.')
        end_date = end_date.strftime('%Y-%m-%d') if end_date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/fat/date/{base-date}/{end-date}.json'.replace(
            '{base-date}', base_date).replace('{end-date}', end_date)

        return self._get(endpoint, **kwargs)

    def add_body_fat_log(self, fat, date, time, **kwargs):
        '''Log Body Fat

        Creates a log entry for body fat and returns a response in the format requested.

        :param fat: Body fat in the format of X.XX in the unit system that corresponds to the Accept-Language header provided.
        :type fat: int
        :param date: A datetime object.
        :type date: datetime
        :param time: Time of the measurement in hours and minutes in the format HH:mm:ss that is set to the last second of the day if not provided.
        :type time: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/fat.json'
        params = {}
        params['fat'] = fat
        params['date'] = date
        params['time'] = time
        return self._post(endpoint, params=params, **kwargs)

    def delete_body_fat_log(self, body_fat_log_id, **kwargs):
        '''Delete Body Fat Log

        Deletes a user's body fat log entry with the given ID.

        :param body_fat_log_id: The ID of the body fat log entry.
        :type body_fat_log_id: int

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/fat/{body-fat-log-id}.json'.replace(
            '{body-fat-log-id}', body_fat_log_id)

        return self._delete(endpoint, **kwargs)

    def get_body_resource_by_date_period(
            self, resource_path, date, period, **kwargs):
        '''Get Body Time Series

        Returns time series data in the specified range for a given resource in the format requested using units in the unit system that corresponds to the Accept-Language header provided.

        :param resource_path: The resource path, which incudes the bmi, fat, or weight options. Possible values: ['bmi', 'fat', 'weight']
        :type resource_path: string
        :param date: A datetime object.
        :type date: datetime
        :param period: The range for which data will be returned. Options are 1d, 7d, 30d, 1w, 1m, 3m, 6m, 1y, or max.
        :type period: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        enum = ['bmi', 'fat', 'weight']
        if resource_path not in enum:
            raise ValueError(
                'Argument \'resource_path\' must be one of the following: {}'.format(enum))

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/{resource-path}/date/{date}/{period}.json'.replace(
            '{resource-path}',
            resource_path).replace(
            '{date}',
            date).replace(
            '{period}',
            period)

        return self._get(endpoint, **kwargs)

    def get_body_resource_by_date_range(
            self,
            resource_path,
            base_date,
            end_date,
            **kwargs):
        '''Get Body Time Series

        Returns time series data in the specified range for a given resource in the format requested using units in the unit system that corresponds to the Accept-Language header provided.

        :param resource_path: The resource path, which incudes the bmi, fat, or weight options. Possible values: ['bmi', 'fat', 'weight']
        :type resource_path: string
        :param base_date: A datetime object.
        :type base_date: datetime
        :param end_date: A datetime object.
        :type end_date: datetime

        '''
        if not isinstance(base_date, datetime):
            raise ValueError(
                'Argument \'base_date\' must be a datetime object.')
        base_date = base_date.strftime('%Y-%m-%d') if base_date else ''

        if not isinstance(end_date, datetime):
            raise ValueError(
                'Argument \'end_date\' must be a datetime object.')
        end_date = end_date.strftime('%Y-%m-%d') if end_date else ''

        enum = ['bmi', 'fat', 'weight']
        if resource_path not in enum:
            raise ValueError(
                'Argument \'resource_path\' must be one of the following: {}'.format(enum))

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/{resource-path}/date/{base-date}/{end-date}.json'.replace(
            '{resource-path}',
            resource_path).replace(
            '{base-date}',
            base_date).replace(
            '{end-date}',
            end_date)

        return self._get(endpoint, **kwargs)

    def get_body_goals(self, goal_type, **kwargs):
        '''Get Body Goals

        Retreives a user's current body fat percentage or weight goal using units in the unit systems that corresponds to the Accept-Language header providedin the format requested.

        :param goal_type: weight or fat.
        :type goal_type: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/{goal-type}/goal.json'.replace(
            '{goal-type}', goal_type)

        return self._get(endpoint, **kwargs)

    def update_body_fat_goal(self, fat, **kwargs):
        '''Update Body Fat Goal

        Updates user's fat percentage goal.

        :param fat: Target body fat percentage; in the format X.XX.
        :type fat: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/fat/goal.json'
        params = {}
        params['fat'] = fat
        return self._post(endpoint, params=params, **kwargs)

    def update_weight_goal(
            self,
            start_date,
            start_weight,
            weight=None,
            **kwargs):
        '''Update Weight Goal

        Updates user's fat percentage goal.

        :param start_date: A datetime object.
        :type start_date: datetime
        :param start_weight: Weight goal start weight; in the format X.XX, in the unit systems that corresponds to the Accept-Language header provided.
        :type start_weight: string
        :param weight: Weight goal target weight; in the format X.XX, in the unit systems that corresponds to the Accept-Language header provided; required if user doesn't have an existing weight goal.
        :type weight: string, optional

        '''
        required_scope = set(['profile', 'heartrate', 'location'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/weight/goal.json'
        params = {}
        params['startDate'] = start_date
        params['startWeight'] = start_weight
        if weight:
            params['weight'] = weight
        return self._post(endpoint, params=params, **kwargs)

    def get_weight_by_date(self, date, **kwargs):
        '''Get Weight Logs

        Retreives a list of all user's body weight log entries for a given day using units in the unit systems which corresponds to the Accept-Language header provided.

        :param date: A datetime object.
        :type date: datetime

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/weight/date/{date}.json'.replace(
            '{date}', date)

        return self._get(endpoint, **kwargs)

    def get_weight_by_date_period(self, date, period, **kwargs):
        '''Get Body Fat Logs

        Retreives a list of all user's body weight log entries for a given day in the format requested.

        :param date: A datetime object.
        :type date: datetime
        :param period: The range for which data will be returned. Options are 1d, 7d, 30d, 1w, 1m, 3m, 6m, 1y, or max.
        :type period: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/weight/date/{date}/{period}.json'.replace(
            '{date}', date).replace('{period}', period)

        return self._get(endpoint, **kwargs)

    def get_weight_by_date_range(self, base_date, end_date, **kwargs):
        '''Get Body Fat Logs

        Retreives a list of all user's body fat log entries for a given day in the format requested.

        :param base_date: A datetime object.
        :type base_date: datetime
        :param end_date: A datetime object.
        :type end_date: datetime

        '''
        if not isinstance(base_date, datetime):
            raise ValueError(
                'Argument \'base_date\' must be a datetime object.')
        base_date = base_date.strftime('%Y-%m-%d') if base_date else ''

        if not isinstance(end_date, datetime):
            raise ValueError(
                'Argument \'end_date\' must be a datetime object.')
        end_date = end_date.strftime('%Y-%m-%d') if end_date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/weight/date/{base-date}/{end-date}.json'.replace(
            '{base-date}', base_date).replace('{end-date}', end_date)

        return self._get(endpoint, **kwargs)

    def add_weight_log(self, weight, date, time=None, **kwargs):
        '''Log Weight

        Creates log entry for a body weight using units in the unit systems that corresponds to the Accept-Language header provided and gets a response in the format requested.

        :param weight: Weight in the format of X.XX.
        :type weight: int
        :param date: A datetime object.
        :type date: datetime
        :param time: Time of the measurement; hours and minutes in the format of HH:mm:ss, which is set to the last second of the day if not provided.
        :type time: string, optional

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/weight.json'
        params = {}
        params['weight'] = weight
        params['date'] = date
        if time:
            params['time'] = time
        return self._post(endpoint, params=params, **kwargs)

    def delete_weight_log(self, body_weight_log_id, **kwargs):
        '''Delete Weight Log

        Deletes a user's body weight log entrywith the given ID.

        :param body_weight_log_id: The ID of the body weight log entry.
        :type body_weight_log_id: int

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/body/log/weight/{body-weight-log-id}.json'.replace(
            '{body-weight-log-id}', body_weight_log_id)

        return self._delete(endpoint, **kwargs)

    def get_devices(self, **kwargs):
        '''Get Devices

        Returns a list of the Fitbit devices connected to a user's account.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/devices.json'

        return self._get(endpoint, **kwargs)

    def get_alarms(self, tracker_id, **kwargs):
        '''Get Alarms

        Returns alarms for a device

        :param tracker_id: The ID of the tracker for which data is returned. The tracker-id value is found via the Get Devices endpoint.
        :type tracker_id: int

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/devices/tracker/{tracker-id}/alarms.json'.replace(
            '{tracker-id}', tracker_id)

        return self._get(endpoint, **kwargs)

    def add_alarms(
            self,
            tracker_id,
            time,
            enabled,
            recurring,
            week_days,
            **kwargs):
        '''Add Alarm

        Adds the alarm settings to a given ID for a given device.

        :param tracker_id: The ID of the tracker for which data is returned. The tracker-id value is found via the Get Devices endpoint.
        :type tracker_id: int
        :param time: Time of day that the alarm vibrates with a UTC timezone offset, e.g. 07:15-08:00.
        :type time: string
        :param enabled: true or false. If false, alarm does not vibrate until enabled is set to true.
        :type enabled: bool
        :param recurring: true or false. If false, the alarm is a single event.
        :type recurring: string
        :param week_days: Comma separated list of days of the week on which the alarm vibrates, e.g. MONDAY, TUESDAY.
        :type week_days: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/devices/tracker/{tracker-id}/alarms.json'.replace(
            '{tracker-id}', tracker_id)
        params = {}
        params['time'] = time
        params['enabled'] = enabled
        params['recurring'] = recurring
        params['weekDays'] = week_days
        return self._post(endpoint, params=params, **kwargs)

    def update_alarms(
            self,
            tracker_id,
            alarm_id,
            time,
            enabled,
            recurring,
            week_days,
            snooze_length,
            snooze_count,
            **kwargs):
        '''Update Alarm

        Updates the alarm entry with a given ID for a given device. It also gets a response in the format requested.

        :param tracker_id: The ID of the tracker for which data is returned. The tracker-id value is found via the Get Devices endpoint.
        :type tracker_id: int
        :param alarm_id: The ID of the alarm to be updated. The alarm-id value is found in the response of the Get Activity endpoint.
        :type alarm_id: int
        :param time: Time of day that the alarm vibrates with a UTC timezone offset, e.g. 07:15-08:00.
        :type time: string
        :param enabled: true or false. If false, the alarm does not vibrate until enabled is set to true.
        :type enabled: bool
        :param recurring: true or false. If false, the alarm is a single event.
        :type recurring: string
        :param week_days: Comma seperated list of days of the week on which the alarm vibrates, e.g. MONDAY, TUESDAY.
        :type week_days: string
        :param snooze_length: Minutes between alarms.
        :type snooze_length: int
        :param snooze_count: Maximum snooze count.
        :type snooze_count: int

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/devices/tracker/{tracker-id}/alarms/{alarm-id}.json'.replace(
            '{tracker-id}', tracker_id).replace('{alarm-id}', alarm_id)
        params = {}
        params['time'] = time
        params['enabled'] = enabled
        params['recurring'] = recurring
        params['weekDays'] = week_days
        params['snoozeLength'] = snooze_length
        params['snoozeCount'] = snooze_count
        return self._post(endpoint, params=params, **kwargs)

    def delete_alarms(self, tracker_id, alarm_id, **kwargs):
        '''Delete Alarm

        Deletes the user's device alarm entry with the given ID for a given device.

        :param tracker_id: The ID of the tracker whose alarms is managed. The tracker-id value is found via the Get Devices endpoint.
        :type tracker_id: int
        :param alarm_id: The ID of the alarm to be updated. The alarm-id value is found via the Get Alarms endpoint.
        :type alarm_id: int

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/devices/tracker/{tracker-id}/alarms/{alarm-id}.json'.replace(
            '{tracker-id}', tracker_id).replace('{alarm-id}', alarm_id)

        return self._delete(endpoint, **kwargs)

    def get_foods_locales(self, **kwargs):
        '''Get Food Locales

        Returns the food locales that the user may choose to search, log, and create food in.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/foods/locales.json'

        return self._get(endpoint, **kwargs)

    def get_foods_goal(self, **kwargs):
        '''Get Food Goals

        Returns a user's current daily calorie consumption goal and/or foodPlan value in the format requested.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/goal.json'

        return self._get(endpoint, **kwargs)

    def add_update_foods_goal(
            self,
            calories,
            intensity=None,
            personalized=None,
            **kwargs):
        '''Update Food Goal

        Updates a user's daily calories consumption goal or food plan and returns a response in the format requested.

        :param calories: Manual calorie consumption goal in either calories or intensity must be provided.
        :type calories: int
        :param intensity: Food plan intensity (MAINTENANCE, EASIER, MEDIUM, KINDAHARD, or HARDER). Either calories or intensity must be provided.
        :type intensity: string, optional
        :param personalized: Food plan type; true or false.
        :type personalized: string, optional

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/goal.json'
        params = {}
        params['calories'] = calories
        if intensity:
            params['intensity'] = intensity
        if personalized:
            params['personalized'] = personalized
        return self._post(endpoint, params=params, **kwargs)

    def get_foods_by_date(self, date, **kwargs):
        '''Get Food Logs

        Retreives a summary and list of a user's food log entries for a given day in the format requested.

        :param date: A datetime object.
        :type date: datetime

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/date/{date}.json'.replace(
            '{date}', date)

        return self._get(endpoint, **kwargs)

    def get_water_by_date(self, date, **kwargs):
        '''Get Water Logs

        Retreives a summary and list of a user's water log entries for a given day in the requested using units in the unit system that corresponds to the Accept-Language header provided.

        :param date: A datetime object.
        :type date: datetime

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/water/date/{date}.json'.replace(
            '{date}', date)

        return self._get(endpoint, **kwargs)

    def get_water_goal(self, **kwargs):
        '''Get Water Goal

        Retreives a summary and list of a user's water goal entries for a given day in the requested using units in the unit system that corresponds to the Accept-Language header provided.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/water/goal.json'

        return self._get(endpoint, **kwargs)

    def add_update_water_goal(self, target, **kwargs):
        '''Update Water Goal

        Updates a user's daily calories consumption goal or food plan and returns a response in the format requested.

        :param target: The target water goal in the format X.X is set in unit based on locale.
        :type target: int

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/water/goal.json'
        params = {}
        params['target'] = target
        return self._post(endpoint, params=params, **kwargs)

    def get_foods_by_date_range(
            self,
            resource_path,
            base_date,
            end_date,
            **kwargs):
        '''Get Food or Water Time Series

        Updates a user's daily activity goals and returns a response using units in the unit system which corresponds to the Accept-Language header provided.

        :param resource_path: The resouce path. See options in the Resouce Path Options section in the full documentation. Possible values: ['caloriesIn', 'water']
        :type resource_path: string
        :param base_date: A datetime object.
        :type base_date: datetime
        :param end_date: A datetime object.
        :type end_date: datetime

        '''
        if not isinstance(base_date, datetime):
            raise ValueError(
                'Argument \'base_date\' must be a datetime object.')
        base_date = base_date.strftime('%Y-%m-%d') if base_date else ''

        if not isinstance(end_date, datetime):
            raise ValueError(
                'Argument \'end_date\' must be a datetime object.')
        end_date = end_date.strftime('%Y-%m-%d') if end_date else ''

        enum = ['caloriesIn', 'water']
        if resource_path not in enum:
            raise ValueError(
                'Argument \'resource_path\' must be one of the following: {}'.format(enum))

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/{resource-path}/date/{base-date}/{end-date}.json'.replace(
            '{resource-path}',
            resource_path).replace(
            '{base-date}',
            base_date).replace(
            '{end-date}',
            end_date)

        return self._get(endpoint, **kwargs)

    def get_foods_resource_by_date_period(
            self, resource_path, date, period, **kwargs):
        '''Get Food or Water Time Series

        Updates a user's daily activity goals and returns a response using units in the unit system which corresponds to the Accept-Language header provided.

        :param resource_path: The resouce path. See options in the Resouce Path Options section in the full documentation. Possible values: ['caloriesIn', 'water']
        :type resource_path: string
        :param date: A datetime object.
        :type date: datetime
        :param period: The range for which data will be returned. Options are 1d, 7d, 30d, 1w, 3m, 6m, 1y, or max.
        :type period: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        enum = ['caloriesIn', 'water']
        if resource_path not in enum:
            raise ValueError(
                'Argument \'resource_path\' must be one of the following: {}'.format(enum))

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/{resource-path}/date/{date}/{period}.json'.replace(
            '{resource-path}',
            resource_path).replace(
            '{date}',
            date).replace(
            '{period}',
            period)

        return self._get(endpoint, **kwargs)

    def add_foods_log(
            self,
            food_id,
            meal_type_id,
            unit_id,
            amount,
            date,
            food_name=None,
            favorite=None,
            brand_name=None,
            calories=None,
            **kwargs):
        '''Log Food

        Creates food log entries for users with or without foodId value.

        :param food_id: The ID of the food to be logged. Either foodId or foodName must be provided.
        :type food_id: string
        :param meal_type_id: Meal types. 1=Breakfast; 2=Morning Snack; 3=Lunch; 4=Afternoon Snack; 5=Dinner; 7=Anytime.
        :type meal_type_id: string
        :param unit_id: The ID of units used. Typically retrieved via a previous call to Get Food Logs, Search Foods, or Get Food Units.
        :type unit_id: string
        :param amount: The amount consumed in the format X.XX in the specified unitId.
        :type amount: string
        :param date: A datetime object.
        :type date: datetime
        :param food_name: Food entry name. Either foodId or foodName must be provided.
        :type food_name: string, optional
        :param favorite: The `true` value will add the food to the user's favorites after creating the log entry; while the `false` value will not. Valid only with foodId value.
        :type favorite: bool, optional
        :param brand_name: Brand name of food. Valid only with foodName parameters.
        :type brand_name: string, optional
        :param calories: Calories for this serving size. This is allowed with foodName parameter (default to zero); otherwise it is ignored.
        :type calories: int, optional

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log.json'
        params = {}
        params['foodId'] = food_id
        if food_name:
            params['foodName'] = food_name
        params['mealTypeId'] = meal_type_id
        params['unitId'] = unit_id
        params['amount'] = amount
        params['date'] = date
        if favorite:
            params['favorite'] = favorite
        if brand_name:
            params['brandName'] = brand_name
        if calories:
            params['calories'] = calories
        return self._post(endpoint, params=params, **kwargs)

    def delete_foods_log(self, food_log_id, **kwargs):
        '''Delete Food Log

        Deletes a user's food log entry with the given ID.

        :param food_log_id: The ID of the food log entry to be deleted.
        :type food_log_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/{food-log-id}.json'.replace(
            '{food-log-id}', food_log_id)

        return self._delete(endpoint, **kwargs)

    def add_water_log(self, date, amount, unit=None, **kwargs):
        '''Log Water

        Creates a log entry for water using units in the unit systems that corresponds to the Accept-Language header provided.

        :param date: A datetime object.
        :type date: datetime
        :param amount: The amount consumption in the format X.XX and in the specified waterUnit or in the unit system that corresponds to the Accept-Language header provided.
        :type amount: int
        :param unit: Water measurement unit; `ml`, `fl oz`, or `cup`.
        :type unit: string, optional

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/water.json'
        params = {}
        params['date'] = date
        params['amount'] = amount
        if unit:
            params['unit'] = unit
        return self._post(endpoint, params=params, **kwargs)

    def delete_water_log(self, water_log_id, **kwargs):
        '''Delete Water Log

        Deletes a user's water log entry with the given ID.

        :param water_log_id: The ID of the waterUnit log entry to be deleted.
        :type water_log_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/water/{water-log-id}.json'.replace(
            '{water-log-id}', water_log_id)

        return self._delete(endpoint, **kwargs)

    def update_water_log(self, water_log_id, amount, unit=None, **kwargs):
        '''Update Water Log

        Updates a user's water log entry with the given ID.

        :param water_log_id: The ID of the waterUnit log entry to be deleted.
        :type water_log_id: string
        :param amount: Amount consumed; in the format X.X and in the specified waterUnit or in the unit system that corresponds to the Accept-Language header provided.
        :type amount: string
        :param unit: Water measurement unit. 'ml', 'fl oz', or 'cup'.
        :type unit: string, optional

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/water/{water-log-id}.json'.replace(
            '{water-log-id}', water_log_id)
        params = {}
        params['amount'] = amount
        if unit:
            params['unit'] = unit
        return self._post(endpoint, params=params, **kwargs)

    def get_favorite_foods(self, **kwargs):
        '''Get Favorite Foods

        Returns a list of a user's favorite foods in the format requested. A favorite food in the list provides a quick way to log the food via the Log Food endpoint.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/favorite.json'

        return self._get(endpoint, **kwargs)

    def get_frequent_foods(self, **kwargs):
        '''Get Frequent Foods

        Returns a list of a user's frequent foods in the format requested. A frequent food in the list provides a quick way to log the food via the Log Food endpoint.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/frequent.json'

        return self._get(endpoint, **kwargs)

    def add_favorite_food(self, food_id, **kwargs):
        '''Add Favorite Food

        Updates a user's daily activity goals and returns a response using units in the unit system which corresponds to the Accept-Language header provided.

        :param food_id: The ID of the food to be added to user's favorites.
        :type food_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/favorite/{food-id}.json'.replace(
            '{food-id}', food_id)

        return self._post(endpoint, **kwargs)

    def delete_favorite_food(self, food_id, **kwargs):
        '''Delete Favorite Food

        Deletes a food with the given ID to the user's list of favorite foods.

        :param food_id: The ID of the food to be deleted from user's favorites.
        :type food_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/favorite/{food-id}.json'.replace(
            '{food-id}', food_id)

        return self._delete(endpoint, **kwargs)

    def get_meals(self, **kwargs):
        '''Get Meals

        Returns a list of meals created by user in the user's food log in the format requested. User creates and manages meals on the Food Log tab on the website.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/meals.json'

        return self._get(endpoint, **kwargs)

    def add_meal(self, name, description, food_id, unit_id, amount, **kwargs):
        '''Create Meal

        Creates a meal with the given food contained in the post body.

        :param name: Name of the meal.
        :type name: string
        :param description: Short description of the meal.
        :type description: string
        :param food_id: ID of the food to be included in the meal.
        :type food_id: string
        :param unit_id: ID of units used. Typically retrieved via a previous call to Get Food Logs, Search Foods, or Get Food Units.
        :type unit_id: string
        :param amount: Amount consumed; in the format X.XX, in the specified unitId.
        :type amount: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/meals.json'
        params = {}
        params['name'] = name
        params['Description'] = description
        params['foodId'] = food_id
        params['unitId'] = unit_id
        params['amount'] = amount
        return self._post(endpoint, params=params, **kwargs)

    def update_meal(
            self,
            meal_id,
            name,
            description,
            food_id,
            unit_id,
            amount,
            **kwargs):
        '''Edit Meal

        Replaces an existing meal with the contents of the request. The response contains the updated meal.

        :param meal_id: Id of the meal to edit.
        :type meal_id: string
        :param name: Name of the meal.
        :type name: string
        :param description: Short description of the meal.
        :type description: string
        :param food_id: ID of the food to be included in the meal.
        :type food_id: string
        :param unit_id: ID of units used. Typically retrieved via a previous call to Get Food Logs, Search Foods, or Get Food Units.
        :type unit_id: string
        :param amount: Amount consumed; in the format X.XX, in the specified unitId.
        :type amount: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/meals/{meal-id}.json'.replace(
            '{meal-id}', meal_id)
        params = {}
        params['name'] = name
        params['Description'] = description
        params['foodId'] = food_id
        params['unitId'] = unit_id
        params['amount'] = amount
        return self._post(endpoint, params=params, **kwargs)

    def delete_meal(self, meal_id, **kwargs):
        '''Delete Meal

        Deletes a user's meal with the given meal id.

        :param meal_id: Id of the meal to delete.
        :type meal_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/meals/{meal-id}.json'.replace(
            '{meal-id}', meal_id)

        return self._delete(endpoint, **kwargs)

    def get_recent_foods(self, **kwargs):
        '''Get Recent Foods

        Returns a list of a user's frequent foods in the format requested. A frequent food in the list provides a quick way to log the food via the Log Food endpoint.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/log/recent.json'

        return self._get(endpoint, **kwargs)

    def add_foods(
            self,
            name,
            default_food_measurement_unit_id,
            default_serving_size,
            calories,
            form_type=None,
            description=None,
            **kwargs):
        '''Create Food

        Creates a new private food for a user and returns a response in the format requested. The created food is found via the Search Foods call.

        :param name: The food name.
        :type name: string
        :param default_food_measurement_unit_id: The ID of the default measurement unit. Full list of units can be retrieved via the Get Food Units endpoint.
        :type default_food_measurement_unit_id: string
        :param default_serving_size: The size of the default serving. Nutrition values should be provided for this serving size.
        :type default_serving_size: string
        :param calories: The calories in the default serving size.
        :type calories: string
        :param form_type: Form type; LIQUID or DRY.
        :type form_type: string, optional
        :param description: The description of the food.
        :type description: string, optional

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods.json'
        params = {}
        params['name'] = name
        params['defaultFoodMeasurementUnitId'] = default_food_measurement_unit_id
        params['defaultServingSize'] = default_serving_size
        params['calories'] = calories
        if form_type:
            params['formType'] = form_type
        if description:
            params['description'] = description
        return self._post(endpoint, params=params, **kwargs)

    def delete_foods(self, food_id, **kwargs):
        '''Delete Custom Food

        Deletes custom food for a user and returns a response in the format requested.

        :param food_id: The ID of the food to be deleted.
        :type food_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/foods/{food-id}.json'.replace(
            '{food-id}', food_id)

        return self._delete(endpoint, **kwargs)

    def get_foods_info(self, food_id, **kwargs):
        '''Get Food

        Returns the details of a specific food in the Fitbit food databases or a private food that an authorized user has entered in the format requested.

        :param food_id: The ID of the food.
        :type food_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/foods/{food-id}.json'.replace('{food-id}', food_id)

        return self._get(endpoint, **kwargs)

    def get_foods_units(self, **kwargs):
        '''Get Food Units

        Returns a list of all valid Fitbit food units in the format requested.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/foods/units.json'

        return self._get(endpoint, **kwargs)

    def get_foods_list(self, query, **kwargs):
        '''Search Foods

        Returns a list of public foods from the Fitbit food database and private food the user created in the format requested.

        :param query: The URL-encoded search query.
        :type query: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/foods/search.json'
        params = {}
        params['query'] = query
        return self._get(endpoint, params=params, **kwargs)

    def get_friends(self, **kwargs):
        '''Get Friends

        Returns data of a user's friends in the format requested using units in the unit system which corresponds to the Accept-Language header provided.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1.1/user/-/friends.json'

        return self._get(endpoint, **kwargs)

    def get_friends_leaderboard(self, **kwargs):
        '''Get Friends Leaderboard

        Returns data of a user's friends in the format requested using units in the unit system which corresponds to the Accept-Language header provided.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1.1/user/-/leaderboard/friends.json'

        return self._get(endpoint, **kwargs)

    def get_friends_invitations(self, **kwargs):
        '''Get Friend Invitations

        Returns a list of invitations to become friends with a user in the format requested.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1.1/user/-/friends/invitations.json'

        return self._get(endpoint, **kwargs)

    def create_friends_invitations(
            self,
            invited_user_email=None,
            invited_user_id=None,
            **kwargs):
        '''Invite Friends

        Creates an invitation to become friends with the authorized user.  Either invitedUserEmail or invitedUserId needs to be provided.

        :param invited_user_email: Email of the user to invite.
        :type invited_user_email: string, optional
        :param invited_user_id: Encoded ID of the user to invite.
        :type invited_user_id: string, optional

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1.1/user/-/friends/invitations'
        params = {}
        if invited_user_email:
            params['invitedUserEmail'] = invited_user_email
        if invited_user_id:
            params['invitedUserId'] = invited_user_id
        return self._post(endpoint, params=params, **kwargs)

    def respond_friends_invitation(self, from_user_id, accept, **kwargs):
        '''Respond to Friend Invitation

        Accepts or rejects an invitation to become friends wit inviting user.

        :param from_user_id: The encoded ID of a user from which to accept or reject invitation.
        :type from_user_id: string
        :param accept: Accept or reject invitation; true or false.
        :type accept: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1.1/user/-/friends/invitations/{from-user-id}'.replace(
            '{from-user-id}', from_user_id)
        params = {}
        params['accept'] = accept
        return self._post(endpoint, params=params, **kwargs)

    def get_heart_by_date_period(self, date, period, **kwargs):
        '''Get Heart Rate Time Series

        Returns the time series data in the specified range for a given resource in the format requested using units in the unit systems that corresponds to the Accept-Language header provided.

        :param date: A datetime object.
        :type date: datetime
        :param period: The range of which data will be returned. Options are 1d, 7d, 30d, 1w, and 1m.
        :type period: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/heart/date/{date}/{period}.json'.replace(
            '{date}', date).replace('{period}', period)

        return self._get(endpoint, **kwargs)

    def get_heart_by_date_range(self, base_date, end_date, **kwargs):
        '''Get Heart Rate Time Series

        Returns the time series data in the specified range for a given resource in the format requested using units in the unit systems that corresponds to the Accept-Language header provided.

        :param base_date: A datetime object.
        :type base_date: datetime
        :param end_date: A datetime object.
        :type end_date: datetime

        '''
        if not isinstance(end_date, datetime):
            raise ValueError(
                'Argument \'end_date\' must be a datetime object.')
        end_date = end_date.strftime('%Y-%m-%d') if end_date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/heart/date/{base-date}/{end-date}.json'.replace(
            '{base-date}', base_date).replace('{end-date}', end_date)

        return self._get(endpoint, **kwargs)

    def get_heart_by_date_range_intraday(
            self, date, end_date, detail_level, **kwargs):
        '''Get Heart Rate Intraday Time Series

        Returns the intraday time series for a given resource in the format requested. If your application has the appropriate access, your calls to a time series endpoint for a specific day (by using start and end dates on the same day or a period of 1d), the response will include extended intraday values with a one-minute detail level for that day. Unlike other time series calls that allow fetching data of other users, intraday data is available only for and to the authorized user.

        :param date: A datetime object.
        :type date: datetime
        :param end_date: A datetime object.
        :type end_date: datetime
        :param detail_level: The number of data points to include either 1sec or 1min.
        :type detail_level: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        if not isinstance(end_date, datetime):
            raise ValueError(
                'Argument \'end_date\' must be a datetime object.')
        end_date = end_date.strftime('%Y-%m-%d') if end_date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/heart/date/{date}/{end-date}/{detail-level}.json'.replace(
            '{date}', date).replace('{end-date}', end_date).replace('{detail-level}', detail_level)

        return self._get(endpoint, **kwargs)

    def get_heart_by_date_range_timestamp_intraday(
            self,
            date,
            end_date,
            detail_level,
            start_time,
            end_time,
            **kwargs):
        '''Get Heart Rate Intraday Time Series

        Returns the intraday time series for a given resource in the format requested. If your application has the appropriate access, your calls to a time series endpoint for a specific day (by using start and end dates on the same day or a period of 1d), the response will include extended intraday values with a one-minute detail level for that day. Unlike other time series calls that allow fetching data of other users, intraday data is available only for and to the authorized user.

        :param date: A datetime object.
        :type date: datetime
        :param end_date: A datetime object.
        :type end_date: datetime
        :param detail_level: The number of data points to include either 1sec or 1min.
        :type detail_level: string
        :param start_time: The start of the period in the format of HH:mm.
        :type start_time: string
        :param end_time: The end time of the period in the format of HH:mm.
        :type end_time: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        if not isinstance(end_date, datetime):
            raise ValueError(
                'Argument \'end_date\' must be a datetime object.')
        end_date = end_date.strftime('%Y-%m-%d') if end_date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/heart/date/{date}/{end-date}/{detail-level}/time/{start-time}/{end-time}.json'.replace(
            '{date}',
            date).replace(
            '{end-date}',
            end_date).replace(
            '{detail-level}',
            detail_level).replace(
                '{start-time}',
                start_time).replace(
                    '{end-time}',
            end_time)

        return self._get(endpoint, **kwargs)

    def get_heart_by_date_intraday(self, date, detail_level, **kwargs):
        '''Get Heart Rate Intraday Time Series

        Returns the intraday time series for a given resource in the format requested. If your application has the appropriate access, your calls to a time series endpoint for a specific day (by using start and end dates on the same day or a period of 1d), the response will include extended intraday values with a one-minute detail level for that day. Unlike other time series calls that allow fetching data of other users, intraday data is available only for and to the authorized user.

        :param date: A datetime object.
        :type date: datetime
        :param detail_level: The number of data points to include either 1sec or 1min.
        :type detail_level: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/heart/date/{date}/1d/{detail-level}.json'.replace(
            '{date}', date).replace('{detail-level}', detail_level)

        return self._get(endpoint, **kwargs)

    def get_heart_by_date_timestamp_intraday(
            self, date, detail_level, start_time, end_time, **kwargs):
        '''Get Heart Rate Intraday Time Series

        Returns the intraday time series for a given resource in the format requested. If your application has the appropriate access, your calls to a time series endpoint for a specific day (by using start and end dates on the same day or a period of 1d), the response will include extended intraday values with a one-minute detail level for that day. Unlike other time series calls that allow fetching data of other users, intraday data is available only for and to the authorized user.

        :param date: A datetime object.
        :type date: datetime
        :param detail_level: The number of data points to include either 1sec or 1min.
        :type detail_level: string
        :param start_time: The start of the period in the format of HH:mm.
        :type start_time: string
        :param end_time: The end time of the period in the format of HH:mm.
        :type end_time: string

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/activities/heart/date/{date}/1d/{detail-level}/time/{start-time}/{end-time}.json'.replace(
            '{date}',
            date).replace(
            '{detail-level}',
            detail_level).replace(
            '{start-time}',
            start_time).replace(
                '{end-time}',
            end_time)

        return self._get(endpoint, **kwargs)

    def delete_sleep(self, log_id, **kwargs):
        '''Delete Sleep Log

        Deletes a user's sleep log entry with the given ID.

        :param log_id: The ID of the sleep log to be deleted.
        :type log_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1.2/user/-/sleep/{log-id}.json'.replace(
            '{log-id}', log_id)

        return self._delete(endpoint, **kwargs)

    def get_sleep_by_date(self, date, **kwargs):
        '''Get Sleep Log

        The Get Sleep Logs by Date endpoint returns a summary and list of a user's sleep log entries (including naps) as well as detailed sleep entry data for a given day.

        :param date: A datetime object.
        :type date: datetime

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1.2/user/-/sleep/date/{date}.json'.replace('{date}', date)

        return self._get(endpoint, **kwargs)

    def get_sleep_by_date_range(self, base_date, end_date, **kwargs):
        '''Get Sleep Logs by Date Range

        The Get Sleep Logs by Date Range endpoint returns a list of a user's sleep log entries (including naps) as well as detailed sleep entry data for a given date range (inclusive of start and end dates).

        :param base_date: A datetime object.
        :type base_date: datetime
        :param end_date: A datetime object.
        :type end_date: datetime

        '''
        if not isinstance(base_date, datetime):
            raise ValueError(
                'Argument \'base_date\' must be a datetime object.')
        base_date = base_date.strftime('%Y-%m-%d') if base_date else ''

        if not isinstance(end_date, datetime):
            raise ValueError(
                'Argument \'end_date\' must be a datetime object.')
        end_date = end_date.strftime('%Y-%m-%d') if end_date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1.2/user/-/sleep/date/{base-date}/{end-date}.json'.replace(
            '{base-date}', base_date).replace('{end-date}', end_date)

        return self._get(endpoint, **kwargs)

    def get_sleep_list(
            self,
            sort,
            offset,
            limit,
            before_date=None,
            after_date=None,
            **kwargs):
        '''Get Sleep Logs List

        The Get Sleep Logs List endpoint returns a list of a user's sleep logs (including naps) before or after a given day with offset, limit, and sort order.

        :param sort: The sort order of entries by date asc (ascending) or desc (descending).
        :type sort: string
        :param offset: The offset number of entries.
        :type offset: int
        :param limit: The maximum number of entries returned (maximum;100).
        :type limit: int
        :param before_date: A datetime object.
        :type before_date: datetime, optional
        :param after_date: A datetime object.
        :type after_date: datetime, optional

        '''
        if before_date and not isinstance(before_date, datetime):
            raise ValueError(
                'Argument \'before_date\' must be a datetime object.')
        before_date = before_date.strftime('%Y-%m-%d') if before_date else ''

        if after_date and not isinstance(after_date, datetime):
            raise ValueError(
                'Argument \'after_date\' must be a datetime object.')
        after_date = after_date.strftime('%Y-%m-%d') if after_date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1.2/user/-/sleep/list.json'
        params = {}
        if before_date:
            params['beforeDate'] = before_date
        if after_date:
            params['afterDate'] = after_date
        params['sort'] = sort
        params['offset'] = offset
        params['limit'] = limit
        return self._get(endpoint, params=params, **kwargs)

    def get_sleep_goal(self, **kwargs):
        '''Get Sleep Goal

        Returns the user's sleep goal.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1.2/user/-/sleep/goal.json'

        return self._get(endpoint, **kwargs)

    def update_sleep_goal(self, min_duration, **kwargs):
        '''Update Sleep Goal

        Create or update the user's sleep goal and get a response in the JSON format.

        :param min_duration: Duration of sleep goal.
        :type min_duration: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1.2/user/-/sleep/goal.json'
        params = {}
        params['minDuration'] = min_duration
        return self._post(endpoint, params=params, **kwargs)

    def add_sleep(self, start_time, duration, date, **kwargs):
        '''Log Sleep

        Creates a log entry for a sleep event and returns a response in the format requested.

        :param start_time: Start time includes hours and minutes in the format HH:mm.
        :type start_time: string
        :param duration: Duration in milliseconds.
        :type duration: int
        :param date: A datetime object.
        :type date: datetime

        '''
        if not isinstance(date, datetime):
            raise ValueError('Argument \'date\' must be a datetime object.')
        date = date.strftime('%Y-%m-%d') if date else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1.2/user/-/sleep.json'
        params = {}
        params['startTime'] = start_time
        params['duration'] = duration
        params['date'] = date
        return self._post(endpoint, params=params, **kwargs)

    def get_subscriptions_list(self, collection_path, **kwargs):
        '''Get a List of Subscriptions

        Retreives a list of a user's subscriptions for your application in the format requested. You can either fetch subscriptions for a specific collection or the entire list of subscriptions for the user. For best practice, make sure that your application maintains this list on your side and use this endpoint only to periodically ensure data consistency.

        :param collection_path: This is the resource of the collection to receive notifications from (foods, activities, sleep, or body). If not present, subscription will be created for all collections. If you have both all and specific collection subscriptions, you will get duplicate notifications on that collections' updates. Each subscriber can have only one subscription for a specific user's collection.
        :type collection_path: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/{collection-path}/apiSubscriptions.json'.replace(
            '{collection-path}', collection_path)

        return self._get(endpoint, **kwargs)

    def add_subscriptions(self, collection_path, subscription_id, **kwargs):
        '''Add a Subscription

        Adds a subscription in your application so that users can get notifications and return a response in the format requested. The subscription-id value provides a way to associate an update with a particular user stream in your application.

        :param collection_path: This is the resource of the collection to receive notifications from (foods, activities, sleep, or body). If not present, subscription will be created for all collections. If you have both all and specific collection subscriptions, you will get duplicate notifications on that collections' updates. Each subscriber can have only one subscription for a specific user's collection.
        :type collection_path: string
        :param subscription_id: This is the unique ID of the subscription created by the API client application. Each ID must be unique across the entire set of subscribers and collections. The Fitbit servers will pass this ID back along with any notifications about the user indicated by the user parameter in the URL path.
        :type subscription_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/{collection-path}/apiSubscriptions/{subscription-id}.json'.replace(
            '{collection-path}', collection_path).replace('{subscription-id}', subscription_id)

        return self._post(endpoint, **kwargs)

    def delete_subscriptions(self, collection_path, subscription_id, **kwargs):
        '''Delete a Subscription

        Deletes a subscription for a user..

        :param collection_path: This is the resource of the collection to receive notifications from (foods, activities, sleep, or body). If not present, subscription will be created for all collections. If you have both all and specific collection subscriptions, you will get duplicate notifications on that collections' updates. Each subscriber can have only one subscription for a specific user's collection.
        :type collection_path: string
        :param subscription_id: This is the resource of the collection to receive notifications from (foods, activities, sleep, or body). If not present, subscription will be created for all collections. If you have both all and specific collection subscriptions, you will get duplicate notifications on that collections' updates. Each subscriber can have only one subscription for a specific user's collection.
        :type subscription_id: string

        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/{collection-path}/apiSubscriptions/{subscription-id}.json'.replace(
            '{collection-path}', collection_path).replace('{subscription-id}', subscription_id)

        return self._delete(endpoint, **kwargs)

    def get_badges(self, **kwargs):
        '''Get Badges

        Retrieves the user's badges in the format requested. Response includes all badges for the user as seen on the Fitbit website badge locker (both activity and weight related.) The endpoint returns weight and distance badges based on the user's unit profile preference as on the website.


        '''
        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/badges.json'

        return self._get(endpoint, **kwargs)

    def get_profile(self, **kwargs):
        '''Get Profile

        Returns a user's profile. The authenticated owner receives all values. However, the authenticated user's access to other users' data is subject to those users' privacy settings. Numerical values are returned in the unit system specified in the Accept-Language header.


        '''
        required_scope = set(['location', 'profile', 'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/profile.json'

        return self._get(endpoint, **kwargs)

    def update_profile(
            self,
            gender=None,
            birthday=None,
            height=None,
            about_me=None,
            fullname=None,
            country=None,
            state=None,
            city=None,
            stride_length_walking=None,
            stride_length_running=None,
            weight_unit=None,
            height_unit=None,
            water_unit=None,
            glucose_unit=None,
            timezone=None,
            foods_locale=None,
            locale=None,
            locale_lang=None,
            locale_country=None,
            start_day_of_week=None,
            **kwargs):
        '''Update Profile

        Updates a user's profile using a form.

        :param gender: The sex of the user; (MALE/FEMALE/NA).
        :type gender: string, optional
        :param birthday: A datetime object.
        :type birthday: datetime, optional
        :param height: The height in the format X.XX in the unit system that corresponds to the Accept-Language header provided.
        :type height: string, optional
        :param about_me: This is a short description of user.
        :type about_me: string, optional
        :param fullname: The fullname of the user.
        :type fullname: string, optional
        :param country: The country of the user's residence. This is a two-character code.
        :type country: string, optional
        :param state: The US state of the user's residence. This is a two-character code if the country was or is set to US.
        :type state: string, optional
        :param city: The US city of the user's residence.
        :type city: string, optional
        :param stride_length_walking: Walking stride length in the format X.XX, where it is in the unit system that corresponds to the Accept-Language header provided.
        :type stride_length_walking: string, optional
        :param stride_length_running: Running stride length in the format X.XX, where it is in the unit system that corresponds to the Accept-Language header provided.
        :type stride_length_running: string, optional
        :param weight_unit: Default weight unit on website (which doesn't affect API); one of (en_US, en_GB, 'any' for METRIC).
        :type weight_unit: string, optional
        :param height_unit: Default height/distance unit on website (which doesn't affect API); one of (en_US, en_GB, 'any' for METRIC).
        :type height_unit: string, optional
        :param water_unit: Default water unit on website (which doesn't affect API); one of (en_US, en_GB, 'any' for METRIC).
        :type water_unit: string, optional
        :param glucose_unit: Default glucose unit on website (which doesn't affect API); one of (en_US, en_GB, 'any' for METRIC).
        :type glucose_unit: string, optional
        :param timezone: The timezone in the format 'America/Los_Angeles'.
        :type timezone: string, optional
        :param foods_locale: The food database locale in the format of xx.XX.
        :type foods_locale: string, optional
        :param locale: The locale of the website (country/language); one of the locales, currently – (en_US, fr_FR, de_DE, es_ES, en_GB, en_AU, en_NZ, ja_JP).
        :type locale: string, optional
        :param locale_lang: The Language in the format 'xx'. You should specify either locale or both - localeLang and localeCountry (locale is higher priority).
        :type locale_lang: string, optional
        :param locale_country: The Country in the format 'xx'. You should specify either locale or both - localeLang and localeCountry (locale is higher priority).
        :type locale_country: string, optional
        :param start_day_of_week: The Start day of the week, meaning what day the week should start on. Either Sunday or Monday.
        :type start_day_of_week: string, optional

        '''
        if birthday and not isinstance(birthday, datetime):
            raise ValueError(
                'Argument \'birthday\' must be a datetime object.')
        birthday = birthday.strftime('%Y-%m-%d') if birthday else ''

        required_scope = set(['activity',
                              'heartrate',
                              'location',
                              'nutrition',
                              'profile',
                              'settings',
                              'sleep',
                              'social',
                              'weight'])
        if not all(scope in self.session.scope for scope in required_scope):
            missing_scope = [
                scope for scope in required_scope if scope not in self.session.scope]
            raise InsufficientScope(
                'This application needs additional scope {missing_scope} for this request.'.format(
                    missing_scope=missing_scope))

        endpoint = '/1/user/-/profile.json'

        return self._post(endpoint, **kwargs)
