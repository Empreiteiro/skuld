# Skuld

Skuld is a powerful cron-based task scheduling platform that allows you to create, manage, and monitor scheduled HTTP requests through a modern web interface. It provides a user-friendly interface for managing cron jobs and execution history.

## Features

- Modern web interface for managing cron schedules
- Support for all HTTP methods (GET, POST, PUT, PATCH)
- Custom headers and request body configuration
- Real-time execution history and monitoring
- Enable/disable schedules dynamically
- Cron expression validation
- Execution logs with detailed responses
- Timezone configuration support

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/skuld.git
cd skuld
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

## Usage

1. Start the Skuld server:

**Option 1 - Using the CLI:**
```bash
python -m skuld.cli run
```

**Option 2 - Direct execution:**
```bash
python run_skuld.py
```

2. Access the web interface at `http://localhost:8000`

## API Endpoints

### Schedules
- `GET /api/schedules` - List all schedules
- `POST /api/schedules` - Create a new schedule

### Executions
- `GET /api/executions` - List execution history

### Health
- `GET /api/health` - Check server status

## Schedule Configuration

### Required Fields
- **Name**: Unique identifier for the schedule
- **URL**: Target endpoint to call
- **Cron Expression**: Cron pattern for scheduling
- **Method**: HTTP method (GET, POST, PUT, PATCH)

### Optional Fields
- **Description**: Human-readable description
- **Headers**: Custom headers (JSON format)
- **Body**: Request body content

### Cron Expression Examples

- `*/5 * * * *` - Every 5 minutes
- `0 */2 * * *` - Every 2 hours
- `0 9 * * 1-5` - Every weekday at 9 AM
- `0 0 1 * *` - First day of each month at midnight
- `0 12 * * 0` - Every Sunday at noon

## Web Interface

The web interface provides:

- **Schedules Tab**: View all configured schedules with their status
- **Executions Tab**: Monitor execution history and responses
- **Create Schedule Tab**: Add new cron schedules through a form

## Development

### Backend

The backend is built with:
- Flask
- SQLite
- APScheduler
- Flask-CORS

### Frontend

The frontend is built with:
- React
- Modern CSS
- Responsive design

## Project Structure

```
skuld/
├── skuld/
│   ├── cli.py         # Command line interface
│   ├── server.py      # Flask server and API
│   └── frontend/      # React web interface
├── setup.py           # Package configuration
└── README.md         # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
