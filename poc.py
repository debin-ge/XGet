import asyncio
import json
import os
import random
from typing import List, Dict
from playwright.async_api import async_playwright
from twscrape import API
from twscrape.account import Account

ACCOUNTS_FILE = "accounts.txt"
PROXY_FILE = "proxy.txt"

def print_add_accounts_guide():
    """添加用户操作指南"""
    print("用户添加指南")
    print("=" * 60)
    
    print("\n 当前目录下创建accounts.txt")
    print("1. 打开accounts.txt文件并按行添加用户信息")
    print("2. 用户信息格式如下：")
    print("\t username:password:email:email_password")
    print("3. 保存并退出文件")
    print("\n=" * 60)

def load_proxys_from_file(file_path=PROXY_FILE) -> List[Dict]:
    proxys = []
    if not os.path.exists(file_path):
        print(f"❌ 未找到代理文件: {file_path}")
        return proxys
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            parts = line.split("|")
            if len(parts) < 5:
                print(f"⚠️ 代理格式错误: {line}")
                continue
            proxy = {
                "type": parts[0],
                "ip": parts[1],
                "port": parts[2],
                "user": parts[3],
                "password": parts[4],
            }
            proxys.append(proxy)
    print(f"✅ 读取到 {len(proxys)} 个代理")
    return proxys

    google_accounts = []
    if not os.path.exists(file_path):
        print(f"❌ 未找到Google账号文件: {file_path}")
        return google_accounts
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            parts = line.split(":")
            if len(parts) < 2:
                print(f"⚠️ Google账号格式错误: {line}")
                continue
            google_accounts.append({"email": parts[0], "password": parts[1]})
    print(f"✅ 读取到 {len(google_accounts)} 个Google账号")
    return google_accounts

