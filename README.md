# PoliPulse - Political Intelligence Tool  🗳️

A comprehensive Political Intelligence tool for analyzing Indian elections, social media sentiment, and political trends.

## Features

- **Election Results Analysis**: Query past Lok Sabha election results by state, constituency, and year
- **Polls & Surveys**: Create and participate in opinion polls, pre-election surveys, and policy polls
- **Social Media Analysis**: Analyze Twitter and Reddit posts from political leaders and parties
- **Sentiment Tracking**: Multilingual sentiment analysis supporting Hindi, Tamil, Telugu, Bengali, and more
- **Prediction Engine**: Data-driven predictions for election outcomes
- **News Aggregation**: Curated Indian political news and global geopolitical updates
- **Party Information**: Detailed profiles of political parties, leaders, ideology, and electoral statistics

## Tech Stack

**Backend:**
- FastAPI
- PostgreSQL (Docker)
- SQLAlchemy + Alembic
- Transformers (multilingual ML)
- Twikit (Twitter scraping)
- PRAW (Reddit API)

**Frontend:**
- React + Vite
- Chart.js / Recharts
- React Router

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

### Backend Setup

1. **Start PostgreSQL Database**
```bash
docker-compose up -d
```

2. **Create Virtual Environment**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Run Development Server**
```bash
uvicorn app.main:app --reload
```

API will be available at: http://localhost:8000
Swagger docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:5173

## Database

The PostgreSQL database is configured via Docker Compose:
- **Database**: polipulse
- **User**: polipulse_admin
- **Port**: 5432
- **Adminer**: http://localhost:8080

Election results data (100,570+ rows) is pre-loaded.

## API Documentation

Visit `/docs` for interactive Swagger API documentation.

### Main Endpoints

- `GET /elections/results?state=X&constituency=Y&year=Z` - Get election results
- `GET /elections/states` - List all states
- `GET /elections/years` - List election years
- `GET /polls` - Get active polls
- `POST /polls/{id}/vote` - Vote on a poll
- `GET /social/trending` - Get trending topics
- `GET /parties` - List political parties

## Project Structure

```
polipulse/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── config.py     # Settings
│   │   ├── database.py   # DB connection
│   │   └── main.py       # FastAPI app
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
└── docker-compose.yml
```

## Development

- Backend runs on port **8000**
- Frontend runs on port **5173**
- PostgreSQL on port **5432**
- Adminer (DB admin) on port **8080**

## License

MIT
