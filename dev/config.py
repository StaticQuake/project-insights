import os

key = "youtube_project"
iv = "youtube_encyptyo"
salt = "youtube_AesEncryption"

TMDB_API_KEY = "abc3b8d49b4f254556730bf374cda743"
TMDB_BASE_URL = "https://api.themoviedb.org/3/discover/movie"
TMDB_BASE_TV_URL = "https://api.themoviedb.org/3/discover/tv"
HEADERS = {
    "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
}


#AWS Access And Secret key
aws_access_key = "jMU9KPMIdX0xqGha3sLbiaZr9N/IebrI9t+lkZ6s7Bw="
aws_secret_key = "56M4Aqjf5m5k0eCxqhBgA0vcOW9j+08r40CAvs7dednhwl0Cx+SG0YfN2lSSS2U8"
bucket_name = "movie-data-raw-shravan"
s3_raw_directory = "raw"

# table name
movie_id_raw_table_name = "movie_id_raw"