# 新增：Google账号登录方法
async def playwright_login_with_google(account: Dict, google_account: Dict, proxy: Dict) -> Dict:
    async with async_playwright() as p:
        proxy_server = f"{proxy['type'].lower()}://{proxy['ip']}:{proxy['port']}"
        print(f"使用代理: {proxy_server}")
        playwright = await async_playwright().start()
        device = playwright.devices["Desktop Chrome"]
        browser = await playwright.chromium.launch(
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
                '--disable-site-isolation-trials',
                '--disable-dev-shm-usage',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        context = await browser.new_context(
            **device,
            # proxy={
            #     "server": proxy_server,
            #     "username": proxy["user"],
            #     "password": proxy["password"]
            # }
        )
        page = await context.new_page()
        await page.goto("https://x.com/login", timeout=30000)
        await page.wait_for_timeout(5000)
        # 1. 查找包含Google登录按钮的iframe
        iframe_element = await page.query_selector('iframe[title*="Google"]')
        if not iframe_element:
            print("❌ 未找到Google登录iframe")
            await page.screenshot(path="not_find_google_iframe1.png")
            await browser.close()
            return {}

        # 2. 获取iframe的frame对象
        google_frame = await iframe_element.content_frame()
        if not google_frame:
            print("❌ 无法获取Google登录iframe的frame对象")
            await page.screenshot(path="not_find_google_frame2.png")
            await browser.close()
            return {}

        # 3. 在iframe内部查找Google登录按钮
        google_btn = await google_frame.query_selector('div[role="button"], button')
        if not google_btn:
            print("❌ 未找到Google登录按钮（iframe内）")
            await google_frame.screenshot(path="not_find_google_login_button.png")
            await browser.close()
            return {}
        
        async with page.expect_popup() as popup_info:
            await google_btn.click()
        popup = await popup_info.value
        await popup.wait_for_load_state('domcontentloaded')

        try:
            selectors = [
                'input[type="email"]',
                'input[name="identifier"]',
                '#identifierId'
            ]
            email_input = None
            for selector in selectors:
                try:
                    email_input = await popup.wait_for_selector(selector, timeout=5000)
                    if email_input:
                        break
                except Exception:
                    continue
            
            if not email_input:
                print("❌ 未找到 email 输入框")
                await popup.screenshot(path="not_find_email_pagqqe.png")
                return {}

            await email_input.fill(google_account["email"])

            await popup.screenshot(path="google_login.png")

            await popup.click('#identifierNext button', timeout=20000)
            await popup.wait_for_timeout(5000)
                        
            password_selectors = [
                'input[type="password"]',
                'input[name="Passwd"]'
            ]
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = await popup.wait_for_selector(selector, timeout=5000)
                    if password_input:
                        break
                except Exception:
                    continue

            if not password_input:
                print("❌ 未找到 password 输入框")
                await popup.screenshot(path="not_find_password_pagqqe.png")
                return {}

            await password_input.fill(google_account["email_password"])
            print("成功输入密码")

            await popup.click('#passwordNext button')
            await popup.wait_for_close(timeout=30000)
        except Exception as e:
            print(f"❌ Google登录弹窗流程失败: {e}")
            await popup.screenshot(path="google_login_error.png")
            await browser.close()
            return {}
        
        try:
            await page.wait_for_url("https://x.com/home", timeout=20000)
            print(f"🎉 Google账号登录成功: {account['username']}")
        except Exception as e:
            print(f"⚠️ Google登录后未跳转主页: {e}")
        cookies = await context.cookies()
        await browser.close()
        cookies_dict = {c['name']: c['value'] for c in cookies}
        print(f"cookies is:{cookies_dict}")
        return cookies_dict

# 修改：注册账号时支持选择登录方式
def ask_login_method() -> str:
    print("请选择登录方式：")
    print("1. Twitter账号密码登录")
    print("2. Google账号登录")
    choice = input("输入1或2: ").strip()
    return choice

async def load_accounts_from_file(file_path=ACCOUNTS_FILE):
    if not os.path.exists(file_path):
        print(f"❌ 未找到账号文件: {file_path}")
        return
    proxys = load_proxys_from_file()
    if not proxys:
        print("❌ 没有代理，退出")
        return
    api = API()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            parts = line.split(":")
            if len(parts) < 4:
                print(f"⚠️ 账号格式错误: {line}")
                continue
            account = {
                "username": parts[0],
                "password": parts[1],
                "email": parts[2],
                "email_password": parts[3] if len(parts) > 3 else ""
            }
            proxy = random.choice(proxys)
            acc_obj = Account(
                username=account['username'],
                password=account["password"],
                email=account["email"],
                email_password=account.get("email_password", ""),
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
                active=False,
                locks={},
                stats={},
                headers={},
                cookies=None,
                mfa_code=None,
                proxy=f"{proxy['type'].lower()}://{proxy['user']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}",
                error_msg=None,
                last_used=None,
                _tx=None
            )
            login_method = ask_login_method()
            if login_method == "2":
                if not account["email"]:
                    print("❌ 没有可用的Google账号，跳过")
                    continue

                cookies = await playwright_login_with_google(account, account, proxy)
            else:
                cookies = await playwright_login_and_get_cookies(account, proxy)
            if cookies:
                acc_obj.cookies = cookies
                acc_obj.active = True
            await api.pool.save(acc_obj)
            print(f"✅ 已保存账号: {account['username']},账号状态为：{acc_obj.active}")


async def playwright_login_and_get_cookies(account: Dict, proxy: Dict) -> Dict:
    async with async_playwright() as p:
        proxy_server = f"{proxy['type'].lower()}://{proxy['ip']}:{proxy['port']}"
        print(f"使用代理: {proxy_server}")
        playwright = await async_playwright().start()
        device = playwright.devices["Desktop Chrome"]
        browser = await playwright.chromium.launch(
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
            **device,
            proxy={
                "server": proxy_server,
                "username": proxy["user"],
                "password": proxy["password"]
            }
        )
        page = await context.new_page()
        await page.set_extra_http_headers({
            "x-csrf-token":"d8875e40e12e8c0b24e62087e385209440c2ccc9bea0168b05d96633b42035500f83d03d6d4d03d84d38ca30ce95ddd3bfb66dcd50302e1c7a90cf40805d83e34ac83b3dec4e8b901334e79486b6751d",
            "x-xp-forwarded-for":"fb3f200e68bcbedba07d6d5fc31906a3283db4bcf868292225d8b2f14255e33fc6a4a745da95758456bdc974bc2d7932c4bfad7e7f538e7e6b5abc9e80a339ba1228be5000d5b55b550e239d9251f2be777500b4ab5bb009cf990f3443e036cc3cf26d2b00b473f21dca36b9b3ae498fa8ffd08e908503ffc1e3c0e80bf138875c809ea2bed790e24751a1993477b47995223d65f61edd8801f8d829ccdda9a47962cbade91eaa969479f355a8e6c999f6fa064e91c9316796f013d67ba8f706805f400283fddbc5ddd3981765aa0854e075f6deb0bfd95fccc5709c11422fdfa6fca17b028a5f52bf736f809f126e215e1023dd74da5509327e20725c38b6cf"
        })
        try:
            response = await page.goto("https://x.com/login", timeout=30000)
            if not response or response.status != 200:
                print(f"❌ 访问失败，状态码: {response.status if response else 'None'}")
                await page.screenshot(path="login_error_page.png")
                await browser.close()
                return {}
            await page.wait_for_timeout(3000)
            username_input = await page.query_selector('input[name="text"]')
            if not username_input:
                print(f"❌ 未找到用户名输入框: {account['username']}")
                await page.screenshot(path="not_find_username_page.png")
                await browser.close()
                return {}
            await username_input.fill(account["username"])
            next_btn = await page.query_selector('button:has-text("Next")')
            if not next_btn:
                print(f"❌ 未找到Next按钮: {account['username']}")
                await page.screenshot(path="not_find_next_page.png")
                await browser.close()
                return {}
            await next_btn.click()
            await page.wait_for_timeout(2000)
            password_input = await page.query_selector('input[name="password"]')
            if not password_input:
                print(f"❌ 未找到密码输入框: {account['username']}")
                await page.screenshot(path="not_find_password_page.png")
                await browser.close()
                return {}
            await password_input.fill(account["password"])
            login_btn = await page.query_selector('button[data-testid="LoginForm_Login_Button"]')
            if not login_btn:
                print(f"❌ 未找到登录按钮: {account['username']}")
                await page.screenshot(path="not_find_login_button_page.png")
                await browser.close()
                return {}
            await login_btn.click()
            
            await page.wait_for_url("https://x.com/home", timeout=15000)
            print(f"🎉 登录成功: {account['username']}")
        except Exception as e:
            print(f"⚠️ 访问失败: {account['username']} {e}")
        cookies = await context.cookies()
        await browser.close()
        # 转为dict格式
        cookies_dict = {c['name']: c['value'] for c in cookies}
        return cookies_dict

async def load_accounts():
    api = API()
    accounts = await api.pool.get_all()
    for acc in accounts:
        print(f"用户名：{acc}")

async def run_core_tests():
    from test_twscrape import test_basic_api, test_search_functionality, test_user_functionality
    print("\n🧪 开始核心功能测试...")
    await test_basic_api()
    await test_search_functionality()
    await test_user_functionality()
    print("\n✅ 核心功能测试完成")

async def main():
    """主函数"""
    print("🚀 Twitter 数据抓取工具")
    print("=" * 60)
    
    while True:
        print("\n请选择操作:")
        print("1. 查看添加用户指南")
        print("2. 注册用户")
        print("3. 查看用户")
        print("4. 数据抓取")
        print("5. 退出")
        
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == "1":
            print_add_accounts_guide()
        elif choice == "2":
            await load_accounts_from_file()
        elif choice == "3":
            await load_accounts()
        elif choice == "4":
            await run_core_tests()
        elif choice == "5":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  操作中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
    finally:
        # 兼容性处理，防止 event loop 已关闭时的警告
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.close()
        except Exception:
            pass