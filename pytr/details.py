import asyncio
from pytr.utils import preview
from datetime import datetime, timedelta


class Details:
    def __init__(self, tr, isin):
        self.tr = tr
        self.isin = isin

    async def details_loop(self):
        recv = 0
        await self.tr.stock_details(self.isin)
        await self.tr.news(self.isin)
        # await self.tr.subscribe_news(self.isin)
        await self.tr.ticker(self.isin, exchange='LSX')
        await self.tr.performance(self.isin, exchange='LSX')
        await self.tr.instrument_details(self.isin)
        await self.tr.instrument_suitability(self.isin)

        # await self.tr.add_watchlist(self.isin)
        # await self.tr.remove_watchlist(self.isin)
        # await self.tr.savings_plan_parameters(self.isin)
        # await self.tr.unsubscribe_news(self.isin)

        while True:
            _subscription_id, subscription, response = await self.tr.recv()

            if subscription['type'] == 'stockDetails':
                recv += 1
                self.stockDetails = response
            elif subscription['type'] == 'neonNews':
                recv += 1
                self.neonNews = response
            elif subscription['type'] == 'ticker':
                recv += 1
                self.ticker = response
            elif subscription['type'] == 'performance':
                recv += 1
                self.performance = response
            elif subscription['type'] == 'instrument':
                recv += 1
                self.instrument = response
            elif subscription['type'] == 'instrumentSuitability':
                recv += 1
                self.instrumentSuitability = response
                print('instrumentSuitability:', response)
            else:
                print(f"unmatched subscription of type '{subscription['type']}':\n{preview(response, num_lines=30)}")

            if recv == 6:
                return

    async def print_instrument(self):
        print('Name:', self.instrument['name'])
        print('ShortName:', self.instrument['shortName'])
        print('Type:', self.instrument['typeId'])
        for ex in self.instrument['exchanges']:
            print(f"{ex['slug']}: {ex['symbolAtExchange']} {ex['nameAtExchange']}")

        for tag in self.instrument['tags']:
            print(f"{tag['type']}: {tag['name']}")
        
        await self.stock_price()

    def stock_details(self):
        company = self.stockDetails['company']
        for company_detail in company:
            if company[company_detail] is not None:
                print(f'{company_detail:15}: {company[company_detail]}')
        for detail in self.stockDetails:
            if detail != 'company' and self.stockDetails[detail] is not None and self.stockDetails[detail] != []:
                print(f'{detail:15}: {self.stockDetails[detail]}')

    def news(self, relevant_days=30):
        since = datetime.now() - timedelta(days=relevant_days)
        if not hasattr(self, 'neonNews'):
            return
        for news in self.neonNews:
            newsdate = datetime.fromtimestamp(news['createdAt'] / 1000.0)
            if newsdate > since:
                dateiso = newsdate.isoformat(sep=' ', timespec='minutes')
                print(f"{dateiso}: {news['headline']}")

    async def overview(self):
        await self.print_instrument()
        self.news()
        self.stock_details()

    def get(self):
        asyncio.get_event_loop().run_until_complete(self.details_loop())

        asyncio.get_event_loop().run_until_complete(self.overview())

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
                await self.tr.unsubscribe(subscription_id)
                exchangeId = subscriptions[subscription_id]['exchangeId']
                subscriptions.pop(subscription_id, None)
                
                exchanges[exchangeId] = response

        for exchange, offers in exchanges.items():
            print(
                f"{exchange[:3]:<4} {float(offers['bid']['price']):>10.4f} {float(offers['ask']['price']):>10.4f}"
                )
            print(offers)