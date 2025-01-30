from curl_cffi import requests
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, json, os, time

class Register:
    def __init__(self):
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/json",
            "Origin": "https://app.depined.org",
            "Referer": "https://app.depined.org",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": FakeUserAgent().random
        }
        self.proxies = []
        self.proxy_index = 0
        self.current_proxy = None

    def load_accounts(self):
        try:
            with open('config/register.txt', 'r') as f:
                accounts = []
                for line in f:
                    email, password = line.strip().split(':')
                    accounts.append({"email": email, "password": password})
                return accounts
        except FileNotFoundError:
            print(f"{Fore.RED}File config/register.txt not found{Style.RESET_ALL}")
            return []

    def load_ref_code(self):
        try:
            with open('ref_code.txt', 'r') as f:
                # Take first line only and strip whitespace
                return f.readline().strip()
        except FileNotFoundError:
            print(f"{Fore.RED}File ref_code.txt not found{Style.RESET_ALL}")
            return None

    def save_to_file(self, filename, content):
        with open(filename, 'a') as f:
            f.write(f"{content}\n")

    def load_proxies(self):
        try:
            with open('proxy.txt', 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            if self.proxies:
                print(f"{Fore.GREEN}Loaded {len(self.proxies)} proxies{Style.RESET_ALL}")
            return bool(self.proxies)
        except FileNotFoundError:
            print(f"{Fore.RED}File proxy.txt not found{Style.RESET_ALL}")
            return False

    def set_account_proxy(self):
        """Set a new proxy for the current account"""
        if not self.proxies:
            return None
        self.current_proxy = self.proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.current_proxy

    def register_user(self, email, password):
        url = 'https://api.depined.org/api/user/register'
        data = json.dumps({"email": email, "password": password})
        proxies = {"http": self.current_proxy, "https": self.current_proxy} if self.current_proxy else None
        
        try:
            response = requests.post(
                url=url,
                headers=self.headers,
                data=data,
                proxies=proxies,
                timeout=60,
                impersonate="chrome110"
            )
            response.raise_for_status()
            result = response.json()
            print(f"{Fore.GREEN}User registered successfully: {result.get('message')}{Style.RESET_ALL}")
            return result
        except Exception as e:
            print(f"{Fore.RED}Error registering user: {str(e)}{Style.RESET_ALL}")
            return None

    def user_login(self, email, password):
        url = 'https://api.depined.org/api/user/login'
        data = json.dumps({"email": email, "password": password})
        proxies = {"http": self.current_proxy, "https": self.current_proxy} if self.current_proxy else None
        
        try:
            response = requests.post(
                url=url,
                headers=self.headers,
                data=data,
                proxies=proxies,
                timeout=30,
                impersonate="chrome110"
            )
            if response.status_code == 403:
                print(f"{Fore.YELLOW}Cloudflare protection detected, retrying with different proxy...{Style.RESET_ALL}")
                return None
                
            response.raise_for_status()
            result = response.json()
            print(f"{Fore.GREEN}User Login successfully: {result.get('message')}{Style.RESET_ALL}")
            return result
        except Exception as e:
            print(f"{Fore.RED}Error Login user: {str(e)}{Style.RESET_ALL}")
            return None

    async def create_user_profile(self, token, payload):
        url = 'https://api.depined.org/api/user/profile-creation'
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}"
        }
        data = json.dumps(payload)
        proxies = {"http": self.current_proxy, "https": self.current_proxy} if self.current_proxy else None

        try:
            response = requests.post(
                url=url,
                headers=headers,
                data=data,
                proxies=proxies,
                timeout=60,
                impersonate="chrome110"
            )
            response.raise_for_status()
            result = response.json()
            print(f"{Fore.GREEN}Profile created successfully: {payload}{Style.RESET_ALL}")
            return result
        except Exception as e:
            print(f"{Fore.RED}Error creating profile: {str(e)}{Style.RESET_ALL}")
            return None

    def confirm_user_ref(self, token, referral_code):
        url = 'https://api.depined.org/api/access-code/referal'
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}"
        }
        # Clean up referral code 
        referral_code = referral_code.strip()
        data = json.dumps({"referral_code": referral_code})
        proxies = {"http": self.current_proxy, "https": self.current_proxy} if self.current_proxy else None

        print(f"\n{Fore.CYAN}Referral Request:{Style.RESET_ALL}")
        print(f"{Fore.GREEN}URL: {Style.RESET_ALL}{url}")
        print(f"{Fore.GREEN}Headers: {Style.RESET_ALL}{json.dumps(headers, indent=2)}")
        print(f"{Fore.GREEN}Payload: {Style.RESET_ALL}{data}\n")

        try:
            response = requests.post(
                url=url,
                headers=headers,
                data=data,
                proxies=proxies,
                timeout=60,
                impersonate="chrome110"
            )
            if response.status_code == 500:
                print(f"{Fore.YELLOW}Server error (500) during referral confirmation, will retry...{Style.RESET_ALL}")
                return None
                
            response.raise_for_status()
            result = response.json()
            if result:
                print(f"{Fore.GREEN}Referral response data: {result}{Style.RESET_ALL}")
            return result
        except Exception as e:
            print(f"{Fore.RED}Error confirming user referral: {str(e)}{Style.RESET_ALL}")
            return None

    async def main(self):
        ref_code = self.load_ref_code()
        if not ref_code:
            return

        accounts = self.load_accounts()
        if not accounts:
            return

        if not self.load_proxies():
            print(f"{Fore.YELLOW}Running without proxies{Style.RESET_ALL}")

        for account in accounts:
            try:
                # Set proxy for this account
                self.set_account_proxy()
                print(f"{Fore.CYAN}Using proxy: {self.current_proxy}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Trying to register email: {account['email']}{Style.RESET_ALL}")
                
                reg_response = None
                while not reg_response or not reg_response.get('data', {}).get('token'):
                    reg_response = self.register_user(account['email'], account['password'])
                    if not reg_response:
                        print(f"{Fore.YELLOW}Failed To Register, Retrying...{Style.RESET_ALL}")
                        await asyncio.sleep(3)
                
                token = reg_response['data']['token']

                # Add login step before profile creation
                login_response = None
                retry_count = 0
                while not login_response and retry_count < 5:
                    login_response = self.user_login(account['email'], account['password'])
                    if not login_response:
                        retry_count += 1
                        print(f"{Fore.YELLOW}Failed to login, retrying... ({retry_count}/5){Style.RESET_ALL}")
                        await asyncio.sleep(3)
                        continue
                
                if not login_response:
                    print(f"{Fore.RED}Failed to login after 5 attempts, skipping account{Style.RESET_ALL}")
                    continue

                token = login_response['data']['token']  # Use new token from login
                print(f"{Fore.CYAN}Trying to create profile for {account['email']}{Style.RESET_ALL}")
                
                profile1 = await self.create_user_profile(token, {"step": "username", "username": account['email']})
                if not profile1:
                    continue
                await asyncio.sleep(3)     
                profile2 = await self.create_user_profile(token, {"step": "description", "description": "AI Startup"})
                if not profile2:
                    continue
                await asyncio.sleep(3)
                confirm = None
                retry_count = 0
                max_retries = 10  # Increase max retries
                
                while not confirm or not confirm.get('data', {}).get('token'):
                    if retry_count >= max_retries:
                        print(f"{Fore.RED}Max retries reached for referral confirmation{Style.RESET_ALL}")
                        break
                        
                    confirm = self.confirm_user_ref(token, ref_code)
                    if not confirm:
                        retry_count += 1
                        delay = min(30, 3 * retry_count)  # Progressive delay up to 30 seconds
                        print(f"{Fore.YELLOW}Failed To Confirm Referral, Retrying in {delay} seconds... (Attempt {retry_count}/{max_retries}){Style.RESET_ALL}")
                        await asyncio.sleep(delay)
                        continue
                
                if confirm and confirm.get('data', {}).get('token'):
                    self.save_to_file("./result/accounts.txt", f"{account['email']}|{account['password']}")
                    self.save_to_file("./result/tokens.txt", confirm['data']['token'])
                    print(f"{Fore.GREEN}Successfully registered and confirmed referral for {account['email']}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Failed to confirm referral for {account['email']} after {max_retries} attempts{Style.RESET_ALL}")
                
                await asyncio.sleep(5)  # Increased delay between accounts

            except Exception as e:
                print(f"{Fore.RED}Error creating account: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        register = Register()
        asyncio.run(register.main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Process interrupted by user{Style.RESET_ALL}")
