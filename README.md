# python-deriv-api
A python implementation of deriv api library

### Requirement
Python (3.9.6 or higher is recommended) and pip3

# Installation



# Usage
This is basic deriv-api python library which helps to make websocket connection and
deal the API calls (including subscription).

Import the module

```
from deriv_api import deriv_api
```

Access 

```
api = deriv_api.DerivAPI({ endpoint: 'ws://...', app_id: 1234 });
response = await api.ping({'ping': 1})
print(response) 
```

## Creating a websocket connection
- Pass the arguments needed to create a connection:
```
   api = deriv_api.DerivAPI({ endpoint: 'ws://...', app_id: 1234 });
```

- create and use a previously opened connection:
```
   connection = await websockets.connect('ws://...')
   api = deriv_api.DerivAPI(connection=connection)
```

# Documentation

#### API reference
The complete API reference is hosted [here](https://binary-com.github.io/python-deriv-api/)

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

# Run test

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

#### Run examples

set token and run example

```
export DERIV_TOKEN=xxxTokenxxx
PYTHONPATH=. python3 examples/simple_bot1.py
```
