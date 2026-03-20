import re
with open('app/services/twitter_service.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Patch _init_client to support force_relogin and reading credentials from .env
init_client_old = '''    async def _init_client(self):
        """Initialize Twikit client with cookies"""
        if self.initialized:
            return'''
            
init_client_new = '''    async def _init_client(self, force_relogin: bool = False):
        """Initialize Twikit client with cookies or fallback to .env credentials"""
        if self.initialized and not force_relogin:
            return
        self.initialized = False'''
        
if init_client_old in code:
    code = code.replace(init_client_old, init_client_new)

load_cookies_old = '''            if not os.path.exists(self.cookies_path):
                raise FileNotFoundError(f"Twitter cookies not found at {self.cookies_path}")
            self.client = Client(language="en-US")
            self.client.load_cookies(self.cookies_path)'''

load_cookies_new = '''            self.client = Client(language="en-US")
            if force_relogin or not os.path.exists(self.cookies_path):
                import os
                logger.warning("Attempting Twikit login via .env credentials...")
                username = os.environ.get("TWITTER_USERNAME", "syman763255")
                email = os.environ.get("TWITTER_EMAIL", "spymanxavier@gmail.com")
                password = os.environ.get("TWITTER_PASSWORD", "9421150039")
                await self.client.login(auth_info_1=username, auth_info_2=email, password=password)
                self.client.save_cookies(self.cookies_path)
            else:
                self.client.load_cookies(self.cookies_path)'''

if load_cookies_old in code:
    code = code.replace(load_cookies_old, load_cookies_new)


# 2. Patch the exact place where KEY_BYTE happens. The user mentioned _scrape_queries
# If it's not exactly that name, let's just find "await self.client.search_tweet"
# and wrap it in the retry block. Actually, the user's snippet was:
search_regex = re.compile(r'(\s+)([\w_]+)\s*=\s*await self\.client\.search_tweet\((.*?)\)')
def replace_search(match):
    indent = match.group(1)
    assignment = match.group(2)
    args = match.group(3)
    return f'''{indent}try:
{indent}    {assignment} = await self.client.search_tweet({args})
{indent}except Exception as e:
{indent}    if "KEY_BYTE" in str(e):
{indent}        logger.warning("KEY_BYTE error — refreshing client and retrying")
{indent}        await self._init_client(force_relogin=True)
{indent}        import asyncio
{indent}        await asyncio.sleep(5)
{indent}        try:
{indent}            {assignment} = await self.client.search_tweet({args})
{indent}        except Exception as retry_e:
{indent}            logger.error(f"Retry also failed: {{retry_e}}")
{indent}            continue
{indent}    else:
{indent}        logger.error(f"Query failed: {{e}}")
{indent}        continue'''

if 'await self.client.search_tweet' in code and 'KEY_BYTE error — refreshing' not in code:
    code = search_regex.sub(replace_search, code)

with open('app/services/twitter_service.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch applied!")
