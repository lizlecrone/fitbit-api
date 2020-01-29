curl https://dev.fitbit.com/build/reference/web-api/explore/fitbit-web-api-swagger.json --output fitbit_api.json
python3 api_converter.py
autopep8 --in-place -a -a -a -a -a --hang-closing api_converter.py
autopep8 --in-place -a -a -a -a -a --hang-closing fitbit_api/__init__.py
autopep8 --in-place -a -a -a -a -a --hang-closing test_fitbit_api.py
cd docs
make html
