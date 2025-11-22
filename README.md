# AI Rooms Backend

AI-powered multi-room chat and task management system built with FastAPI, MongoDB, and LangChain.

## 🚀 Quick Start

**Want to test immediately?** See [QUICKSTART.md](QUICKSTART.md) for Docker setup and Postman testing.

```bash
# Start everything with Docker
docker-compose up -d

# Import Postman collection
# AI-Rooms-API.postman_collection.json

# Access API docs
open http://localhost:8000/docs
```

## ⚠️ Current Status: POC/SKELETON

This is a **proof-of-concept skeleton** with:

- ✅ Complete project structure
- ✅ All endpoints defined
- ✅ Docker setup ready
- ✅ Postman collection for testing
- ✅ Simplified authentication (no JWT)
- ⚠️ **Business logic is NOT implemented** (stubs/TODOs only)

Perfect for testing deployment and architecture before implementing features!

## 🏗️ Project Structure

```
Backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application settings
│   ├── db.py                # MongoDB connection utilities
│   │
│   ├── models/              # MongoDB document models
│   │   ├── user.py
│   │   ├── room.py
│   │   ├── message.py
│   │   ├── task.py
│   │   ├── profile.py
│   │   ├── goal.py
│   │   └── kb.py
│   │
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── auth.py
│   │   ├── room.py
│   │   ├── message.py
│   │   ├── task.py
│   │   ├── profile.py
│   │   ├── goal.py
│   │   └── kb.py
│   │
│   ├── routers/             # API route handlers
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── rooms.py         # Room management
│   │   ├── messages.py      # Message operations
│   │   ├── tasks.py         # Task management
│   │   ├── ai.py            # AI operations (rewrite, translate, etc.)
│   │   └── ws.py            # WebSocket for real-time chat
│   │
│   ├── services/            # Business logic layer
│   │   ├── auth_service.py
│   │   ├── room_service.py
│   │   ├── message_service.py
│   │   ├── task_service.py
│   │   ├── profile_service.py
│   │   ├── goal_service.py
│   │   └── kb_service.py
│   │
│   ├── ai/                  # AI agent logic (STUBS ONLY)
│   │   ├── orchestrator.py  # Main AI orchestration
│   │   ├── classifier.py    # Should-respond classifier
│   │   ├── utility_evaluator.py  # Action selection
│   │   └── tools.py         # AI tools (tasks, translate, search, etc.)
│   │
│   └── utils/               # Utility functions
│       ├── security.py      # JWT and password utilities
│       └── pagination.py    # Cursor-based pagination
│
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## 🐳 Docker Deployment (Recommended)

### Quick Start with Docker

```bash
# Start all services (API + MongoDB + Mongo Express)
docker-compose up -d

# Check services
docker-compose ps

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

**Services:**

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MongoDB Admin: http://localhost:8081 (admin/admin123)

### Docker Commands

```bash
# Rebuild after code changes
docker-compose up -d --build

# Clean slate (remove volumes)
docker-compose down -v

# Access MongoDB shell
docker exec -it ai-rooms-mongodb mongosh

# View all logs
docker-compose logs -f
```

## 🧪 Testing with Postman

1. **Import Collection**: `AI-Rooms-API.postman_collection.json`
2. **Start Services**: `docker-compose up -d`
3. **Run Requests**: Collection has all endpoints with examples
4. **See Details**: Check [QUICKSTART.md](QUICKSTART.md) for full workflow

## 💻 Local Development (Alternative)

### Prerequisites

- Python 3.11+
- MongoDB (local or cloud)
- Google AI API key (optional, for future AI features)

### Installation

