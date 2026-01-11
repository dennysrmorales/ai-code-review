# AI-Powered Code Review Assistant

A full-stack application that uses AI to analyze code snippets for common issues, inefficiencies, and bugs. Built with React frontend and Django backend, integrated with OpenAI for code analysis and Sentry for error tracking.

> Note: Cursor.ai was used to accelerate boilerplate setup and component scaffolding, while all core logic, AI integration, and architecture were designed and implemented independently.

## Features

- **Code Editor**: Monaco editor with syntax highlighting for multiple languages
- **AI-Powered Analysis**: Uses OpenAI GPT-4o-mini to review code and provide suggestions
- **Issue Highlighting**: Visual markers on code lines with issues
- **Detailed Reports**: Shows issues with severity levels (error, warning, info), suggestions, and overall score
- **Error Tracking**: Sentry integration for monitoring errors and performance
- **Multi-language Support**: Python, JavaScript, TypeScript, Java, C++, C, Go, Rust

## Tech Stack

- **Frontend**: React, Monaco Editor, Axios
- **Backend**: Django, Django REST Framework
- **AI**: OpenAI API (GPT-4o-mini)
- **Error Tracking**: Sentry

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- OpenAI API key
- (Optional) Sentry account for error tracking

## Setup Instructions

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

4. Create a `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` and add your configuration:
   ```
   SECRET_KEY=your-django-secret-key-here
   DEBUG=True
   OPENAI_API_KEY=your-openai-api-key-here
   SENTRY_DSN=your-backend-sentry-dsn-here  # Optional - requires separate Sentry project
   ENVIRONMENT=development
   ```

6. Run migrations:
   ```bash
   python manage.py migrate
   ```

7. Start the Django server:
   ```bash
   python manage.py runserver
   ```

   The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your Sentry DSN (optional):
   ```
   REACT_APP_SENTRY_DSN=your-frontend-sentry-dsn-here  # Optional - requires separate Sentry project
   REACT_APP_ENVIRONMENT=development
   ```

5. Start the React development server:
   ```bash
   npm start
   ```

   The frontend will run on `http://localhost:3000`

## Usage

1. Open your browser and navigate to `http://localhost:3000`
2. Select the programming language from the dropdown
3. Enter or paste your code in the editor
4. Click "Review Code" to analyze your code
5. View the results in the right panel:
   - Summary of the review
   - List of issues found with severity levels
   - Code preview with highlighted issue lines
   - Overall code quality score

## API Endpoint

### POST `/api/review/`

Analyze code using AI.

**Request Body:**
```json
{
  "code": "def hello():\n    print('Hello, World!')",
  "language": "python"
}
```

**Response:**
```json
{
  "review": {
    "issues": [
      {
        "line": 1,
        "severity": "info",
        "message": "Function could have a docstring",
        "suggestion": "Add a docstring to document the function's purpose"
      }
    ],
    "summary": "Overall good code structure...",
    "score": 85
  },
  "response_time": 2.34
}
```

## Error Tracking

The application is integrated with Sentry for error tracking:

- **Backend**: Tracks errors in AI analysis, failed requests, slow responses, and invalid input
- **Frontend**: Tracks JavaScript errors and React component errors

**Important**: The backend and frontend require **separate Sentry DSNs**. You need to create two separate projects in Sentry - one for Django (backend) and one for React (frontend).

To enable Sentry:
1. Create a Sentry account at https://sentry.io
2. Create **two separate projects**:
   - One for Django (backend) - select "Django" as the platform
   - One for React (frontend) - select "React" as the platform
3. Copy the DSNs from each project
4. Add the backend DSN to `backend/.env` as `SENTRY_DSN`
5. Add the frontend DSN to `frontend/.env` as `REACT_APP_SENTRY_DSN`

## Project Structure

```
.
├── backend/
│   ├── api/              # Django API app
│   │   ├── views.py      # Code review API endpoint
│   │   └── urls.py       # URL routing
│   ├── code_review/      # Django project settings
│   │   ├── settings.py   # Django configuration
│   │   └── urls.py       # Main URL configuration
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CodeEditor.js      # Monaco editor component
│   │   │   └── ReviewResults.js   # Results display component
│   │   ├── App.js        # Main app component
│   │   └── index.js      # Entry point with Sentry init
│   └── package.json
└── README.md
```

## Development

### Backend Development

- API endpoint: `http://localhost:8000/api/review/`
- Admin panel: `http://localhost:8000/admin/`
- Django REST Framework browsable API available

### Frontend Development

- Development server: `http://localhost:3000`
- Hot reload enabled
- API proxy configured to backend (port 8000)

## License

MIT
