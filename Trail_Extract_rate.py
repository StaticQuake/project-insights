import requests
import pandas as pd
from datetime import date
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "abc3b8d49b4f254556730bf374cda743"

movie_ids = pd.read_csv("data\movie_ids.csv")["id"].tolist()

def fetch_movie(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    try:
        response = requests.get(url, params={"api_key": API_KEY}, timeout=10)
        if response.status_code == 200:
            d = response.json()
            return {
                "id": d["id"],
                "popularity": d["popularity"],
                "vote_average": d["vote_average"],
                "vote_count": d["vote_count"]
            }
    except:
        return None

results = []
failed = []

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(fetch_movie, mid): mid for mid in movie_ids}
    for i, future in enumerate(as_completed(futures)):
        result = future.result()
        if result:
            results.append(result)
        else:
            failed.append(futures[future])
        if i % 500 == 0:
            print(f"Progress: {i}/{len(movie_ids)}")

today = date.today().isoformat()
df_metrics = pd.DataFrame(results)
df_metrics.to_csv(f"metrics_{today}.csv", index=False)
print(f"Done. Success: {len(results)}, Failed: {len(failed)}")
# import requests
# import pandas as pd
# from datetime import date
# import time

# API_KEY = "abc3b8d49b4f254556730bf374cda743"

# # load just 5 ids for testing
# movie_ids = pd.read_csv("data\movie_ids.csv")["id"].tolist()

# results = []

# for movie_id in movie_ids:
#     url = f"https://api.themoviedb.org/3/movie/{movie_id}"
#     params = {"api_key": API_KEY}
    
#     response = requests.get(url, params=params)
    
#     if response.status_code == 200:
#         d = response.json()
#         results.append({
#             "id": d["id"],
#             "snapshot_date": date.today().isoformat(),
#             "popularity": d["popularity"],
#             "vote_average": d["vote_average"],
#             "vote_count": d["vote_count"]
#         })
#         print(f"Done: {d['title']}")
#     else:
#         print(f"Failed: {movie_id} — status {response.status_code}")
    
#     time.sleep(0.1)

# df_metrics = pd.DataFrame(results)
# print(df_metrics)
# df_metrics.to_csv(f"data\metrics_{date.today().isoformat()}.csv", index=False)