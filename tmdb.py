from cache import Cache
from datetime import timedelta
import httpx
import os
import asyncio

#from dotenv import load_dotenv
#load_dotenv()

TMDB_POSTER_URL = 'https://image.tmdb.org/t/p/w500'
TMDB_BACK_URL = 'https://image.tmdb.org/t/p/original'
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

# Cache set
tmp_cache = Cache(maxsize=100000, ttl=timedelta(days=7).total_seconds())
tmp_cache.clear()

# Too many requests retry
max_retries = 5

async def get_tmdb_data(client: httpx.AsyncClient, id: str, source: str) -> dict:
    params = {
        "external_source": source,
        "language": "it-IT",
        "api_key": TMDB_API_KEY
    }

    headers = {
        "accept": "application/json"
    }
    
    url = f"https://api.themoviedb.org/3/find/{id}"
    item = tmp_cache.get(id)

    if item != None:
        return item
    else:
        for attempt in range(1, max_retries + 1):
            response = await client.get(url, headers=headers, params=params)

            if response.status_code == 200:
                meta_dict = response.json()
                meta_dict['imdb_id'] = id
                tmp_cache.set(id, meta_dict)
                return meta_dict

            elif response.status_code == 429:
                print(response)
                await asyncio.sleep(attempt * 2)

        return {}


async def convert_imdb_to_tmdb(imdb_id: str) -> dict:

    tmdb_data = tmp_cache.get(imdb_id)

    if tmdb_data != None:
        return get_id(tmdb_data)
    else:
        async with httpx.AsyncClient(timeout=20) as client:
            tmdb_data = await get_tmdb_data(client, imdb_id, 'imdb_id')
            return get_id(tmdb_data)
        

def get_id(tmdb_data: dict) -> str:
    try:
        id = next((v[0]["id"] for v in tmdb_data.values() if v), None)
    except:
        return tmdb_data['imdb_id']
    else:
        return f"tmdb:{id}"