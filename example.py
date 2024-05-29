from tweet_search import Tweet

eng = Tweet()

session = eng.auth(session_json='authentication.json')
result = eng.search_hashtag(session=session,query="#covid")
#print(eng.search_iter_and_store(session=session,query="#covid",iter=2,use_cursor=False,cursor_path="#covid_cursor.txt"))
for tweet in result:
    print(f"tweet:{tweet[4]}")
    print(f"like_count:{tweet[3]}")
    print(f"reply_count:{tweet[5]}")
    print(f"retweet_count:{tweet[6]}")
    print(f"screen_name:{tweet[2]}")
    print(f"followers_count:{tweet[0]}")
    print(f"tweet_location:{tweet[1]}")
    print("===========================\n\n")
    
