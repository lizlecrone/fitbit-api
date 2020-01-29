import json
from jinja2 import Environment, FileSystemLoader


def camel_to_snake_case(str):
    return ''.join(['_' + i.lower() if i.isupper()
                    else i for i in str]).lstrip('_')


def kabob_to_snake_case(str):
    return str.replace('-', '_')


def is_date(parameter):
    return (parameter.get('format') == 'date') or (
        'yyyy-MM-dd' in parameter.get('description'))


def is_int(parameter):
    return parameter.get('type') == 'integer'


def is_bool(parameter):
    return parameter.get('type') == 'boolean'


# attempt to read fitbit's json
fitbit_api_json = ''
with open('fitbit_api.json', 'r') as file:
    fitbit_api_json = json.load(file)

endpoints = [endpoint for endpoint in fitbit_api_json['paths'].keys(
) if endpoint not in ['/oauth2/token', '/1.1/oauth2/introspect']]

apis = []
for endpoint in endpoints:
    for method in fitbit_api_json['paths'][endpoint].keys():
        endpoint_data = fitbit_api_json['paths'][endpoint][method]
        parameters = (
            endpoint_data['parameters']
            if 'parameters' in endpoint_data else []
            )
        for parameter in parameters:
            parameter['python_name'] = camel_to_snake_case(
                kabob_to_snake_case(parameter['name']))
            if is_date(parameter):
                parameter['description'] = 'A datetime object.'
                parameter['python_type'] = 'datetime'
            elif is_int(parameter):
                parameter['python_type'] = 'int'
            elif is_bool(parameter):
                parameter['python_type'] = 'bool'
            else:
                parameter['python_type'] = 'string'

        date_parameters = [p for p in parameters if is_date(p)]
        int_parameters = [p for p in parameters if is_int(p)]
        bool_parameters = [p for p in parameters if is_bool(p)]

        required_scope = (
            endpoint_data['security'][0]['oauth2']
            if 'security' in endpoint_data else []
            )

        # load the jinja file with variables
        apis.append({
            'function': camel_to_snake_case(endpoint_data['operationId']),
            'required_scope': required_scope,
            'parameters': sorted(parameters, key=lambda p: not p['required']),
            'path_params': [p for p in parameters if p['in'] == 'path'],
            'query_params': [p for p in parameters if p['in'] == 'query'],
            'date_parameters': date_parameters,
            'endpoint': endpoint,
            'method': method,
            'summary': endpoint_data['summary'],
            'description': endpoint_data['description'],
            })

env = Environment(loader=FileSystemLoader(''))
template = env.get_template('fitbit_api.jinja')
output_from_parsed_template = template.render(apis=apis)

# print the result of above to python file
with open('fitbit_api/__init__.py', 'w') as python_file:
    python_file.write(output_from_parsed_template)
