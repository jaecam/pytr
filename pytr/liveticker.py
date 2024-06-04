import asyncio
from pytr.utils import preview
from datetime import datetime, timedelta


class Liveticker:
    def __init__(self, tr, isin):
        self.tr = tr
        self.isin = isin

    async def print_instrument(self):
        await self.tr.instrument_details(self.isin)
        _, _, response = await self.tr.recv()
        self.instrument = response

        print('Name:', self.instrument['name'])
        print('ShortName:', self.instrument['shortName'])
        print('Type:', self.instrument['typeId'])
        for ex in self.instrument['exchanges']:
            print(f"{ex['slug']}: {ex['symbolAtExchange']} {ex['nameAtExchange']}")

        for tag in self.instrument['tags']:
            print(f"{tag['type']}: {tag['name']}")
        
        await self.stock_price()


    def get(self):
        asyncio.get_event_loop().run_until_complete(self.print_instrument())

    async def stock_price(self):
        subscriptions = {}
        subscription_id = await self.tr.instrument_details(self.isin)
        subscription_id, subscription, response = await self.tr.recv()
        await self.tr.unsubscribe(subscription_id)
        exchangeIds = response['exchangeIds']
        # Populate netValue for each ISIN
        subscriptions = {}
        if len(exchangeIds) > 0:
            for exchange in exchangeIds:
                subscription_id = await self.tr.ticker(self.isin, exchange=exchange)
                pos = {}
                pos['name'] = response['shortName']
                pos['exchangeId'] = exchange
                subscriptions[subscription_id] = pos

        exchanges = {}
        while len(subscriptions) > 0:
            subscription_id, subscription, response = await self.tr.recv()
            if subscription['type'] == 'ticker':
                exchangeId = subscriptions[subscription_id]['exchangeId']
                exchanges[exchangeId] = response

                dt_object = datetime.fromtimestamp(float(response['bid']['time']) / 1000)
                print(
                    f"{exchangeId[:3]:<4} {float(response['bid']['price']):>10.4f} {response['bid']['size']:>10} " +
                    f" {float(response['ask']['price']):>10.4f} {response['ask']['size']:>10}" +
                    f"   {dt_object.strftime('%H:%M:%S')}.{response['bid']['time']%1000:03}"

                    )