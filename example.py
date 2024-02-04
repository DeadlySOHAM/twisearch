from tweet_search import Tweet

eng = Tweet()

session = eng.auth(session_json='test.json')
print(eng.search_hashtag(session=session,query="#covid"))
print(eng.search_iter(session=session,query="#covid",iter=5,use_cursor=True,cursor_path="#covid_cursor.txt"))