
# Usage examples
## Short examples

```python
    from deriv_api import DerivAPI
    api = DerivAPI(app_id=app_id)
```

### Authenticate to an account using token
```python
    authorize = await api.authorize(api_token)
    print(authorize)
```
### Get Balance
```python
    account = await api.balance()
    print(account) 
```
### Get all the assets info
```python
    assets = await api.asset_index({"asset_index": 1})
    print(assets)
```

To get assets info from cache
```python
    assets = await api.cache.asset_index({"asset_index": 1})
    print(assets)
```

### Get all active symbols
```python
    active_symbols = await api.active_symbols({"active_symbols": "full"})
    print(active_symbols)
```

To get active symbols from cache
```python
    active_symbols = await api.cache.active_symbols({"active_symbols": "full"})
    print(active_symbols)
```

### Get proposal
```python
    proposal = await api.proposal({"proposal": 1, "amount": 100, "barrier": "+0.1", "basis": "payout",
                                   "contract_type": "CALL", "currency": "USD", "duration": 60, "duration_unit": "s",
                                   "symbol": "R_100"
    })
    print(proposal) 
```

subscribe the proposal stream
```python
    source_proposal: Observable = await api.subscribe({"proposal": 1, "amount": 100, "barrier": "+0.1", "basis": "payout",
                                           "contract_type": "CALL", "currency": "USD", "duration": 160,
                                           "duration_unit": "s",
                                           "symbol": "R_100",
                                           "subscribe": 1
                                           })
    source_proposal.subscribe(lambda proposal: print(proposal))
```

### Buy
```python
    proposal_id = proposal.get('proposal').get('id')
    buy = await api.buy({"buy": proposal_id, "price": 100})
    print(buy)
```

### open contract detail
```python
    contract_id = buy.get('buy').get('contract_id')
    poc = await api.proposal_open_contract(
        {"proposal_open_contract": 1, "contract_id": contract_id })
    print(poc)
```

subscribe the open contract stream
```
    source_poc: Observable = await api.subscribe({"proposal_open_contract": 1, "contract_id": contract_id})
    source_poc.subscribe(lambda poc: print(poc)
```

### Sell 
```python
    contract_id = buy.get('buy').get('contract_id')
    sell = await api.sell({"sell": contract_id, "price": 40})
    print(sell)
```

### Profit table
```python
    profit_table = await api.profit_table({"profit_table": 1, "description": 1, "sort": "ASC"})
    print(profit_table)
```

### Transaction statement
```python
    statement = await api.statement({"statement": 1, "description": 1, "limit": 100, "offset": 25})
    print(statement)
```

### Subscribe a stream

We are using rxpy to maintain our deriv api subscriptions. Please distinguish api subscription from rxpy sequence subscription
```python
    # creating a rxpy sequence object to represent deriv api streams
    source_tick_50 = await api.subscribe({'ticks': 'R_50'})

    # subscribe the rxpy sequence with a callback function,
    # when the data received, the call back function will be called
    source_tick_50.subscribe(lambda tick: print(tick))
```

### unsubscribe the rxpy sequence
```python
    seq_sub = source_tick_50.subscribe(lambda tick: print(tick))
    seq_sub.dispose()
```

### unsubscribe the deriv api stream

There are 2 ways to unsubscribe deriv api stream

- by `dispose` all sequence subscriptions
```python
    # creating a rxpy sequence object to represent deriv api streams
    source_tick_50 = await api.subscribe({'ticks': 'R_50'})
    # subscribe the rxpy sequence with a callback function,
    # when the data received , the call back function will be called
    seq_sub1 = source_tick_50.subscribe(lambda tick: print(f"get tick from sub1 {tick}"))
    seq_sub2 = source_tick_50.subscribe(lambda tick: print(f"get tick from sub2 {tick}"))
    seq_sub1.dispose()
    seq_sub2.dispose()
    # When all seq subscriptions of one sequence are disposed. Then a `forget` will be called and that deriv api stream will be unsubscribed
```


- by `forget` that deriv stream
```python
    # get a datum first
    from rx import operators as op
    tick = await source_tick_50.pipe(op.first(), op.to_future)
    api.forget(tick['R_50']['subscription']['id'])
```

### print errors
```python
    api.sanity_errors.subscribe(lambda err: print(err))
```

### do something when one type of message coming
```python
    async def print_hello_after_authorize():
        auth_data = await api.expect_response('authorize')
        print(f"Hello {auth_data['authorize']['fullname']}")
    asyncio.create_task(print_hello_after_authorize())
    api.authorize({'authorize': 'AVALIDTOKEN'})
```
