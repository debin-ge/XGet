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

            # 构造Account对象
            acc_obj = Account(
                username=account['username'],
                password=account["password"],
                email=account["email"],
                email_password=account.get("email_password", ""),
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                active=False,
                locks={},
                stats={},
                headers={},
                cookies=None,
                mfa_code=None,
                # proxy=None, # 暂时先不考虑代理
                proxy=f"{proxy['type'].lower()}://{proxy['user']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}",
                error_msg=None,
                last_used=None,
                _tx=None
            )

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
        browser = await p.chromium.launch(
            headless=True,
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            proxy={
                "server": proxy_server,
                "username": proxy["user"],
                "password": proxy["password"]
            }
        )
        page = await context.new_page()
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