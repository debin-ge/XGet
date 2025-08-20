from typing import Dict, List, Any, Optional
import asyncio
from twscrape import API
from twscrape.account import Account
from twscrape.models import Tweet, User
from ..schemas.result import ResultCreate
from ..models.result import RESULT_TYPE_TWEET, RESULT_TYPE_USER, RESULT_TYPE_TOPIC, RESULT_TYPE_FOLLOWER
from ..core.logging import logger
from twscrape.utils import utc


class TwitterScraper:
    def __init__(self, account_info: Dict, proxy_info: Optional[Dict] = None):
        self.account_info = account_info
        self.proxy_info = proxy_info
        self.api = API()
        self.account = None
        self._cancelled = False

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
            await self.api.pool.save(self.account)
            # 设置锁定时间为30分钟（1800秒）
            lock_duration = 1800
            await self.api.pool.lock_until(self.account_info["username"] if self.account_info["username"] else self.account_info["email"], "search", utc.ts() + lock_duration)
            
            logger.info(f"Twitter API设置成功, username: {self.account_info["username"] if self.account_info["username"] else self.account_info["email"]}")
            return True
        except Exception as e:
            logger.error(f"设置Twitter API失败, Error: {str(e)}")
            await self.cleanup()
            return False

    async def cleanup(self):
        """清理资源"""
        try:
            if self.account and self.api:
                # 释放账号锁定
                await self.api.pool.unlock(self.account_info["username"] if self.account_info["username"] else self.account_info["email"], "search")
                logger.info(f"已释放账号锁定: {self.account_info["username"] if self.account_info["username"] else self.account_info["email"]}")
        except Exception as e:
            logger.warning(f"清理资源时发生异常: {e}")

    def cancel(self):
        """取消操作"""
        self._cancelled = True
        logger.info("Twitter scraper 操作已取消")

    def _check_cancelled(self):
        """检查是否已取消"""
        if self._cancelled:
            raise asyncio.CancelledError("操作已被取消")

    async def get_user_info(self, username: str) -> Optional[ResultCreate]:
        """获取用户信息"""
        try:
            self._check_cancelled()
            users = []
            logger.info(f"正在获取用户信息, username: {username}")
            async for user in self.api.search_user(username, limit=1):
                self._check_cancelled()
                users.append(user)
                if len(users) >= 1:
                    break
            
            if not users:
                logger.warning(f"未找到用户, username: {username}")
                return None
            logger.info(f"用户信息: {users}")
            return ResultCreate(
                task_id="",  # 由调用者设置
                data_type=RESULT_TYPE_USER,
                data=users[0].dict(),
                metadata={
                    "source": "twitter",
                    "username": username
                }
            )
        except asyncio.CancelledError:
            logger.info(f"获取用户信息被取消, username: {username}")
            raise
        except Exception as e:
            logger.error(f"获取用户信息失败, username: {username}, error: {str(e)}")
            return None

    async def get_user_tweets_stream(
        self, 
        uid: str, 
        limit: int = 5, 
        include_replies: bool = False, 
        include_retweets: bool = False
    ):
        """获取用户推文（流式）"""
        try:
            self._check_cancelled()
            logger.info(f"开始流式获取用户推文, username: {uid}, limit: {limit}, include_replies: {include_replies}, include_retweets: {include_retweets}")
            
            count = 0
            
            async for tweet in self.api.user_tweets(uid):
                self._check_cancelled()
                
                # 检查是否已达到目标limit
                if count >= limit:
                    break
                
                # 过滤回复和转发
                if not include_replies and tweet.in_reply_to_status_id:
                    continue
                if not include_retweets and tweet.retweeted_status_id:
                    continue
                    
                result = ResultCreate(
                    task_id="",  # 由调用者设置
                    data_type=RESULT_TYPE_TWEET,
                    data=tweet.dict(),
                    metadata={
                        "source": "twitter",
                        "username": uid,
                        "tweet_id": tweet.id
                    }
                )
                yield result
                count += 1

            logger.info(f"流式获取用户推文完成, username: {uid}, 实际获取: {count}")
        except asyncio.CancelledError:
            logger.info(f"流式获取用户推文被取消, username: {uid}")
            raise
        except Exception as e:
            logger.error(f"流式获取用户推文失败, username: {uid}, error: {str(e)}")
            raise

    async def search_tweets_stream(self, query: str, limit: int = 5):
        """搜索推文（流式）"""
        try:
            self._check_cancelled()
            logger.info(f"开始流式搜索推文, query: {query}, limit: {limit}")

            count = 0
            
            async for tweet in self.api.search(query):
                self._check_cancelled()
                
                # 检查是否已达到目标limit
                if count >= limit:
                    break
                
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
                yield result
                count += 1
                    
            logger.info(f"流式搜索推文完成, query: {query}, 实际获取: {count}")
        except asyncio.CancelledError:
            logger.info(f"流式搜索推文被取消, query: {query}")
            raise
        except Exception as e:
            logger.error(f"流式搜索推文失败, query: {query}, error: {str(e)}")
            raise

    async def get_followers_stream(self, uid: str, limit: int = 100):
        """获取用户粉丝（流式）"""
        try:
            self._check_cancelled()
            logger.info(f"开始流式获取用户粉丝, uid: {uid}, limit: {limit}")
            
            count = 0
            
            async for follower in self.api.followers(uid):
                self._check_cancelled()
                
                # 检查是否已达到目标limit
                if count >= limit:
                    break
                
                result = ResultCreate(
                    task_id="",  # 由调用者设置
                    data_type=RESULT_TYPE_FOLLOWER,
                    data=follower.dict(),
                    metadata={
                        "source": "twitter",
                        "target_username": follower.display_name,
                        "follower_username": follower.screen_name
                    }
                )
                yield result
                count += 1
                    
            logger.info(f"流式获取用户粉丝完成, uid: {uid}, 实际获取: {count}")
        except asyncio.CancelledError:
            logger.info(f"流式获取用户粉丝被取消, uid: {uid}")
            raise
        except Exception as e:
            logger.error(f"流式获取用户粉丝失败, uid: {uid}, error: {str(e)}")
            raise

    async def get_topic_tweets_stream(self, topic: str, limit: int = 100):
        """获取话题相关推文（流式）"""
        try:
            self._check_cancelled()
            logger.info(f"开始流式获取话题推文, topic: {topic}, limit: {limit}")
            
            async for result in self.search_tweets_stream(f"#{topic}", limit):
                self._check_cancelled()
    
                # 更新metadata中的话题信息
                result.metadata.update({
                    "topic": topic,
                    "query": f"#{topic}"
                })
                
                yield result
                
            logger.info(f"流式获取话题推文完成, topic: {topic}")
        except asyncio.CancelledError:
            logger.info(f"流式获取话题推文被取消, topic: {topic}")
            raise
        except Exception as e:
            logger.error(f"流式获取话题推文失败, topic: {topic}, error: {str(e)}")
            raise

    async def get_following_stream(self, uid: str, limit: int = 100):
        """获取用户关注列表（流式）"""
        try:
            self._check_cancelled()
            logger.info(f"开始流式获取用户关注列表, uid: {uid}, limit: {limit}")
            
            count = 0
            
            async for following in self.api.following(uid):
                self._check_cancelled()
                
                # 检查是否已达到目标limit
                if count >= limit:
                    break
                
                result = ResultCreate(
                    task_id="",  # 由调用者设置
                    data_type=RESULT_TYPE_USER,  # 关注的用户信息
                    data=following.dict(),
                    metadata={
                        "source": "twitter",
                        "target_username": uid,
                        "following_username": following.displayname,
                        "relationship_type": "following"
                    }
                )
                yield result
                count += 1
                    
            logger.info(f"流式获取用户关注列表完成, uid: {uid}, 实际获取: {count}")
        except asyncio.CancelledError:
            logger.info(f"流式获取用户关注列表被取消, uid: {uid}")
            raise
        except Exception as e:
            logger.error(f"流式获取用户关注列表失败, uid: {uid}, error: {str(e)}")
            raise
