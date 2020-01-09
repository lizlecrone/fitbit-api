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

class InsufficientScope(Exception):
	pass

class FitbitClient:
	def __init__(self, session):
		self.session = session

	@classmethod
	def create_using_token(cls, token, client_id, callback_uri, scope=None, new_token_callback=None):
		scope = scope or ALL_SCOPES
		session = OAuth2Session(
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
		session = OAuth2Session(client_id=client_id, redirect_uri=callback_uri, scope=scope)
		authorization_url, state = session.authorization_url('https://www.fitbit.com/oauth2/authorize')
		return authorization_url

	@classmethod
	def OAuth2_step_two(cls, client_id, client_secret, callback_uri, redirect_uri, scope=None, new_token_callback=None):
		scope = scope or ALL_SCOPES
		session = OAuth2Session(
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

	def get_food_locales(self):
		return self.session.get('https://api.fitbit.com/1/foods/locales.json').json()

	def get_activities_by_date(self,date):
		required_scope = {
			"activity",
			"heartrate",
			"location",
			"nutrition",
			"profile",
			"settings",
			"sleep",
			"social",
			"weight"
		}
		if not all(scope in self.session.scope for scope in required_scope):
			missing_scope = [scope for scope in required_scope if scope not in self.session.scope]
			raise InsufficientScope('This application needs additional scope {missing_scope} for this request.'.format(missing_scope=missing_scope))
		if not isinstance(date, datetime):
			raise ValueError('Argument \'date\' must be a datetime object.')
		date = date.strftime('%Y-%m-%d')
		url = 'https://api.fitbit.com/1/user/-/activities/date/{date}.json'.replace('{date}', date)
		return self.session.get(url).json()







