
# Usage examples
## Short examples

```
from deriv_api import DerivAPI
api = DerivAPI(app_id=app_id)
```

### Authenticate to an account using token
```
    authorize = await api.authorize(api_token)
    print(authorize)
```
### Get Balance
```
    account = await api.balance()
    print(account) 
```
### Get all the assets info
```
    assets = await api.cache.asset_index({"asset_index": 1})
    print(assets)
```

### Get all active symbols
```
    active_symbols = await api.active_symbols({"active_symbols": "full"})
    print(active_symbols)
```

### To get active symbols from cache 
```
    active_symbols = await api.cache.active_symbols({"active_symbols": "full"})
    print(active_symbols)
```

### Get proposal
```
    proposal = await api.proposal({"proposal": 1, "amount": 100, "barrier": "+0.1", "basis": "payout",
                                   "contract_type": "CALL", "currency": "USD", "duration": 60, "duration_unit": "s",
                                   "symbol": "R_100"
    })
    print(proposal) 
```

### Buy
```
    proposal_id = proposal.get('proposal').get('id')
    buy = await api.buy({"buy": proposal_id, "price": 100})
    print(buy)
```

### open contract detail
```
    contract_id = buy.get('buy').get('contract_id')
    poc = await api.proposal_open_contract(
        {"proposal_open_contract": 1, "contract_id": contract_id })
    print(poc)
```

### Sell 
```
    contract_id = buy.get('buy').get('contract_id')
    sell = await api.sell({"sell": contract_id, "price": 40})
    print(sell)
```

### Profit table
```
    profit_table = await api.profit_table({"profit_table": 1, "description": 1, "sort": "ASC"})
    print(profit_table)
```

### Transaction statement
```
    statement = await api.statement({"statement": 1, "description": 1, "limit": 100, "offset": 25})
    print(statement)
```
