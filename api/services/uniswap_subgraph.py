import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert, update
from models.token import Token
from models.chart_data import PriceData
from config import UNISWAP_SUBGRAPH_URL

class UniswapSubgraphService:
    def __init__(self, db_session):
        self.api_url = UNISWAP_SUBGRAPH_URL
        self.db_session = db_session

    async def fetch_token_info(self, token_address):
        query = """
        {
            token(id: "%s") {
                name
                symbol
                totalSupply
                volumeUSD
                decimals
            }
        }
        """ % token_address

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json={'query': query}) as response:
                data = await response.json()
                return data['data']['token']

    async def fetch_tokens(self, address_array):
        address_arrayJSON = json.dumps(address_array)
        query = """
        {
            tokens(where: 
                { id_in: %s }
            ) {
                id
                name
                symbol
                totalSupply
                volumeUSD
                decimals
            }
        }
        """ % address_arrayJSON

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json={'query': query}) as response:
                data = await response.json()
                return data['data']['tokens']
            
    async def fetch_price_data(self, token_address, start_timestamp):
        query = """
        {
            tokenHourDatas(
                orderBy: periodStartUnix
                orderDirection: desc
                where: {token: "%s", periodStartUnix_gte: %d}
            ) {
                low
                open
                high
                close
                priceUSD
                periodStartUnix
                id
            }
        }
        """ % (token_address, start_timestamp)

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json={'query': query}) as response:
                data = await response.json()
                return data['data']['tokenHourDatas']

    async def update_token_info(self, token_address):
        token_info = await self.fetch_token_info(token_address)
        
        # Check if token exists
        existing_token = await self.db_session.execute(select(Token).filter_by(address=token_address))
        existing_token = existing_token.scalar_one_or_none()

        if existing_token:
            # Update existing token
            await self.db_session.execute(
                update(Token).
                where(Token.address == token_address).
                values(**self.format_token_data(token_info))
            )
        else:
            # Insert new token
            await self.db_session.execute(
                insert(Token).
                values(**self.format_token_data(token_info, token_address))
            )
        
        await self.db_session.commit()

    def format_token_data(self, token_info, token_address=None):
        formatted_data = {
            'name': token_info['name'],
            'symbol': token_info['symbol'],
            'total_supply': token_info['totalSupply'],
            'volume_usd': token_info['volumeUSD'],
            'decimals': token_info['decimals']
        }

        if token_address:
            formatted_data['address'] = token_address

        # Remove None values (else None values will be inserted into the database as null) 
        return {k: v for k, v in formatted_data.items() if v is not None}


    async def get_token_id(self, token_address):
        token = await self.db_session.execute(select(Token).filter_by(address=token_address))
        token = token.scalar_one_or_none()

        return token.id
    
    async def update_price_data(self, token_id):
        # Get the latest timestamp in our database
        latest_price_data = await self.db_session.execute(
            select(PriceData).
            filter_by(token_id=token_id).
            order_by(PriceData.timestamp.desc()).
            limit(1)
        )
        latest_price_data = latest_price_data.scalar_one_or_none()

        if latest_price_data:
            start_timestamp = int(latest_price_data.timestamp.timestamp())
        else:
            # If no data, fetch last 10 days
            start_timestamp = int((datetime.now() - timedelta(days=10)).timestamp())

        price_data = await self.fetch_price_data(token_id, start_timestamp)

        for data in price_data:
            timestamp = datetime.fromtimestamp(data['periodStartUnix'])
            await self.db_session.execute(
                insert(PriceData).
                values(
                    token_id=token_id,
                    timestamp=timestamp,
                    open=data['open'],
                    close=data['close'],
                    high=data['high'],
                    low=data['low'],
                    price_usd=data['priceUSD']
                ).
                on_conflict_do_update(
                    index_elements=['token_id', 'timestamp'],
                    set_=dict(
                        open=data['open'],
                        close=data['close'],
                        high=data['high'],
                        low=data['low'],
                        price_usd=data['priceUSD']
                    )
                )
            )
        
        await self.db_session.commit()

    async def update_all_data(self):
        # Fetch all tokens
        tokens = await self.db_session.execute(select(Token))
        tokens = tokens.scalars().all()

        for token in tokens:
            await self.update_token_info(token.id)
            await self.update_price_data(token.id)

    async def fetch_and_store_data(self, address_array):
        # Fetch token info
        tokens = await self.fetch_tokens(address_array)

        for token in tokens:
            await self.db_session.execute(
                insert(Token).
                values(address=token['id'], **token)
            )

        await self.db_session.commit()

        # Fetch price data
        for token in tokens:
            token_id = await self.get_token_id(token['id'])
            await self.update_price_data(token_id)

    async def update_chart_data(self):
        # Fetch all tokens
        tokens = await self.db_session.execute(select(Token))
        tokens = tokens.scalars().all()

        for token in tokens:
            await self.update_price_data(token.id)

    async def start_polling(self, interval_seconds=30):
        while True:
            await self.update_chart_data()
            await asyncio.sleep(interval_seconds)