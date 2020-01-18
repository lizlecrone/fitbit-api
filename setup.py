import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="fitbit_api", # Replace with your own username
    version="0.0.1",
    author="Liz LeCrone",
    author_email="lizlecrone@gmail.com",
    description="Fitbit API Client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lizlecrone/fitbit-api",
    packages=[
    	'fitbit_api',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)