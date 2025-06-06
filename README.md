# Skuld

Skuld is a powerful web-based cron job scheduler with a user-friendly interface that allows you to schedule and monitor HTTP calls using cron expressions.

## Features

- Schedule HTTP requests using cron expressions
- Monitor executions through detailed logs
- Support for multiple HTTP methods (GET, POST, PUT, DELETE)
- User-friendly interface for schedule management
- Real-time execution log updates
- Easy to install and configure

## Requirements

- Python 3.8 or higher
- Node.js 14 or higher
- npm (usually comes with Node.js)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Empreiteiro/skuld.git
cd skuld
```

2. Install the Python package:
```bash
pip install -e .
```

## Usage

### Quick Start (Recommended)

Run the startup script that will start both backend and frontend:

```bash
python start.py
```

### Manual Start (Alternative)

If you prefer to start services separately:

Terminal 1 (Backend):
```bash
skuld run
```

Terminal 2 (Frontend):
```bash
cd skuld/frontend
npm install
npm start
```

## Accessing the Application

After starting the services, you can access:

- Frontend Interface: [http://localhost:3000](http://localhost:3000)
- API Backend: [http://localhost:5000](http://localhost:5000)

## Cron Expression Guide

Skuld uses standard cron expressions. Here are some common patterns:

| Expression    | Description                                |
|---------------|--------------------------------------------|
| `* * * * *`   | Every minute                               |
| `*/5 * * * *` | Every 5 minutes                            |
| `0 * * * *`   | At the beginning of every hour            |
| `0 0 * * *`   | Every day at midnight                      |
| `0 0 * * 0`   | Every Sunday at midnight                   |
| `0 0 1 * *`   | First day of every month at midnight       |

## API Dependencies

- Flask >= 2.0.0
- Flask-CORS >= 3.0.0
- Requests >= 2.25.0
- Click >= 8.0.0
- APScheduler >= 3.9.0
- Python-dateutil >= 2.8.0
- Croniter

## Development

To contribute to the project:

1. Fork the repository
2. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```
3. Commit your changes:
```bash
git commit -am "Add new feature"
```
4. Push to the branch:
```bash
git push origin feature/your-feature-name
```
5. Create a Pull Request

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   - Change the port using the `--port` option:
   ```bash
   skuld run --port 5001
   ```

2. **Node Modules Not Found**
   - Run `npm install` in the frontend directory:
   ```bash
   cd skuld/frontend
   npm install
   ```

## License

This project is licensed under the MIT License.

## Author

Created and maintained by [Empreiteiro](https://github.com/Empreiteiro)
