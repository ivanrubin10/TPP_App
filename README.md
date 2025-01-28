# Car Inspection Application

A modern web application for managing car inspections, with support for GALC and ICS integration.

## Features

- Real-time car inspection processing
- Queue management for incoming cars
- Integration with GALC (Generic Automotive Line Controller)
- Integration with ICS (Inspection Control System)
- Image processing and object detection using TensorFlow Lite
- RESTful API endpoints
- Modern Vue.js frontend
- Real-time updates using WebSocket

## Project Structure

```
.
├── application/              # Backend application
│   ├── api/                 # API routes and endpoints
│   ├── config/              # Configuration settings
│   ├── core/               # Core application logic
│   ├── models/             # Database models
│   ├── services/           # Business logic services
│   ├── tests/              # Unit and integration tests
│   └── utils/              # Utility functions
├── application-ui/          # Frontend application
├── logs/                    # Application logs
├── uploads/                # Uploaded images
└── instance/               # Instance-specific files
```

## Dependencies

### Backend Dependencies
- Flask and extensions (Flask-SQLAlchemy, Flask-Marshmallow, Flask-CORS, Flask-SocketIO)
- TensorFlow (>=2.15.0) for object detection
- OpenCV (opencv-python) for image processing
- SQLAlchemy for database management
- WebSocket support for real-time communication

### Frontend Dependencies
- Vue.js 3 with TypeScript
- Socket.IO client for real-time updates
- Axios for HTTP requests
- Modern UI components

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- SQLite (default) or PostgreSQL
- Virtual environment tool (recommended)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd car-inspection-app
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install frontend dependencies:
   ```bash
   cd application-ui
   npm install
   ```

## Configuration

1. Create a `.env` file in the root directory:
   ```
   FLASK_APP=application.app
   FLASK_ENV=development
   FLASK_DEBUG=1
   
   # Database
   DATABASE_URL=sqlite:///instance/app.db
   
   # GALC Settings
   GALC_HOST=127.0.0.1
   GALC_PORT=5002
   
   # ICS Settings
   ICS_API_URL=http://localhost:8000
   ICS_API_KEY=your-api-key
   ```

2. Adjust settings in `application/config/config.py` as needed.

## Running the Application

1. Start the backend server:
   ```bash
   python -m application.app
   ```

2. Start the frontend development server:
   ```bash
   cd application-ui
   npm run serve
   ```

3. Access the application at `http://localhost:8080`

## Development

### Code Style

The project follows PEP 8 style guide for Python code. Use the following tools:

```bash
# Format code
black application

# Check style
flake8 application

# Type checking
mypy application
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=application
```

## API Documentation

### Car Endpoints

- `GET /api/cars` - Get all car logs
- `GET /api/cars/<car_id>` - Get specific car log
- `POST /api/cars` - Create new car log

### Queue Endpoints

- `GET /api/queued-cars` - Get all queued cars
- `POST /api/queued-cars` - Add car to queue
- `GET /api/queued-cars/<car_id>` - Get specific queued car
- `POST /api/queued-cars/<car_id>/process` - Mark car as processed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 