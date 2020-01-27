curl https://dev.fitbit.com/build/reference/web-api/explore/fitbit-web-api-swagger.json --output fitbit_api.json
python3 api_converter.py
cd docs
make html
