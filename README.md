# Buffer

Buffer is a powerful message buffer platform that allows you to receive, store, and forward messages based on configurable rules. It provides a user-friendly interface for managing message buffers and forwarding configurations.

## Features

- Webhook endpoint for receiving messages
- Configurable message buffering based on message characteristics
- Multiple forwarding destinations with custom headers and methods
- Message history tracking
- Real-time status monitoring
- Modern and responsive web interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/buffer.git
cd buffer
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

1. Start the backend server:
```bash
buffer run
```

2. Start the frontend development server:
```bash
cd buffer/frontend
npm install
npm start
```

3. Access the web interface at `http://localhost:3000`

## Webhook Usage

Send messages to the webhook endpoint:

```bash
curl -X POST http://localhost:5000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, World!", "phone_number": "+5511999999999"}'
```

## Configuration

### Buffer Configuration

Configure message buffering based on message characteristics:

- Filter Field: The field in the message to match (e.g., "phone_number")
- Filter Value: The value to match against
- Max Size: Maximum number of messages to buffer

### Forwarding Configuration

Configure message forwarding:

- URL: Destination endpoint
- Method: HTTP method (POST, PUT, PATCH)
- Headers: Custom headers for the request

## Development

### Backend

The backend is built with:
- Flask
- SQLite
- APScheduler

### Frontend

The frontend is built with:
- React
- React Router
- Modern CSS

## License

This project is licensed under the MIT License - see the LICENSE file for details.
