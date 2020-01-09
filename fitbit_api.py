from datetime import datetime
from requests_oauthlib import OAuth2Session

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

class FitbitException(Exception):
	pass

class InsufficientScope(FitbitException):
	pass

class RateLimitException(FitbitException):
	def __init__(self, retry_after, *args, **kwargs):
		self.retry_after = retry_after
		super().__init__(*args, **kwargs)

class FitbitClient:
	OAuth2Session = OAuth2Session
	authorization_endpoint_url = 'https://www.fitbit.com/oauth2/authorize'

	def __init__(self, session):
		self.session = session

	@classmethod
	def create_using_token(cls, token, client_id, callback_uri, scope=None, new_token_callback=None):
		scope = scope or ALL_SCOPES
		session = cls.OAuth2Session(
			client_id=client_id,
			redirect_uri=callback_uri,
			scope=scope,
			token=token,
			token_updater=new_token_callback,
		)
		return cls(session)

	@classmethod
	def OAuth2_step_one(cls, client_id, callback_uri, scope=None):
		scope = scope or ALL_SCOPES
		session = cls.OAuth2Session(client_id=client_id, redirect_uri=callback_uri, scope=scope)
		authorization_url, state = session.authorization_url(cls.authorization_endpoint_url)
		return authorization_url

	@classmethod
	def OAuth2_step_two(cls, client_id, client_secret, callback_uri, redirect_uri, scope=None, new_token_callback=None):
		scope = scope or ALL_SCOPES
		session = cls.OAuth2Session(
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
		new_token_callback(token)
		return cls(session)

	def request(self, method, endpoint, params=None, full_response=False):
		url = 'https://api.fitbit.com'+endpoint
		params = params or {}
		response = self.session.request(method, url, params=params)
		if full_response:
			return response
		if response.ok:
			return response.json()
		elif response.status_code == 429:
			raise RateLimitException(retry_after=response.headers['Retry-After'])

	def get(self, endpoint, params=None, **kwargs):
		return self.request('get', endpoint, params, **kwargs)

	def post(self, endpoint, params=None, **kwargs):
		return self.request('post', endpoint, params, **kwargs)

	def delete(self, endpoint, params=None, **kwargs):
		return self.request('delete', endpoint, params, **kwargs)

	def put(self, endpoint, params=None, **kwargs):
		return self.request('put', endpoint, params, **kwargs)


	def get_activities_by_date(self, date, **kwargs):
		'''Get Activity Summary by Date 

		Retrieves a summary and list of a user's activities and activity log entries for a given day.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/date/{date}.json'.replace('{date}', date)

		return self.get(endpoint, **kwargs)

	def get_activities_resource_by_date_range(self, resource_path, base_date, end_date, **kwargs):
		'''Get Activity Resource by Date Range

		Returns activities time series data in the specified range for a given resource.
		'''
		if not isinstance(base_date, datetime):
			raise ValueError('Argument \'base_date\' must be a datetime object.')
		base_date = base_date.strftime('%Y-%m-%d') if base_date else ''
	
		if not isinstance(end_date, datetime):
			raise ValueError('Argument \'end_date\' must be a datetime object.')
		end_date = end_date.strftime('%Y-%m-%d') if end_date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/{resource-path}/date/{base-date}/{end-date}.json'.replace('{resource-path}', resource_path).replace('{base-date}', base_date).replace('{end-date}', end_date)

		return self.get(endpoint, **kwargs)

	def get_activities_tracker_resource_by_date_range(self, resource_path, base_date, end_date, **kwargs):
		'''Get Activity Tracker Resource by Date Range Time Series

		Returns time series data in the specified range for a given resource.
		'''
		if not isinstance(base_date, datetime):
			raise ValueError('Argument \'base_date\' must be a datetime object.')
		base_date = base_date.strftime('%Y-%m-%d') if base_date else ''
	
		if not isinstance(end_date, datetime):
			raise ValueError('Argument \'end_date\' must be a datetime object.')
		end_date = end_date.strftime('%Y-%m-%d') if end_date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/tracker/{resource-path}/date/{base-date}/{end-date}.json'.replace('{resource-path}', resource_path).replace('{base-date}', base_date).replace('{end-date}', end_date)

		return self.get(endpoint, **kwargs)

	def get_activities_resource_by_date_period(self, resource_path, date, period, **kwargs):
		'''Get Activity Time Series

		Returns time series data in the specified range for a given resource in the format requested using units in the unit system that corresponds to the Accept-Language header provided.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/{resource-path}/date/{date}/{period}.json'.replace('{resource-path}', resource_path).replace('{date}', date).replace('{period}', period)

		return self.get(endpoint, **kwargs)

	def get_activities_tracker_resource_by_date_period(self, resource_path, date, period, **kwargs):
		'''Get Activity Time Series

		Returns time series data in the specified range for a given resource in the format requested using units in the unit system that corresponds to the Accept-Language header provided.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/tracker/{resource-path}/date/{date}/{period}.json'.replace('{resource-path}', resource_path).replace('{date}', date).replace('{period}', period)

		return self.get(endpoint, **kwargs)

	def get_activities_resource_by_date_range_intraday(self, resource_path, base_date, end_date, detail_level, **kwargs):
		'''Get Activity Intraday Time Series

		Returns the Activity Intraday Time Series for a given resource in the format requested.
		'''
		if not isinstance(base_date, datetime):
			raise ValueError('Argument \'base_date\' must be a datetime object.')
		base_date = base_date.strftime('%Y-%m-%d') if base_date else ''
	
		if not isinstance(end_date, datetime):
			raise ValueError('Argument \'end_date\' must be a datetime object.')
		end_date = end_date.strftime('%Y-%m-%d') if end_date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/{resource-path}/date/{base-date}/{end-date}/{detail-level}.json'.replace('{resource-path}', resource_path).replace('{base-date}', base_date).replace('{end-date}', end_date).replace('{detail-level}', detail_level)

		return self.get(endpoint, **kwargs)

	def get_activities_resource_by_date_intraday(self, resource_path, date, detail_level, **kwargs):
		'''Get Intraday Time Series

		Returns the Intraday Time Series for a given resource in the format requested.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/{resource-path}/date/{date}/1d/{detail-level}.json'.replace('{resource-path}', resource_path).replace('{date}', date).replace('{detail-level}', detail_level)

		return self.get(endpoint, **kwargs)

	def get_activities_resource_by_date_range_time_series_intraday(self, resource_path, date, end_date, detail_level, start_time, end_time, **kwargs):
		'''Get Activity Intraday Time Series

		Returns the Intraday Time Series for a given resource in the format requested.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		if not isinstance(end_date, datetime):
			raise ValueError('Argument \'end_date\' must be a datetime object.')
		end_date = end_date.strftime('%Y-%m-%d') if end_date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/{resource-path}/date/{date}/{end-date}/{detail-level}/time/{start-time}/{end-time}.json'.replace('{resource-path}', resource_path).replace('{date}', date).replace('{end-date}', end_date).replace('{detail-level}', detail_level).replace('{start-time}', start_time).replace('{end-time}', end_time)

		return self.get(endpoint, **kwargs)

	def get_activities_resource_by_date_time_series_intraday(self, resource_path, date, detail_level, start_time, end_time, **kwargs):
		'''Get Intraday Time Series

		Returns the Intraday Time Series for a given resource in the format requested.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/{resource-path}/date/{date}/1d/{detail-level}/time/{start-time}/{end-time}.json'.replace('{resource-path}', resource_path).replace('{date}', date).replace('{detail-level}', detail_level).replace('{start-time}', start_time).replace('{end-time}', end_time)

		return self.get(endpoint, **kwargs)

	def add_activities_log(self, activityId, manualCalories, startTime, durationMillis, date, distance, activityName=None, distanceUnit=None, **kwargs):
		'''Log Activity

		The Log Activity endpoint creates log entry for an activity or user's private custom activity using units in the unit system which corresponds to the Accept-Language header provided (or using optional custom distanceUnit) and get a response in the format requested.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities.json'
		params = {}
		params['activityId'] = activityId
		if activityName:
			params['activityName'] = activityName
		params['manualCalories'] = manualCalories
		params['startTime'] = startTime
		params['durationMillis'] = durationMillis
		params['date'] = date
		params['distance'] = distance
		if distanceUnit:
			params['distanceUnit'] = distanceUnit
		return self.post(endpoint, params=params, **kwargs)

	def get_activities_log(self, **kwargs):
		'''Get Lifetime Stats

		Updates a user's daily activity goals and returns a response using units in the unit system which corresponds to the Accept-Language header provided.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities.json'

		return self.get(endpoint, **kwargs)

	def delete_activities_log(self, activity_log_id, **kwargs):
		'''Delete Activity Log

		Deletes a user's activity log entry with the given ID.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/{activity-log-id}.json'.replace('{activity-log-id}', activity_log_id)

		return self.delete(endpoint, **kwargs)

	def get_activities_log_list(self, sort, offset, limit, beforeDate=None, afterDate=None, **kwargs):
		'''Get Activity Log List

		Retreives a list of user's activity log entries before or after a given day with offset and limit using units in the unit system which corresponds to the Accept-Language header provided.
		'''
		if beforeDate and not isinstance(beforeDate, datetime):
			raise ValueError('Argument \'beforeDate\' must be a datetime object.')
		beforeDate = beforeDate.strftime('%Y-%m-%d') if beforeDate else ''
	
		if afterDate and not isinstance(afterDate, datetime):
			raise ValueError('Argument \'afterDate\' must be a datetime object.')
		afterDate = afterDate.strftime('%Y-%m-%d') if afterDate else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/list.json'
		params = {}
		if beforeDate:
			params['beforeDate'] = beforeDate
		if afterDate:
			params['afterDate'] = afterDate
		params['sort'] = sort
		params['offset'] = offset
		params['limit'] = limit
		return self.get(endpoint, params=params, **kwargs)

	def get_activities_t_c_x(self, log_id, includePartialTCX=None, **kwargs):
		'''Get Activity TCX

		Retreives the details of a user's location and heart rate data during a logged exercise activity.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/{log-id}.tcx'.replace('{log-id}', log_id)
		params = {}
		if includePartialTCX:
			params['includePartialTCX'] = includePartialTCX
		return self.get(endpoint, params=params, **kwargs)

	def get_activities_types(self, **kwargs):
		'''Browse Activity Types

		Retreives a tree of all valid Fitbit public activities from the activities catelog as well as private custom activities the user created in the format requested.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/activities.json'

		return self.get(endpoint, **kwargs)

	def get_activities_type_detail(self, activity_id, **kwargs):
		'''Get Activity Type

		Returns the detail of a specific activity in the Fitbit activities database in the format requested. If activity has levels, it also returns a list of activity level details.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/activities/{activity-id}.json'.replace('{activity-id}', activity_id)

		return self.get(endpoint, **kwargs)

	def get_frequent_activities(self, **kwargs):
		'''Get Frequent Activities

		Retreives a list of a user's frequent activities in the format requested using units in the unit system which corresponds to the Accept-Language header provided.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/frequent.json'

		return self.get(endpoint, **kwargs)

	def get_recent_activities(self, **kwargs):
		'''Get Recent Activity Types

		Retreives a list of a user's recent activities types logged with some details of the last activity log of that type using units in the unit system which corresponds to the Accept-Language header provided.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/recent.json'

		return self.get(endpoint, **kwargs)

	def get_favorite_activities(self, **kwargs):
		'''Get Favorite Activities

		Returns a list of a user's favorite activities.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/favorite.json'

		return self.get(endpoint, **kwargs)

	def delete_favorite_activities(self, activity_id, **kwargs):
		'''Delete Favorite Activity

		Removes the activity with the given ID from a user's list of favorite activities.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/favorite/{activity-id}.json'.replace('{activity-id}', activity_id)

		return self.delete(endpoint, **kwargs)

	def add_favorite_activities(self, activity_id, **kwargs):
		'''Add Favorite Activity

		Adds the activity with the given ID to user's list of favorite activities.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/favorite/{activity-id}.json'.replace('{activity-id}', activity_id)

		return self.post(endpoint, **kwargs)

	def get_activities_goals(self, period, **kwargs):
		'''Get Activity Goals

		Retreives a user's current daily or weekly activity goals using measurement units as defined in the unit system, which corresponds to the Accept-Language header provided.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/goals/{period}.json'.replace('{period}', period)

		return self.get(endpoint, **kwargs)

	def add_update_activities_goals(self, period, type, value, **kwargs):
		'''Update Activity Goals

		Updates a user's daily or weekly activity goals and returns a response using units in the unit system which corresponds to the Accept-Language header provided.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/goals/{period}.json'.replace('{period}', period)
		params = {}
		params['type'] = type
		params['value'] = value
		return self.post(endpoint, params=params, **kwargs)

	def get_body_fat_by_date(self, date, **kwargs):
		'''Get Body Fat Logs

		Retreives a list of all user's body fat log entries for a given day in the format requested.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/fat/date/{date}.json'.replace('{date}', date)

		return self.get(endpoint, **kwargs)

	def get_body_fat_by_date_period(self, date, period, **kwargs):
		'''Get Body Fat Logs

		Retreives a list of all user's body fat log entries for a given day in the format requested.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/fat/date/{date}/{period}.json'.replace('{date}', date).replace('{period}', period)

		return self.get(endpoint, **kwargs)

	def get_body_fat_by_date_range(self, base_date, end_date, **kwargs):
		'''Get Body Fat Logs

		Retreives a list of all user's body fat log entries for a given day in the format requested.
		'''
		if not isinstance(base_date, datetime):
			raise ValueError('Argument \'base_date\' must be a datetime object.')
		base_date = base_date.strftime('%Y-%m-%d') if base_date else ''
	
		if not isinstance(end_date, datetime):
			raise ValueError('Argument \'end_date\' must be a datetime object.')
		end_date = end_date.strftime('%Y-%m-%d') if end_date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/fat/date/{base-date}/{end-date}.json'.replace('{base-date}', base_date).replace('{end-date}', end_date)

		return self.get(endpoint, **kwargs)

	def add_body_fat_log(self, fat, date, time, **kwargs):
		'''Log Body Fat

		Creates a log entry for body fat and returns a response in the format requested.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/fat.json'
		params = {}
		params['fat'] = fat
		params['date'] = date
		params['time'] = time
		return self.post(endpoint, params=params, **kwargs)

	def delete_body_fat_log(self, body_fat_log_id, **kwargs):
		'''Delete Body Fat Log

		Deletes a user's body fat log entry with the given ID.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/fat/{body-fat-log-id}.json'.replace('{body-fat-log-id}', body_fat_log_id)

		return self.delete(endpoint, **kwargs)

	def get_body_resource_by_date_period(self, resource_path, date, period, **kwargs):
		'''Get Body Time Series

		Returns time series data in the specified range for a given resource in the format requested using units in the unit system that corresponds to the Accept-Language header provided.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/{resource-path}/date/{date}/{period}.json'.replace('{resource-path}', resource_path).replace('{date}', date).replace('{period}', period)

		return self.get(endpoint, **kwargs)

	def get_body_resource_by_date_range(self, resource_path, base_date, end_date, **kwargs):
		'''Get Body Time Series

		Returns time series data in the specified range for a given resource in the format requested using units in the unit system that corresponds to the Accept-Language header provided.
		'''
		if not isinstance(base_date, datetime):
			raise ValueError('Argument \'base_date\' must be a datetime object.')
		base_date = base_date.strftime('%Y-%m-%d') if base_date else ''
	
		if not isinstance(end_date, datetime):
			raise ValueError('Argument \'end_date\' must be a datetime object.')
		end_date = end_date.strftime('%Y-%m-%d') if end_date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/{resource-path}/date/{base-date}/{end-date}.json'.replace('{resource-path}', resource_path).replace('{base-date}', base_date).replace('{end-date}', end_date)

		return self.get(endpoint, **kwargs)

	def get_body_goals(self, goal_type, **kwargs):
		'''Get Body Goals

		Retreives a user's current body fat percentage or weight goal using units in the unit systems that corresponds to the Accept-Language header providedin the format requested.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/{goal-type}/goal.json'.replace('{goal-type}', goal_type)

		return self.get(endpoint, **kwargs)

	def update_body_fat_goal(self, fat, **kwargs):
		'''Update Body Fat Goal

		Updates user's fat percentage goal.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/fat/goal.json'
		params = {}
		params['fat'] = fat
		return self.post(endpoint, params=params, **kwargs)

	def update_weight_goal(self, startDate, startWeight, weight=None, **kwargs):
		'''Update Weight Goal

		Updates user's fat percentage goal.
		'''
		required_scope = set(['profile', 'heartrate', 'location'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/weight/goal.json'
		params = {}
		params['startDate'] = startDate
		params['startWeight'] = startWeight
		if weight:
			params['weight'] = weight
		return self.post(endpoint, params=params, **kwargs)

	def get_weight_by_date(self, date, **kwargs):
		'''Get Weight Logs

		Retreives a list of all user's body weight log entries for a given day using units in the unit systems which corresponds to the Accept-Language header provided.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/weight/date/{date}.json'.replace('{date}', date)

		return self.get(endpoint, **kwargs)

	def get_weight_by_date_period(self, date, period, **kwargs):
		'''Get Body Fat Logs

		Retreives a list of all user's body weight log entries for a given day in the format requested.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/weight/date/{date}/{period}.json'.replace('{date}', date).replace('{period}', period)

		return self.get(endpoint, **kwargs)

	def get_weight_by_date_range(self, base_date, end_date, **kwargs):
		'''Get Body Fat Logs

		Retreives a list of all user's body fat log entries for a given day in the format requested.
		'''
		if not isinstance(base_date, datetime):
			raise ValueError('Argument \'base_date\' must be a datetime object.')
		base_date = base_date.strftime('%Y-%m-%d') if base_date else ''
	
		if not isinstance(end_date, datetime):
			raise ValueError('Argument \'end_date\' must be a datetime object.')
		end_date = end_date.strftime('%Y-%m-%d') if end_date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/weight/date/{base-date}/{end-date}.json'.replace('{base-date}', base_date).replace('{end-date}', end_date)

		return self.get(endpoint, **kwargs)

	def add_weight_log(self, weight, date, time=None, **kwargs):
		'''Log Weight

		Creates log entry for a body weight using units in the unit systems that corresponds to the Accept-Language header provided and gets a response in the format requested.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/weight.json'
		params = {}
		params['weight'] = weight
		params['date'] = date
		if time:
			params['time'] = time
		return self.post(endpoint, params=params, **kwargs)

	def delete_weight_log(self, body_weight_log_id, **kwargs):
		'''Delete Weight Log

		Deletes a user's body weight log entrywith the given ID.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/body/log/weight/{body-weight-log-id}.json'.replace('{body-weight-log-id}', body_weight_log_id)

		return self.delete(endpoint, **kwargs)

	def get_devices(self, **kwargs):
		'''Get Devices

		Returns a list of the Fitbit devices connected to a user's account.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/devices.json'

		return self.get(endpoint, **kwargs)

	def get_alarms(self, tracker_id, **kwargs):
		'''Get Alarms

		Returns alarms for a device
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/devices/tracker/{tracker-id}/alarms.json'.replace('{tracker-id}', tracker_id)

		return self.get(endpoint, **kwargs)

	def add_alarms(self, tracker_id, time, enabled, recurring, weekDays, **kwargs):
		'''Add Alarm

		Adds the alarm settings to a given ID for a given device.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/devices/tracker/{tracker-id}/alarms.json'.replace('{tracker-id}', tracker_id)
		params = {}
		params['time'] = time
		params['enabled'] = enabled
		params['recurring'] = recurring
		params['weekDays'] = weekDays
		return self.post(endpoint, params=params, **kwargs)

	def update_alarms(self, tracker_id, alarm_id, time, enabled, recurring, weekDays, snoozeLength, snoozeCount, **kwargs):
		'''Update Alarm

		Updates the alarm entry with a given ID for a given device. It also gets a response in the format requested.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/devices/tracker/{tracker-id}/alarms/{alarm-id}.json'.replace('{tracker-id}', tracker_id).replace('{alarm-id}', alarm_id)
		params = {}
		params['time'] = time
		params['enabled'] = enabled
		params['recurring'] = recurring
		params['weekDays'] = weekDays
		params['snoozeLength'] = snoozeLength
		params['snoozeCount'] = snoozeCount
		return self.post(endpoint, params=params, **kwargs)

	def delete_alarms(self, tracker_id, alarm_id, **kwargs):
		'''Delete Alarm

		Deletes the user's device alarm entry with the given ID for a given device.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/devices/tracker/{tracker-id}/alarms/{alarm-id}.json'.replace('{tracker-id}', tracker_id).replace('{alarm-id}', alarm_id)

		return self.delete(endpoint, **kwargs)

	def get_foods_locales(self, **kwargs):
		'''Get Food Locales

		Returns the food locales that the user may choose to search, log, and create food in.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/foods/locales.json'

		return self.get(endpoint, **kwargs)

	def get_foods_goal(self, **kwargs):
		'''Get Food Goals

		Returns a user's current daily calorie consumption goal and/or foodPlan value in the format requested.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/goal.json'

		return self.get(endpoint, **kwargs)

	def add_update_foods_goal(self, calories, intensity=None, personalized=None, **kwargs):
		'''Update Food Goal

		Updates a user's daily calories consumption goal or food plan and returns a response in the format requested.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/goal.json'
		params = {}
		params['calories'] = calories
		if intensity:
			params['intensity'] = intensity
		if personalized:
			params['personalized'] = personalized
		return self.post(endpoint, params=params, **kwargs)

	def get_foods_by_date(self, date, **kwargs):
		'''Get Food Logs

		Retreives a summary and list of a user's food log entries for a given day in the format requested.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/date/{date}.json'.replace('{date}', date)

		return self.get(endpoint, **kwargs)

	def get_water_by_date(self, date, **kwargs):
		'''Get Water Logs

		Retreives a summary and list of a user's water log entries for a given day in the requested using units in the unit system that corresponds to the Accept-Language header provided.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/water/date/{date}.json'.replace('{date}', date)

		return self.get(endpoint, **kwargs)

	def get_water_goal(self, **kwargs):
		'''Get Water Goal

		Retreives a summary and list of a user's water goal entries for a given day in the requested using units in the unit system that corresponds to the Accept-Language header provided.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/water/goal.json'

		return self.get(endpoint, **kwargs)

	def add_update_water_goal(self, target, **kwargs):
		'''Update Water Goal

		Updates a user's daily calories consumption goal or food plan and returns a response in the format requested.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/water/goal.json'
		params = {}
		params['target'] = target
		return self.post(endpoint, params=params, **kwargs)

	def get_foods_by_date_range(self, resource_path, base_date, end_date, **kwargs):
		'''Get Food or Water Time Series

		Updates a user's daily activity goals and returns a response using units in the unit system which corresponds to the Accept-Language header provided.
		'''
		if not isinstance(base_date, datetime):
			raise ValueError('Argument \'base_date\' must be a datetime object.')
		base_date = base_date.strftime('%Y-%m-%d') if base_date else ''
	
		if not isinstance(end_date, datetime):
			raise ValueError('Argument \'end_date\' must be a datetime object.')
		end_date = end_date.strftime('%Y-%m-%d') if end_date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/{resource-path}/date/{base-date}/{end-date}.json'.replace('{resource-path}', resource_path).replace('{base-date}', base_date).replace('{end-date}', end_date)

		return self.get(endpoint, **kwargs)

	def get_foods_resource_by_date_period(self, resource_path, date, period, **kwargs):
		'''Get Food or Water Time Series

		Updates a user's daily activity goals and returns a response using units in the unit system which corresponds to the Accept-Language header provided.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/{resource-path}/date/{date}/{period}.json'.replace('{resource-path}', resource_path).replace('{date}', date).replace('{period}', period)

		return self.get(endpoint, **kwargs)

	def add_foods_log(self, foodId, mealTypeId, unitId, amount, date, foodName=None, favorite=None, brandName=None, calories=None, **kwargs):
		'''Log Food

		Creates food log entries for users with or without foodId value.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log.json'
		params = {}
		params['foodId'] = foodId
		if foodName:
			params['foodName'] = foodName
		params['mealTypeId'] = mealTypeId
		params['unitId'] = unitId
		params['amount'] = amount
		params['date'] = date
		if favorite:
			params['favorite'] = favorite
		if brandName:
			params['brandName'] = brandName
		if calories:
			params['calories'] = calories
		return self.post(endpoint, params=params, **kwargs)

	def delete_foods_log(self, food_log_id, **kwargs):
		'''Delete Food Log

		Deletes a user's food log entry with the given ID.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/{food-log-id}.json'.replace('{food-log-id}', food_log_id)

		return self.delete(endpoint, **kwargs)

	def add_water_log(self, date, amount, unit=None, **kwargs):
		'''Log Water

		Creates a log entry for water using units in the unit systems that corresponds to the Accept-Language header provided.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/water.json'
		params = {}
		params['date'] = date
		params['amount'] = amount
		if unit:
			params['unit'] = unit
		return self.post(endpoint, params=params, **kwargs)

	def delete_water_log(self, water_log_id, **kwargs):
		'''Delete Water Log

		Deletes a user's water log entry with the given ID.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/water/{water-log-id}.json'.replace('{water-log-id}', water_log_id)

		return self.delete(endpoint, **kwargs)

	def update_water_log(self, water_log_id, amount, unit=None, **kwargs):
		'''Update Water Log

		Updates a user's water log entry with the given ID.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/water/{water-log-id}.json'.replace('{water-log-id}', water_log_id)
		params = {}
		params['amount'] = amount
		if unit:
			params['unit'] = unit
		return self.post(endpoint, params=params, **kwargs)

	def get_favorite_foods(self, **kwargs):
		'''Get Favorite Foods

		Returns a list of a user's favorite foods in the format requested. A favorite food in the list provides a quick way to log the food via the Log Food endpoint.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/favorite.json'

		return self.get(endpoint, **kwargs)

	def get_frequent_foods(self, **kwargs):
		'''Get Frequent Foods

		Returns a list of a user's frequent foods in the format requested. A frequent food in the list provides a quick way to log the food via the Log Food endpoint.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/frequent.json'

		return self.get(endpoint, **kwargs)

	def add_favorite_food(self, food_id, **kwargs):
		'''Add Favorite Food

		Updates a user's daily activity goals and returns a response using units in the unit system which corresponds to the Accept-Language header provided.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/favorite/{food-id}.json'.replace('{food-id}', food_id)

		return self.post(endpoint, **kwargs)

	def delete_favorite_food(self, food_id, **kwargs):
		'''Delete Favorite Food

		Deletes a food with the given ID to the user's list of favorite foods.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/favorite/{food-id}.json'.replace('{food-id}', food_id)

		return self.delete(endpoint, **kwargs)

	def get_meals(self, **kwargs):
		'''Get Meals

		Returns a list of meals created by user in the user's food log in the format requested. User creates and manages meals on the Food Log tab on the website.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/meals.json'

		return self.get(endpoint, **kwargs)

	def add_meal(self, name, Description, foodId, unitId, amount, **kwargs):
		'''Create Meal

		Creates a meal with the given food contained in the post body.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/meals.json'
		params = {}
		params['name'] = name
		params['Description'] = Description
		params['foodId'] = foodId
		params['unitId'] = unitId
		params['amount'] = amount
		return self.post(endpoint, params=params, **kwargs)

	def update_meal(self, meal_id, name, Description, foodId, unitId, amount, **kwargs):
		'''Edit Meal

		Replaces an existing meal with the contents of the request. The response contains the updated meal.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/meals/{meal-id}.json'.replace('{meal-id}', meal_id)
		params = {}
		params['name'] = name
		params['Description'] = Description
		params['foodId'] = foodId
		params['unitId'] = unitId
		params['amount'] = amount
		return self.post(endpoint, params=params, **kwargs)

	def delete_meal(self, meal_id, **kwargs):
		'''Delete Meal

		Deletes a user's meal with the given meal id.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/meals/{meal-id}.json'.replace('{meal-id}', meal_id)

		return self.delete(endpoint, **kwargs)

	def get_recent_foods(self, **kwargs):
		'''Get Recent Foods

		Returns a list of a user's frequent foods in the format requested. A frequent food in the list provides a quick way to log the food via the Log Food endpoint.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/log/recent.json'

		return self.get(endpoint, **kwargs)

	def add_foods(self, name, defaultFoodMeasurementUnitId, defaultServingSize, calories, formType=None, description=None, **kwargs):
		'''Create Food

		Creates a new private food for a user and returns a response in the format requested. The created food is found via the Search Foods call.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods.json'
		params = {}
		params['name'] = name
		params['defaultFoodMeasurementUnitId'] = defaultFoodMeasurementUnitId
		params['defaultServingSize'] = defaultServingSize
		params['calories'] = calories
		if formType:
			params['formType'] = formType
		if description:
			params['description'] = description
		return self.post(endpoint, params=params, **kwargs)

	def delete_foods(self, food_id, **kwargs):
		'''Delete Custom Food

		Deletes custom food for a user and returns a response in the format requested.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/foods/{food-id}.json'.replace('{food-id}', food_id)

		return self.delete(endpoint, **kwargs)

	def get_foods_info(self, food_id, **kwargs):
		'''Get Food

		Returns the details of a specific food in the Fitbit food databases or a private food that an authorized user has entered in the format requested.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/foods/{food-id}.json'.replace('{food-id}', food_id)

		return self.get(endpoint, **kwargs)

	def get_foods_units(self, **kwargs):
		'''Get Food Units

		Returns a list of all valid Fitbit food units in the format requested.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/foods/units.json'

		return self.get(endpoint, **kwargs)

	def get_foods_list(self, query, **kwargs):
		'''Search Foods

		Returns a list of public foods from the Fitbit food database and private food the user created in the format requested.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/foods/search.json'
		params = {}
		params['query'] = query
		return self.get(endpoint, params=params, **kwargs)

	def get_friends(self, **kwargs):
		'''Get Friends

		Returns data of a user's friends in the format requested using units in the unit system which corresponds to the Accept-Language header provided.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1.1/user/-/friends.json'

		return self.get(endpoint, **kwargs)

	def get_friends_leaderboard(self, **kwargs):
		'''Get Friends Leaderboard

		Returns data of a user's friends in the format requested using units in the unit system which corresponds to the Accept-Language header provided.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1.1/user/-/leaderboard/friends.json'

		return self.get(endpoint, **kwargs)

	def get_friends_invitations(self, **kwargs):
		'''Get Friend Invitations

		Returns a list of invitations to become friends with a user in the format requested.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1.1/user/-/friends/invitations.json'

		return self.get(endpoint, **kwargs)

	def create_friends_invitations(self, invitedUserEmail=None, invitedUserId=None, **kwargs):
		'''Invite Friends

		Creates an invitation to become friends with the authorized user.  Either invitedUserEmail or invitedUserId needs to be provided.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1.1/user/-/friends/invitations'
		params = {}
		if invitedUserEmail:
			params['invitedUserEmail'] = invitedUserEmail
		if invitedUserId:
			params['invitedUserId'] = invitedUserId
		return self.post(endpoint, params=params, **kwargs)

	def respond_friends_invitation(self, from_user_id, accept, **kwargs):
		'''Respond to Friend Invitation

		Accepts or rejects an invitation to become friends wit inviting user.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1.1/user/-/friends/invitations/{from-user-id}'.replace('{from-user-id}', from_user_id)
		params = {}
		params['accept'] = accept
		return self.post(endpoint, params=params, **kwargs)

	def get_heart_by_date_period(self, date, period, **kwargs):
		'''Get Heart Rate Time Series

		Returns the time series data in the specified range for a given resource in the format requested using units in the unit systems that corresponds to the Accept-Language header provided.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/heart/date/{date}/{period}.json'.replace('{date}', date).replace('{period}', period)

		return self.get(endpoint, **kwargs)

	def get_heart_by_date_range(self, base_date, end_date, **kwargs):
		'''Get Heart Rate Time Series

		Returns the time series data in the specified range for a given resource in the format requested using units in the unit systems that corresponds to the Accept-Language header provided.
		'''
		if not isinstance(end_date, datetime):
			raise ValueError('Argument \'end_date\' must be a datetime object.')
		end_date = end_date.strftime('%Y-%m-%d') if end_date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/heart/date/{base-date}/{end-date}.json'.replace('{base-date}', base_date).replace('{end-date}', end_date)

		return self.get(endpoint, **kwargs)

	def get_heart_by_date_range_intraday(self, date, end_date, detail_level, **kwargs):
		'''Get Heart Rate Intraday Time Series

		Returns the intraday time series for a given resource in the format requested. If your application has the appropriate access, your calls to a time series endpoint for a specific day (by using start and end dates on the same day or a period of 1d), the response will include extended intraday values with a one-minute detail level for that day. Unlike other time series calls that allow fetching data of other users, intraday data is available only for and to the authorized user.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		if not isinstance(end_date, datetime):
			raise ValueError('Argument \'end_date\' must be a datetime object.')
		end_date = end_date.strftime('%Y-%m-%d') if end_date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/heart/date/{date}/{end-date}/{detail-level}.json'.replace('{date}', date).replace('{end-date}', end_date).replace('{detail-level}', detail_level)

		return self.get(endpoint, **kwargs)

	def get_heart_by_date_range_timestamp_intraday(self, date, end_date, detail_level, start_time, end_time, **kwargs):
		'''Get Heart Rate Intraday Time Series

		Returns the intraday time series for a given resource in the format requested. If your application has the appropriate access, your calls to a time series endpoint for a specific day (by using start and end dates on the same day or a period of 1d), the response will include extended intraday values with a one-minute detail level for that day. Unlike other time series calls that allow fetching data of other users, intraday data is available only for and to the authorized user.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		if not isinstance(end_date, datetime):
			raise ValueError('Argument \'end_date\' must be a datetime object.')
		end_date = end_date.strftime('%Y-%m-%d') if end_date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/heart/date/{date}/{end-date}/{detail-level}/time/{start-time}/{end-time}.json'.replace('{date}', date).replace('{end-date}', end_date).replace('{detail-level}', detail_level).replace('{start-time}', start_time).replace('{end-time}', end_time)

		return self.get(endpoint, **kwargs)

	def get_heart_by_date_intraday(self, date, detail_level, **kwargs):
		'''Get Heart Rate Intraday Time Series

		Returns the intraday time series for a given resource in the format requested. If your application has the appropriate access, your calls to a time series endpoint for a specific day (by using start and end dates on the same day or a period of 1d), the response will include extended intraday values with a one-minute detail level for that day. Unlike other time series calls that allow fetching data of other users, intraday data is available only for and to the authorized user.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/heart/date/{date}/1d/{detail-level}.json'.replace('{date}', date).replace('{detail-level}', detail_level)

		return self.get(endpoint, **kwargs)

	def get_heart_by_date_timestamp_intraday(self, date, detail_level, start_time, end_time, **kwargs):
		'''Get Heart Rate Intraday Time Series

		Returns the intraday time series for a given resource in the format requested. If your application has the appropriate access, your calls to a time series endpoint for a specific day (by using start and end dates on the same day or a period of 1d), the response will include extended intraday values with a one-minute detail level for that day. Unlike other time series calls that allow fetching data of other users, intraday data is available only for and to the authorized user.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/activities/heart/date/{date}/1d/{detail-level}/time/{start-time}/{end-time}.json'.replace('{date}', date).replace('{detail-level}', detail_level).replace('{start-time}', start_time).replace('{end-time}', end_time)

		return self.get(endpoint, **kwargs)

	def delete_sleep(self, log_id, **kwargs):
		'''Delete Sleep Log

		Deletes a user's sleep log entry with the given ID.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1.2/user/-/sleep/{log-id}.json'.replace('{log-id}', log_id)

		return self.delete(endpoint, **kwargs)

	def get_sleep_by_date(self, date, **kwargs):
		'''Get Sleep Log

		The Get Sleep Logs by Date endpoint returns a summary and list of a user's sleep log entries (including naps) as well as detailed sleep entry data for a given day.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1.2/user/-/sleep/date/{date}.json'.replace('{date}', date)

		return self.get(endpoint, **kwargs)

	def get_sleep_by_date_range(self, base_date, end_date, **kwargs):
		'''Get Sleep Logs by Date Range

		The Get Sleep Logs by Date Range endpoint returns a list of a user's sleep log entries (including naps) as well as detailed sleep entry data for a given date range (inclusive of start and end dates).
		'''
		if not isinstance(base_date, datetime):
			raise ValueError('Argument \'base_date\' must be a datetime object.')
		base_date = base_date.strftime('%Y-%m-%d') if base_date else ''
	
		if not isinstance(end_date, datetime):
			raise ValueError('Argument \'end_date\' must be a datetime object.')
		end_date = end_date.strftime('%Y-%m-%d') if end_date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1.2/user/-/sleep/date/{base-date}/{end-date}.json'.replace('{base-date}', base_date).replace('{end-date}', end_date)

		return self.get(endpoint, **kwargs)

	def get_sleep_list(self, sort, offset, limit, beforeDate=None, afterDate=None, **kwargs):
		'''Get Sleep Logs List

		The Get Sleep Logs List endpoint returns a list of a user's sleep logs (including naps) before or after a given day with offset, limit, and sort order.
		'''
		if beforeDate and not isinstance(beforeDate, datetime):
			raise ValueError('Argument \'beforeDate\' must be a datetime object.')
		beforeDate = beforeDate.strftime('%Y-%m-%d') if beforeDate else ''
	
		if afterDate and not isinstance(afterDate, datetime):
			raise ValueError('Argument \'afterDate\' must be a datetime object.')
		afterDate = afterDate.strftime('%Y-%m-%d') if afterDate else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1.2/user/-/sleep/list.json'
		params = {}
		if beforeDate:
			params['beforeDate'] = beforeDate
		if afterDate:
			params['afterDate'] = afterDate
		params['sort'] = sort
		params['offset'] = offset
		params['limit'] = limit
		return self.get(endpoint, params=params, **kwargs)

	def get_sleep_goal(self, **kwargs):
		'''Get Sleep Goal

		Returns the user's sleep goal.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1.2/user/-/sleep/goal.json'

		return self.get(endpoint, **kwargs)

	def update_sleep_goal(self, minDuration, **kwargs):
		'''Update Sleep Goal

		Create or update the user's sleep goal and get a response in the JSON format.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1.2/user/-/sleep/goal.json'
		params = {}
		params['minDuration'] = minDuration
		return self.post(endpoint, params=params, **kwargs)

	def add_sleep(self, startTime, duration, date, **kwargs):
		'''Log Sleep

		Creates a log entry for a sleep event and returns a response in the format requested.
		'''
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d') if date else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1.2/user/-/sleep.json'
		params = {}
		params['startTime'] = startTime
		params['duration'] = duration
		params['date'] = date
		return self.post(endpoint, params=params, **kwargs)

	def get_subscriptions_list(self, collection_path, **kwargs):
		'''Get a List of Subscriptions

		Retreives a list of a user's subscriptions for your application in the format requested. You can either fetch subscriptions for a specific collection or the entire list of subscriptions for the user. For best practice, make sure that your application maintains this list on your side and use this endpoint only to periodically ensure data consistency.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/{collection-path}/apiSubscriptions.json'.replace('{collection-path}', collection_path)

		return self.get(endpoint, **kwargs)

	def add_subscriptions(self, collection_path, subscription_id, **kwargs):
		'''Add a Subscription

		Adds a subscription in your application so that users can get notifications and return a response in the format requested. The subscription-id value provides a way to associate an update with a particular user stream in your application.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/{collection-path}/apiSubscriptions/{subscription-id}.json'.replace('{collection-path}', collection_path).replace('{subscription-id}', subscription_id)

		return self.post(endpoint, **kwargs)

	def delete_subscriptions(self, collection_path, subscription_id, **kwargs):
		'''Delete a Subscription

		Deletes a subscription for a user..
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/{collection-path}/apiSubscriptions/{subscription-id}.json'.replace('{collection-path}', collection_path).replace('{subscription-id}', subscription_id)

		return self.delete(endpoint, **kwargs)

	def get_badges(self, **kwargs):
		'''Get Badges

		Retrieves the user's badges in the format requested. Response includes all badges for the user as seen on the Fitbit website badge locker (both activity and weight related.) The endpoint returns weight and distance badges based on the user's unit profile preference as on the website.
		'''
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/badges.json'

		return self.get(endpoint, **kwargs)

	def get_profile(self, **kwargs):
		'''Get Profile

		Returns a user's profile. The authenticated owner receives all values. However, the authenticated user's access to other users' data is subject to those users' privacy settings. Numerical values are returned in the unit system specified in the Accept-Language header.
		'''
		required_scope = set(['location', 'profile', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/profile.json'

		return self.get(endpoint, **kwargs)

	def update_profile(self, gender=None, birthday=None, height=None, aboutMe=None, fullname=None, country=None, state=None, city=None, strideLengthWalking=None, strideLengthRunning=None, weightUnit=None, heightUnit=None, waterUnit=None, glucoseUnit=None, timezone=None, foodsLocale=None, locale=None, localeLang=None, localeCountry=None, startDayOfWeek=None, **kwargs):
		'''Update Profile

		Updates a user's profile using a form.
		'''
		if birthday and not isinstance(birthday, datetime):
			raise ValueError('Argument \'birthday\' must be a datetime object.')
		birthday = birthday.strftime('%Y-%m-%d') if birthday else ''
	
		required_scope = set(['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight'])
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))

		endpoint = '/1/user/-/profile.json'

		return self.post(endpoint, **kwargs)