1. **Clone the repository**

   ```bash
   cd Backend
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start MongoDB**

   ```bash
   # If using local MongoDB
   mongod

   # Or use MongoDB Atlas connection string in .env
   ```

6. **Run the application**

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## 📋 MongoDB Collections

The application uses the following MongoDB collections:

1. **users** - User accounts
2. **rooms** - Chat rooms
3. **room_members** - Room membership
4. **messages** - Chat messages
5. **tasks** - Room tasks
6. **user_profiles** - User style preferences
7. **room_goals** - Room goals
8. **room_kb** - Room knowledge base

## 🔌 API Endpoints

### Authentication (POC Mode - No JWT)

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get user info
- `GET /auth/me?user_id=...` - Get current user info

**⚠️ POC Mode**: Pass `user_id` as query parameter (no JWT tokens)

### Rooms

- `GET /rooms` - List user's rooms
- `POST /rooms` - Create new room
- `POST /rooms/join` - Join room with code
- `GET /rooms/{room_id}/members` - List room members

### Messages

- `GET /rooms/{room_id}/messages` - Get messages (with pagination)
- `POST /rooms/{room_id}/messages` - Send message

### Tasks

- `GET /rooms/{room_id}/tasks` - List room tasks
- `POST /rooms/{room_id}/tasks` - Create task
- `PATCH /tasks/{task_id}` - Update task

### AI Operations

- `POST /ai/rewrite` - Rewrite text in user's style
- `POST /ai/translate` - Translate text
- `POST /ai/summarize-room` - Summarize room messages

### WebSocket

- `GET /ws` - WebSocket connection for real-time chat

## ⚠️ Current Status: SKELETON

**This is a skeleton implementation with NO business logic.**

All endpoints, services, and AI modules contain:

- ✅ Proper structure and organization
- ✅ Type annotations
- ✅ Docstrings
- ✅ Function signatures
- ⚠️ **TODO comments and `pass` statements instead of actual implementation**

### What's NOT Implemented

- ❌ Database queries (all service methods are stubs)
- ❌ Password hashing (plain text in POC)
- ❌ AI agent logic (no LangChain calls)
- ❌ WebSocket connection management
- ❌ All API endpoint business logic

### What IS Implemented (POC)

- ✅ Complete project structure
- ✅ All endpoint definitions with proper signatures
- ✅ Docker setup (backend + MongoDB + admin UI)
- ✅ Simplified authentication (no JWT for testing)
- ✅ Postman collection with all API calls
- ✅ Health checks and monitoring
- ✅ CORS configured for frontend

### Next Steps to Production

1. **Implement Database Operations**

   - Complete all service methods in `app/services/`
   - Add MongoDB queries and error handling
   - Implement pagination logic

2. **Add Proper Authentication**

   - Add JWT token support
   - Implement password hashing with bcrypt
   - Add authorization middleware

3. **Implement AI Features**

   - Set up LangChain with Google AI
   - Implement classifier logic
   - Implement utility evaluator
   - Complete AI tools with actual LangChain calls
   - Implement orchestrator workflow

4. **Implement WebSocket**

   - Complete `ConnectionManager` class
   - Add message broadcasting
   - Integrate with AI orchestrator

5. **Add Error Handling & Validation**

   - Add proper exception handling throughout
   - Add validation and business rule checks
   - Add rate limiting

6. **Testing & Deployment**
   - Add unit tests
   - Add integration tests
   - Set up CI/CD pipeline
   - Deploy to cloud provider

## 🛠️ Tech Stack

- **Framework**: FastAPI (async)
- **Database**: MongoDB with Motor (async driver)
- **Validation**: Pydantic v2
- **Authentication**: Simplified for POC (no JWT in current version)
- **AI**: LangChain + Google AI Gemini (planned, stubs only)
- **WebSockets**: FastAPI WebSocket support (planned)
- **Containerization**: Docker + Docker Compose
- **DB Admin**: Mongo Express

## 📝 Development Notes

- All functions are async-ready
- Type hints throughout for better IDE support
- Pydantic models for request/response validation
- Separation of concerns (models, schemas, services, routes)
- Ready for AI integration with LangChain

## 🤝 Contributing

This is a skeleton project. To contribute:

1. Pick a service or feature to implement
2. Replace `pass` with actual implementation
3. Test your implementation
4. Update this README with completed features

## 📄 License

[Your License Here]
