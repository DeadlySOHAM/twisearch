from httpx import Client
import re
from random import randint
import json
from json.decoder import JSONDecodeError
import os
import time
import pandas as pd

#some regex
tweet_regex = re.compile(r'\"followers_count\":(\d+),\".*?\"location\":\"(.*?)\".*?\"screen_name\":\"(.*?)\".*?\"favorite_count\":(\d+),"favorited":\w+,\"full_text\":\"(.*?)\","is_quote_stat.*?,"reply_count":(\d+),\"retweet_count\":(\d+)')
cursor_regex = re.compile(r'"value":"(.*?)"')

#features
features={"responsive_web_graphql_exclude_directive_enabled":True,
          "verified_phone_label_enabled":True,
          "creator_subscriptions_tweet_preview_api_enabled":True,
          "responsive_web_graphql_timeline_navigation_enabled":True,
          "responsive_web_graphql_skip_user_profile_image_extensions_enabled":False,
          "c9s_tweet_anatomy_moderator_badge_enabled":True,
          "tweetypie_unmention_optimization_enabled":True,
          "responsive_web_edit_tweet_api_enabled":True,
          "graphql_is_translatable_rweb_tweet_is_translatable_enabled":True,
          "view_counts_everywhere_api_enabled":True,
          "longform_notetweets_consumption_enabled":True,
          "responsive_web_twitter_article_tweet_consumption_enabled":True,
          "tweet_awards_web_tipping_enabled":False,
          "freedom_of_speech_not_reach_fetch_enabled":True,
          "standardized_nudges_misinfo":True,
          "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":True,
          "rweb_video_timestamps_enabled":True,
          "longform_notetweets_rich_text_read_enabled":True,
          "longform_notetweets_inline_media_enabled":True,
          "responsive_web_media_download_video_enabled":False,
          "responsive_web_enhance_cards_enabled":False
          }


#helper function
def get_headers(session, **kwargs) -> dict:
    """
    Get the headers required for authenticated requests
    """
    cookies = session.cookies
    # todo httpx cookie issues
    try:
        if session._init_with_cookies:
            cookies.delete('ct0', domain='.twitter.com')
    except:
        ...
    headers = kwargs | {
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'cookie': '; '.join(f'{k}={v}' for k, v in cookies.items()),
        'referer': 'https://twitter.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        'x-csrf-token': cookies.get('ct0', ''),
        'x-guest-token': cookies.get('guest_token', ''),
        'x-twitter-auth-type': 'OAuth2Session' if cookies.get('auth_token') else '',
        'x-twitter-active-user': 'yes',
        'x-twitter-client-language': 'en',
    }
    return dict(sorted({k.lower(): v for k, v in headers.items()}.items()))

def build_params(params: dict) -> dict:
    return {k: json.dumps(v) for k, v in params.items()}

