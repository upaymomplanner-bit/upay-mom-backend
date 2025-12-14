# UPay MOM Backend

A FastAPI-based backend for the UPay MOM (Minutes of Meeting) application.

## Features

- **Transcript Processing**: Upload meeting transcripts (.txt or .pdf) and get structured analysis
- **AI-Powered Analysis**: Uses Google Gemini 2.0 Flash for intelligent transcript analysis
- **Native File Handling**: Gemini directly processes PDF and text files (no manual extraction needed)
- **Structured Output**: Extracts participants, action items, decisions, and key topics
- **Type-Safe**: Built with Pydantic models for data validation

## Setup

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Create a `.env` file based on `.env.example`:

   ```bash
   cp .env.example .env
   ```

3. Add your Google Gemini API key to the `.env` file:

   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

4. Run the application:

   ```bash
   uv run fastapi dev app/main.py --host 0.0.0.0 --port 8000
   ```

5. Open your browser to `http://localhost:8000/docs` to see the interactive API documentation

## API Endpoints

### Transcript Processing

**POST** `/transcripts/process`

Upload a meeting transcript file (.txt or .pdf) and receive structured analysis.

**Request:**

- `file`: Upload file (multipart/form-data)
  - Supported formats: `.txt`, `.pdf`
  - Max size: 10MB (configurable)

## Project Structure

- `app/`: Application package
  - `main.py`: FastAPI application entry point
  - `config.py`: Configuration and settings management
  - `routers/`: API route handlers
    - `items.py`: Example items router
    - `transcript.py`: Transcript processing endpoints
  - `schemas/`: Pydantic models for request/response validation
    - `transcript.py`: Transcript-related data models
  - `services/`: Business logic and external service integrations
    - `gemini_client.py`: Reusable Google Gemini API client
    - `file_processor.py`: File upload and text extraction service

## Configuration

Environment variables (set in `.env`):

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `GEMINI_MODEL`: Gemini model to use (default: `gemini-2.0-flash-exp`)
- `MAX_FILE_SIZE`: Maximum file upload size in bytes (default: 10485760 = 10MB)

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **Google Generative AI**: Gemini API client for AI-powered analysis with native file support
- **python-multipart**: File upload support

## Testing

### Prerequisites

Before running live tests, ensure you have the following environment variables configured in your `.env.development` file:

```bash
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

### Running all tests

```bash
uv run pytest tests/ -v
```

### Running Live Tests - Integration Tests

#### Run all live tests

```bash
uv run pytest tests/test_integration.py::TestLiveIntegration -m live -v
```

#### Run specific live test

```bash
# Test Gemini API only
uv run pytest tests/test_integration.py::TestLiveIntegration::test_live_gemini_analysis -v

# Test Supabase operations only
uv pytest tests/test_integration.py::TestLiveIntegration::test_live_supabase_save_and_delete -v

# Test complete end-to-end flow
uv run pytest tests/test_integration.py::TestLiveIntegration::test_live_complete_gemini_to_supabase_flow -v
```

#### Skip live tests (run only mocked tests)

```bash
uv run pytest tests/test_integration.py -m "not live" -v
```
