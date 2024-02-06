from tweet_search import Tweet

eng = Tweet()

session = eng.auth(session_json='authentication.json')
print(eng.search_hashtag(session=session,query="#covid"))
print(eng.search_iter_and_store(session=session,query="#covid",iter=2,use_cursor=False,cursor_path="#covid_cursor.txt"))
