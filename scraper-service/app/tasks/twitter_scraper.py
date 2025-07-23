from typing import Dict, List, Any, Optional
import asyncio
from twscrape import API
from twscrape.account import Account
from twscrape.models import Tweet, User
from ..schemas.result import ResultCreate
from ..models.result import RESULT_TYPE_TWEET, RESULT_TYPE_USER, RESULT_TYPE_TOPIC, RESULT_TYPE_FOLLOWER


class TwitterScraper:
    def __init__(self, account_info: Dict, proxy_info: Optional[Dict] = None):
        self.account_info = account_info
        self.proxy_info = proxy_info
        self.api = API()
        self.account = None

    async def setup(self) -> bool:
        """设置Twitter API"""
        try:
            # 创建账号对象
            proxy = None
            if self.proxy_info:
                proxy_auth = ""
                if self.proxy_info.get("username") and self.proxy_info.get("password"):
                    proxy_auth = f"{self.proxy_info['username']}:{self.proxy_info['password']}@"
                    
                proxy = f"{self.proxy_info['type'].lower()}://{proxy_auth}{self.proxy_info['ip']}:{self.proxy_info['port']}"
                
            self.account = Account(
                username=self.account_info["username"],
                password=self.account_info.get("password", ""),
                email=self.account_info.get("email", ""),
                email_password=self.account_info.get("email_password", ""),
                user_agent=self.account_info.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"),
                active=True,
                locks={},
                stats={},
                headers=self.account_info.get("headers", {}),
                cookies=self.account_info.get("cookies", {}),
                mfa_code=None,
                proxy=proxy,
                error_msg=None,
                last_used=None,
                _tx=None
            )
            
            # 添加账号到API
            await self.api.pool.add_account(self.account)
            
            # 检查账号是否可用
            accounts = await self.api.pool.get_accounts()
            if not accounts:
                return False
                
            return True
        except Exception as e:
            print(f"设置Twitter API失败: {e}")
            return False

    async def get_user_info(self, username: str) -> Optional[ResultCreate]:
        """获取用户信息"""
        try:
            user = await self.api.user_by_screen_name(username)
            if not user:
                return None
                
            return ResultCreate(
                task_id="",  # 由调用者设置
                data_type=RESULT_TYPE_USER,
                data=user.dict(),
                metadata={
                    "source": "twitter",
                    "username": username
                }
            )
        except Exception as e:
            print(f"获取用户信息失败: {e}")
            return None

    async def get_user_tweets(
        self, 
        username: str, 
        limit: int = 100, 
        include_replies: bool = False, 
        include_retweets: bool = False
    ) -> List[ResultCreate]:
        """获取用户推文"""
        results = []
        try:
            tweets = []
            async for tweet in self.api.user_tweets(username, limit=limit):
                # 过滤回复和转发
                if not include_replies and tweet.in_reply_to_status_id:
                    continue
                if not include_retweets and tweet.retweeted_status_id:
                    continue
                    
                tweets.append(tweet)
                if len(tweets) >= limit:
                    break
                    
            for tweet in tweets:
                result = ResultCreate(
                    task_id="",  # 由调用者设置
                    data_type=RESULT_TYPE_TWEET,
                    data=tweet.dict(),
                    metadata={
                        "source": "twitter",
                        "username": username,
                        "tweet_id": tweet.id
                    }
                )
                results.append(result)
        except Exception as e:
            print(f"获取用户推文失败: {e}")
            
        return results

    async def search_tweets(self, query: str, limit: int = 100) -> List[ResultCreate]:
        """搜索推文"""
        results = []
        try:
            tweets = []
            async for tweet in self.api.search(query, limit=limit):
                tweets.append(tweet)
                if len(tweets) >= limit:
                    break
                    
            for tweet in tweets:
                result = ResultCreate(
                    task_id="",  # 由调用者设置
                    data_type=RESULT_TYPE_TWEET,
                    data=tweet.dict(),
                    metadata={
                        "source": "twitter",
                        "query": query,
                        "tweet_id": tweet.id
                    }
                )
                results.append(result)
        except Exception as e:
            print(f"搜索推文失败: {e}")
            
        return results

    async def get_followers(self, username: str, limit: int = 100) -> List[ResultCreate]:
        """获取用户粉丝"""
        results = []
        try:
            followers = []
            async for follower in self.api.followers(username, limit=limit):
                followers.append(follower)
                if len(followers) >= limit:
                    break
                    
            for follower in followers:
                result = ResultCreate(
                    task_id="",  # 由调用者设置
                    data_type=RESULT_TYPE_FOLLOWER,
                    data=follower.dict(),
                    metadata={
                        "source": "twitter",
                        "target_username": username,
                        "follower_username": follower.screen_name
                    }
                )
                results.append(result)
        except Exception as e:
            print(f"获取用户粉丝失败: {e}")
            
        return results

    async def get_topic_tweets(self, topic: str, limit: int = 100) -> List[ResultCreate]:
        """获取话题相关推文"""
        # 话题搜索实际上就是搜索带有特定话题标签的推文
        return await self.search_tweets(f"#{topic}", limit)

    async def close(self):
        """关闭Twitter API"""
        if self.api:
            await self.api.pool.close()