# python-deriv-api
A python implementation of deriv api library

# Usage

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


# Development
```
git clone https://github.com/binary-com/python-deriv-api
cd python-deriv-api
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

pdoc deriv_api --force --html -o docs/html --template-dir docs/templates

#### Run examples

set token and run example

```
export DERIV_TOKEN=xxxTokenxxx
PYTHONPATH=. python3 examples/simple_bot1.py
```
