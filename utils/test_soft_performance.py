import asyncio
import json
import websockets


async def get_cashDistributed(uri):
    payment_details = []
    async with websockets.connect(uri) as websocket:
        async for event in websocket:
            # event = json.loads( await websocket.recv() )
            event = json.loads(event)
            #print(event)
            if event['__source'] == "SmartHopper/hopper":
                if str.upper(event['__type']) == str.upper('MoneyDistributorDevice_MoneyAmountEvent'):
                    # we will use the hopper of index 0 as we are testing with only one hopper
                    # TODO : Generalize to multiple hoppers
                    if event['paymentList'][0]['accepted']['coins'] != '':
                        payment_details = str.split(event['paymentList'][0]['accepted']['coins'])
                        print(payment_details)
                        break
        return payment_details


payment_details = asyncio.get_event_loop().run_until_complete(get_cashDistributed("ws://172.31.94.132:8091/hopper"))
each_coin_count = dict()
for coin in set(payment_details):
    each_coin_count[coin] = payment_details.count(coin)
print(each_coin_count)