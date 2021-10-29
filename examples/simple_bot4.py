# run it like PYTHONPATH=. python3 examples/simple_bot4.py
import sys
import asyncio
import os
from deriv_api import DerivAPI
from rx import Observable

app_id = 1089
api_token = os.getenv('DERIV_TOKEN', '')
expected_payout = os.getenv('EXPECTED_PAYOUT', 10)

if len(api_token) == 0:
    sys.exit("DERIV_TOKEN environment variable is not set")


async def sample_calls():
    api = DerivAPI(app_id=app_id)

    # Authorize
    authorize = await api.authorize(api_token)

    asyncio.create_task(buy_proposal(api))

    # Subscribe proposal
    source_proposal: Observable = await api.subscribe({"proposal": 1, "amount": 10, "barrier": "+0.1",
                                                       "basis": "payout",
                                                       "contract_type": "CALL", "currency": "USD", "duration": 160,
                                                       "duration_unit": "s",
                                                       "symbol": "R_100"
                                                       })
    source_proposal.subscribe()
    await asyncio.sleep(5)


# Buy contract
async def buy_proposal(api):
    proposal = await api.expect_response('proposal')
    if proposal.get('proposal').get('payout') >= expected_payout:
        proposal_id = proposal.get('proposal').get('id')
        # buy contract
        buy = await api.buy({"buy": proposal_id, "price": 10})
        contract_id = buy.get('buy').get('contract_id')

        # open contract stream
        source_poc: Observable = await api.subscribe({"proposal_open_contract": 1, "contract_id": contract_id})
        source_poc.subscribe(lambda poc: print(poc))
        await asyncio.sleep(10)

        await api.forget(proposal.get('subscription').get('id'))

loop = asyncio.get_event_loop()
asyncio.run(sample_calls())
loop.run_forever()
