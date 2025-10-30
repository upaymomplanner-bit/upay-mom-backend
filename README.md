# UPay MOM Backend

A FastAPI-based backend for the UPay MOM application.

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Run the application:
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload
   ```

3. Open your browser to `http://localhost:8000` to see the API documentation at `http://localhost:8000/docs`

## Project Structure

- `app/`: Application package
  - `main.py`: FastAPI application entry point
  - `routers/`: API route handlers
    - `items.py`: Example items router