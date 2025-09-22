# PearlCard Fare Calculation System

A flexible NFC-enabled prepaid card fare calculation system for Pearly City's metro network.

## Project Structure

```
pearlcard-system/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── fare_calculator.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── endpoints.py
│   │   └── config.py
│   ├── tests/
│   │   └── test_fare_calculator.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── JourneyForm.jsx
│   │   │   ├── FareTable.jsx
│   │   │   └── FilterControls.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── index.js
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── .env
└── docker-compose.yml
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
API documentation will be available at `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

### Running Tests

#### Backend Tests
```bash
cd backend
pytest tests/ -v
```

#### Frontend Tests
```bash
cd frontend
npm test
```

## API Endpoints

### Calculate Fares
- **Endpoint:** `POST /api/calculate-fares`
- **Input:** List of journeys with from_zone and to_zone
- **Output:** Fare for each journey and total daily fare

Example Request:
```json
{
  "journeys": [
    {"from_zone": 1, "to_zone": 2},
    {"from_zone": 2, "to_zone": 3}
  ]
}
```

## Features

- ✅ Modular architecture following SOLID principles
- ✅ Python FastAPI backend
- ✅ React frontend with hooks
- ✅ Up to 20 journeys per day
- ✅ Sortable fare table
- ✅ Price filtering (>, <, =)
- ✅ Comprehensive unit tests
- ✅ Configurable fare rules
- ✅ CORS support for development
- ✅ **Local SQLite datastore for fare rules** (Nice to have - IMPLEMENTED)
- ✅ Persistent fare configuration
- ✅ Admin API for updating fare rules
