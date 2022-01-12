# python-deriv-api
A python implementation of deriv api library.

[![PyPI](https://img.shields.io/pypi/v/python_deriv_api.svg?style=flat-square)](https://pypi.org/project/python_deriv_api/)
[![Python 3.9.6](https://img.shields.io/badge/python-3.9.6-blue.svg)](https://www.python.org/download/releases/3.9.6/)
[![Test status](https://circleci.com/gh/binary-com/python-deriv-api.svg?style=shield&circle-token=8b7c7b39615ea83053044854105bf90975b18126)](https://app.circleci.com/pipelines/github/binary-com/python-deriv-api)

Go through [api.deriv.com](https://api.deriv.com/) to know simple easy steps on how to register and get access.
Use this all-in-one python library to set up and make your app running or you can extend it.

### Requirement
Python (3.9.6 or higher is recommended) and pip3

Note: There is bug in 'websockets' package with python 3.9.7, hope that will be fixed in 3.9.8 as mentioned in
https://github.com/aaugustin/websockets/issues/1051. Please exclude python 3.9.7.

# Installation

`python3 -m pip install python_deriv_api`

# Usage
This is basic deriv-api python library which helps to make websockets connection and
deal the API calls (including subscription).

Import the module

```
from deriv_api import DerivAPI
```

Access 

```
api = DerivAPI(endpoint='ws://...', app_id=1234);
response = await api.ping({'ping': 1})
print(response) 
```

## Creating a websockets connection and API instantiation
You can either create an instance of websockets and pass it as connection
    or
pass the endpoint and app_id to the constructor to create the connection for you.

If you pass the connection it's up to you to reconnect in case the connection drops (cause API doesn't know how to create the same connection).


- Pass the arguments needed to create a connection:
```
   api = DerivAPI(endpoint='ws://...', app_id=1234);
```

- create and use a previously opened connection:
```
   connection = await websockets.connect('ws://...')
   api = DerivAPI(connection=connection)
```

# Documentation

#### API reference
The complete API reference is hosted [here](https://binary-com.github.io/python-deriv-api/)

Examples [here](https://github.com/binary-com/python-deriv-api/tree/master/examples)

# Development
```
git clone https://github.com/binary-com/python-deriv-api
cd python-deriv-api
```
Setup environment
```
make setup
```

Setup environment and run test
```
make all
```

#### Run test

```
python setup.py pytest
```

or

```
pytest
```

or

```
make test
```
#### Generate documentations

Generate html version of the docs and publish it to gh-pages

```
make gh-pages
```

#### Build the package
```
make build
```
#### Run examples

set token and run example

```
export DERIV_TOKEN=xxxTokenxxx
PYTHONPATH=. python3 examples/simple_bot1.py
```

