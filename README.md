# BrandRadar

BrandRadar is a full-stack application for analyzing brands, products, and reviews. It features a FastAPI backend, a React frontend, and a Python-based web scraper.

## Features
- FastAPI backend with endpoints for brands, products, insights, and reviews
- React frontend with data visualization
- Dockerized development and deployment
- Web scraping for data collection

## Project Structure
```
BrandRadar/
├── backend/        # FastAPI backend
├── frontend/       # React frontend
├── scraper/        # Python web scraper
├── docker-compose.yml
├── requirement.txt
└── readme.md
```

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js and npm (for local frontend development)
- Python 3.11+ (for local backend/scraper development)

### Running with Docker Compose
1. Clone the repository:
   ```sh
   git clone <repo-url>
   cd BrandRadar
   ```
2. Build and start the containers:
   ```sh
   docker-compose up --build
   ```
3. Access the frontend at [http://localhost](http://localhost)
4. The backend API will be available at [http://localhost:5000](http://localhost:5000)

### Running Locally (Without Docker)
#### Backend
1. Navigate to the backend folder:
   ```sh
   cd backend
   pip install -r ../requirement.txt
   uvicorn main:app --reload --port 5000
   ```

#### Frontend
1. Navigate to the frontend folder:
   ```sh
   cd frontend
   npm install
   npm run dev
   ```
2. Open [http://localhost:5173](http://localhost:5173) in your browser.

#### Scraper
1. Navigate to the scraper folder:
   ```sh
   cd scraper
   python scraper.py
   ```

## Environment Variables
- Place your environment variables in a `.env` file in the appropriate folder (e.g., `backend/.env`, `scraper/.env`).
- Do not commit `.env` files to version control.

## License
This project is for educational and demonstration purposes.
