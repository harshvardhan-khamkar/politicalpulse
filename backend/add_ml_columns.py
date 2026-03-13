from app.database import engine
from sqlalchemy import text

def add_columns():
    with engine.connect() as conn:
        try:
            conn.execute(text('ALTER TABLE twitter_posts ADD COLUMN IF NOT EXISTS predicted_alignment VARCHAR(50);'))
            conn.execute(text('ALTER TABLE twitter_posts ADD COLUMN IF NOT EXISTS alignment_confidence NUMERIC(5,4);'))
            conn.execute(text('ALTER TABLE reddit_posts ADD COLUMN IF NOT EXISTS predicted_alignment VARCHAR(50);'))
            conn.execute(text('ALTER TABLE reddit_posts ADD COLUMN IF NOT EXISTS alignment_confidence NUMERIC(5,4);'))
            conn.commit()
            print("Columns added successfully.")
        except Exception as e:
            print(f"Error adding columns: {e}")

if __name__ == "__main__":
    add_columns()
