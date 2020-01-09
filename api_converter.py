import json
from pprint import pprint
from jinja2 import Environment, FileSystemLoader

def camel_to_snake_case(str):
	return ''.join(['_'+i.lower() if i.isupper()
		else i for i in str]).lstrip('_')

def kabob_to_snake_case(str):
	return str.replace('-','_')

#attempt to read fitbit's json
fitbit_api_json = ''
with open('fitbit_api.json', 'r') as file:
	fitbit_api_json = json.load(file)

endpoints = [endpoint for endpoint in fitbit_api_json['paths'].keys() if endpoint not in ['/oauth2/token', '/1.1/oauth2/introspect']]

apis = []
for endpoint in endpoints:
	for method in fitbit_api_json['paths'][endpoint].keys():
		endpoint_data = fitbit_api_json['paths'][endpoint][method]
		parameters = endpoint_data['parameters'] if 'parameters' in endpoint_data else []
		for parameter in parameters:
			parameter['python_name'] = kabob_to_snake_case(parameter['name'])
		date_parameters = [parameter for parameter in parameters if 'format' in parameter and parameter['format']== 'date']

		#load the jinja file with variables
		apis.append({
			'function': camel_to_snake_case(endpoint_data['operationId']),
			'required_scope': endpoint_data['security'][0]['oauth2'] if 'security' in endpoint_data else [],
			'parameters': sorted(parameters, key=lambda p: not p['required']),
			'path_params': [parameter for parameter in parameters if parameter['in'] == 'path'],
			'query_params': [parameter for parameter in parameters if parameter['in'] == 'query'],
			'date_parameters': date_parameters,
			'endpoint': endpoint,
			'method': method,
			'summary': endpoint_data['summary'],
			'description': endpoint_data['description'],
		})

env = Environment(loader=FileSystemLoader(''))
template = env.get_template('fitbit_api.jinja')
output_from_parsed_template = template.render(apis=apis)

#print the result of above to python file
with open('fitbit_api.py', 'w') as python_file:
    python_file.write(output_from_parsed_template)



