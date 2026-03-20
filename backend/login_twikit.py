import asyncio
from twikit import Client

async def main():
    try:
        client = Client('en-US')
        print("Logging in to Twikit...")
        await client.login(
            auth_info_1='syman763255',
            auth_info_2='spymanxavier@gmail.com',
            password='9421150039'
        )
        client.save_cookies('cookies.json')
        print("Cookies saved successfully!")
    except Exception as e:
        print(f"Error logging in: {e}")

asyncio.run(main())
