# python-deriv-api
A python implementation of deriv api library.

Go thru [api.deriv.com](https://api.deriv.com/){:target="_blank"} to know simple easy steps on how to register and get access.
Use this all-in-one python library to set up and make your app running or you can extend it.

### Requirement
Python (3.9.6 or higher is recommended) and pip3 token

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

Examples [here](https://github.com/binary-com/python-deriv-api/examples)

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

#### Generate documentations

Generate html version of the docs and publish it to gh-pages
make gh-pages

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

