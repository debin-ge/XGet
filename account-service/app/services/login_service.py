from playwright.async_api import async_playwright
from typing import Dict
from ..core.logging import logger
from ..core.config import settings
from .proxy_client import ProxyClient
import time
from ..models.account import Account
from ..schemas.proxy import Proxy

class LoginService:
    async def login_with_twitter(self, account: Account, proxy: Proxy) -> Dict:
        """使用Twitter账号密码登录"""
        cookies_dict = {}
        proxy_client = ProxyClient()
        login_success = "FAILED"
        
        async with async_playwright() as p:
            proxy_server = f"{proxy.type.lower()}://{proxy.ip}:{proxy.port}"
            
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox', 
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-gpu',
                    '--single-process',
                    '--disable-extensions', 
                    '--disable-infobars',
                ]
            )
            
            context = await browser.new_context(
                proxy={
                    "server": proxy_server,
                    "username": proxy.username,
                    "password": proxy.password
                }
            )
            
            page = await context.new_page()

            start_time = time.time()
            
            try:
                # 访问登录页面
                await page.goto("https://x.com/login", timeout=30000)
                await page.wait_for_timeout(3000)

                # 填写用户名
                username_input = await page.query_selector('input[name="text"]')
                if not username_input:
                    return {}
                await username_input.fill(account.username)
                
                # 点击下一步
                next_btn = await page.query_selector('button:has-text("Next")')
                if not next_btn:
                    return {}
                await next_btn.click()
                await page.wait_for_timeout(2000)
                
                # 填写密码
                password_input = await page.query_selector('input[name="password"]')
                if not password_input:
                    return {}
                await password_input.fill(account.password)
                                
                # 点击登录
                login_btn = await page.query_selector('button[data-testid="LoginForm_Login_Button"]')
                if not login_btn:
                    return {}
                await login_btn.click()
                await page.wait_for_timeout(10000)
                                
                # 等待跳转到主页
                await page.wait_for_url("https://x.com/home", timeout=15000)
                                
                # 获取cookies
                cookies = await context.cookies()
                cookies_dict = {c['name']: c['value'] for c in cookies}
                login_success = "SUCCESS" if len(cookies_dict) > 0 else "FAILED"
                
            except Exception as e:
                logger.error(f"登录失败: {e}")
                raise e

            finally:
                await browser.close()
        
                await proxy_client.record_proxy_usage(
                    proxy_id=proxy.id, 
                    success=login_success,
                    account_id=account.id,
                    service_name=settings.PROJECT_NAME,
                    response_time=int((time.time() - start_time) * 1000),
                    proxy_ip=proxy.ip,
                    proxy_port=proxy.port,
                    account_username_email=account.username or account.email,
                    latency=proxy.latency
                )
                
        return cookies_dict
    
    async def login_with_google(self, account: Account, proxy: Proxy) -> Dict:
        """使用Google账号登录Twitter"""
        cookies_dict = {}
        proxy_client = ProxyClient()
        login_success = "FAILED"
        
        async with async_playwright() as playwright:
            proxy_server = f"{proxy.type.lower()}://{proxy.ip}:{proxy.port}"
            device = playwright.devices["Desktop Chrome"]
            
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox', 
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-gpu',
                    '--disable-extensions', 
                    '--disable-infobars',
                    '--disable-site-isolation-trials',
                    '--disable-dev-shm-usage',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            
            context = await browser.new_context(
                **device,
                proxy={
                    "server": proxy_server,
                    "username": proxy.username,
                    "password": proxy.password
                }
            )
            
            page = await context.new_page()

            start_time = time.time()
            
            try:
                # 打开登录页
                await page.goto("https://x.com/login")
                await page.wait_for_timeout(3000)

                # 查找Google登录iframe
                iframe_element = await page.query_selector('iframe[title*="Google"]')
                if not iframe_element:
                    logger.error(f"未找到Google登录iframe")
                    return {}

                google_frame = await iframe_element.content_frame()
                if not google_frame:
                    logger.error(f"未找到Google登录iframe")
                    return {}

                # 查找Google登录按钮
                google_btn = await google_frame.query_selector('div[role="button"], button')
                if not google_btn:
                    logger.error(f"未找到Google登录按钮")
                    return {}

                # 点击Google登录，获取弹窗
                async with page.expect_popup() as popup_info:
                    await google_btn.click()
                popup = await popup_info.value
                await popup.wait_for_load_state('domcontentloaded')

                # 填写邮箱
                email_selectors = [
                    'input[type="email"]',
                    'input[name="identifier"]',
                    '#identifierId'
                ]
                email_input = None
                for selector in email_selectors:
                    try:
                        email_input = await popup.wait_for_selector(selector, timeout=5000)
                        if email_input:
                            break
                    except Exception:
                        continue
                if not email_input:
                    logger.error(f"未找到邮箱输入框")
                    return {}

                await email_input.fill(account.email)

                # 点击"下一步"
                await popup.click('#identifierNext button', timeout=5000)
                await popup.wait_for_timeout(5000)

                # 填写密码
                password_selectors = [
                    'input[type="password"]',
                    'input[name="Passwd"]',
                    'input[autocomplete="current-password"]'
                ]
                password_input = None
                for selector in password_selectors:
                    try:
                        password_input = await popup.wait_for_selector(selector, timeout=8000)
                        if password_input:
                            break
                    except Exception:
                        continue
                if not password_input:
                    logger.error(f"未找到密码输入框")
                    return {}

                await password_input.fill(account.email_password)

                # 点击"下一步"并等待弹窗关闭
                await popup.click('#passwordNext button')
                try:
                    await popup.wait_for_event("close", timeout=30000)
                except Exception:
                    pass

                # 等待主页面跳转
                try:
                    await page.wait_for_url("https://x.com/home", timeout=20000)
                except Exception:
                    pass

                # 获取cookies
                cookies = await context.cookies()
                cookies_dict = {c['name']: c['value'] for c in cookies}
                login_success = "SUCCESS" if len(cookies_dict) > 0 else "FAILED"

            except Exception as e:
                logger.error(f"Google登录流程异常: {e}")
                raise e

            finally:
                await browser.close()
        
                await proxy_client.record_proxy_usage(
                    proxy_id=proxy.id, 
                    success=login_success,
                    account_id=account.id,
                    service_name=settings.PROJECT_NAME,
                    response_time=int((time.time() - start_time) * 1000),
                    proxy_ip=proxy.ip,
                    proxy_port=proxy.port,
                    account_username_email=account.email or account.username,
                    latency=proxy.latency
                )

        return cookies_dict