class Tweet:
    def __init__(self) -> None:
        self.__main_url = 'https://twitter.com/i/api/graphql/4c-S64XQJHuCJXBhG9JwZw/SearchTimeline'

    def auth(self,session_json:str)->Client:
        """method to autheticate a session

        params:
            session_json : str = a path to session.json file with the following cookie values
                                 ct0 and auth_token
        return:
            a httpx Client object for futher operations
        """
        if not os.path.exists(session_json):
            print("[-]Invalid json file")
            exit(0)

        f=open(session_json,'r')
        try:
            data=json.load(f)
        except JSONDecodeError:
            print("[-]Invalid json format")
            exit(0)
        
        if data.get("auth_token") and data.get("ct0"):
            auth_token , ct0 = data.get("auth_token"),data.get("ct0")
        else:
            print("[-]auth_token,ct0 must exists")
            exit(0)

        #prepare the client
        cookies = {
            "auth_token":auth_token,
            "ct0": ct0
        }

        client = Client(
            cookies=cookies,
            follow_redirects=True,
            timeout=None
        )
        client.headers.update(get_headers(session=client))
        return client
    
    def search_hashtag(self,session:Client,query:str,use_cursor:bool=False,cursor_path:str=None)->list:
        """method to search a hashtag and return the top and latest tweet

        params:
            session: Client = An authenticated Client session
            query: str = hashtag to search
            use_cursor: bool = True if you want to use a cursor False for default behaviour
            cursor_path: str = cursor file path to use the cursor. Format 
                                  latest_tweet_cursor:{cursor_data},top_tweet_cursor:{cursor_data}
        return:
            tweets: list = list(latest_tweet+top_tweets)
        P.S A query cursor file will be generated
        """

        query=query if query.startswith("#") else f"#{query}"

        #construct the parameters
        top_tweet_parametrs:dict={
            'variables':{
                "rawQuery":f"{query} lang:en",
                "count":"20",
                "querySource":"typed_query",
                "product":"Top"
            },
            'features':features
        }

        latest_tweet_parametrs:dict={
            'variables':{
                "rawQuery":f"{query} lang:en",
                "count":"20",
                "querySource":"typed_query",
                "product":"Latest"
            },
            'features':features
        }

        if use_cursor:
            if not os.path.exists(cursor_path):
                print("[-]Cursor doesn't exist")
                exit(0)
            f = open(cursor_path).read()
            latest_cursor,top_cursor =re.findall(r':(\w+)',f)

            top_tweet_parametrs["variables"]["cursor"] = top_cursor
            latest_tweet_parametrs["variables"]["cursor"] = latest_cursor

        #gather the top tweets
        
        top_response = session.get(
            self.__main_url,
            params=build_params(top_tweet_parametrs)

        )
        #print(top_response.text)
        if top_response.status_code == 403:
            print("[-]Authentication Failed")
            print("[-]Check cookies for error")
            exit(0)
        elif top_response.status_code > 403:
            print("[-]Something Wrong with the parameters")
            exit(0)

        #stupid way to get the tweet
        top_tweet = tweet_regex.findall(top_response.text)
        top_cursor = cursor_regex.findall(top_response.text)[0]
        
        latest_response = session.get(
                    self.__main_url,
                    params=build_params(latest_tweet_parametrs)
        )

        latest_tweet = tweet_regex.findall(latest_response.text)
        latest_cursor = cursor_regex.findall(latest_response.text)[0]

        #write the cursor to the file
        with open(f'{query}_cursor.txt','w') as f:
            f.write(f"latest_tweet_cursor:{latest_cursor},top_tweet_cursor:{top_cursor}")

        f.close()

        #print(f"[*]Cursor written to: {query}_cursor.txt")

        return latest_tweet+top_tweet

    def search_iter(self,session:Client,query:str,iter:int,use_cursor:bool=False,cursor_path:str=None)->list:
        """method to search a hashtag for a certain number of times and return the top and latest tweet
        
        params:
            session: Client = An authenticated Client session
            query: str = hashtag to search
            iter: int = no. of times
            use_cursor: bool = True if you want to use a cursor False for default behaviour
            cursor_path: str = cursor file path to use the cursor. Format 
                                  latest_tweet_cursor:{cursor_data},top_tweet_cursor:{cursor_data}
        return:
            tweets: list = list(latest_tweet+top_tweets)
        P.S A query cursor file will be generated
        """

        tweets :list = []

        for i in range(iter):
            if i != 0 :
                print(f"[*]Sleeping for {x} seconds")
                time.sleep(x)#sleep for a random amount of time
            print(f"[*]Iteration: {i}")
            if use_cursor:
                
                t = self.search_hashtag(session=session,query=query,use_cursor=use_cursor,cursor_path=cursor_path)
                tweets += t
            
            else:
                t = self.search_hashtag(session=session,query=query)
                tweets +=t
                use_cursor=True
                cursor_path=f'{query}_cursor.txt'

            x = randint(5,10)

        return tweets   

    def search_iter_and_store(self,session:Client,query:str,iter:int,use_cursor:bool=False,cursor_path:str=None) ->bool:
              """method to do an iter search and save in a csv file
              save path: csvs/{query}.csv
              """
        folder_path = "./csvs"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        data = self.search_iter(session,query,iter,use_cursor,cursor_path)
        try :
            pd.DataFrame(data={"text":data}).to_csv("./csvs/"+query+".csv",index=False)
            return True
        except Exception as e:
            print(e)
            return False
        
