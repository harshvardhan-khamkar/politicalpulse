
import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

USER = "polipulse_admin"
DB_NAME = "polipulse"
HOST = "localhost"
PORT = "5432"

PASSWORDS_TO_TRY = [
    "polipulse_password",
    "polipulse_admin",
    "admin",
    "password",
    "postgres",
    "123456",
    "1234",
    ""
]

def test_connection():
    print(f"Testing connection for user: {USER}")
    
    for password in PASSWORDS_TO_TRY:
        url = f"postgresql+psycopg://{USER}:{password}@{HOST}:{PORT}/{DB_NAME}"
        displayed_url = f"postgresql+psycopg://{USER}:****@{HOST}:{PORT}/{DB_NAME}"
        
        print(f"Trying password: '{password}'...")
        
        try:
            engine = create_engine(url)
            connection = engine.connect()
            connection.close()
            print(f"✅ SUCCESS! Correct password is: '{password}'")
            return
        except OperationalError:
            print(f"❌ Failed")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n❌ Could not find correct password.")

if __name__ == "__main__":
    test_connection()
