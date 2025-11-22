# 🚀 Quick Start Guide - AI Rooms API

## Prerequisites

- Docker & Docker Compose installed
- Postman (for API testing)

## 🏃 Getting Started in 3 Steps

### 1. Start the Services

```bash
cd Backend
docker-compose up -d
```

This will start:

- **Backend API**: http://localhost:8000
- **MongoDB**: localhost:27017
- **Mongo Express** (DB Admin): http://localhost:8081 (admin/admin123)

### 2. Verify Services

```bash
# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f backend

# Test health endpoint
curl http://localhost:8000/health
```

### 3. Import Postman Collection

1. Open Postman
2. Click **Import**
3. Select `AI-Rooms-API.postman_collection.json`
4. The collection includes all API endpoints with examples

## 📖 API Documentation

Interactive API docs available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing Workflow

### Step 1: Register a User

```bash
POST http://localhost:8000/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "password": "test123",
  "preferred_language": "en"
}
```

**Response:**

```json
{
  "id": "674123abc...",
  "username": "testuser",
  "preferred_language": "en",
  "created_at": "2025-11-22T10:30:00"
}
```

Save the `id` - you'll need it for subsequent requests!

### Step 2: Create a Room

```bash
POST http://localhost:8000/rooms?user_id=YOUR_USER_ID
Content-Type: application/json

{
  "name": "My Project Room"
}
```

**Response:**

```json
{
  "id": "674124def...",
  "name": "My Project Room",
  "join_code": "ABC123",
  "created_at": "2025-11-22T10:31:00"
}
```

### Step 3: Send a Message

```bash
POST http://localhost:8000/rooms/YOUR_ROOM_ID/messages?user_id=YOUR_USER_ID
Content-Type: application/json

{
  "content": "Hello, team!",
  "type": "text"
}
```

### Step 4: Create a Task

```bash
POST http://localhost:8000/rooms/YOUR_ROOM_ID/tasks?user_id=YOUR_USER_ID
Content-Type: application/json

{
  "title": "Setup database",
  "assignee_id": "YOUR_USER_ID"
}
```

## 🔧 Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up -d --build

# Access MongoDB shell
docker exec -it ai-rooms-mongodb mongosh

# Access backend container
docker exec -it ai-rooms-backend bash
```

## 📊 MongoDB Access

### Via Mongo Express (Web UI)

- URL: http://localhost:8081
- Username: `admin`
- Password: `admin123`

### Via MongoDB Shell

```bash
docker exec -it ai-rooms-mongodb mongosh
use ai_rooms
db.users.find()
db.rooms.find()
db.messages.find()
```

## 🐛 Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Ensure ports are free
lsof -i :8000  # Backend
lsof -i :27017 # MongoDB
lsof -i :8081  # Mongo Express
```

### Backend can't connect to MongoDB

```bash
# Check if MongoDB is healthy
docker-compose ps

# Restart services
docker-compose restart
```

### Hot reload not working

The backend is mounted with a volume for development. Changes to `app/` folder will auto-reload.

## 🔐 Authentication (POC Mode)

**⚠️ This is a POC with simplified authentication:**

- No JWT tokens
- Pass `user_id` as query parameter
- Passwords stored in plain text
- **NOT for production use!**

Example:

```
GET /rooms?user_id=674123abc...
```

## 📁 Project Structure

```
Backend/
├── app/                          # Application code
│   ├── main.py                  # FastAPI app
│   ├── config.py                # Settings
│   ├── db.py                    # MongoDB connection
│   ├── models/                  # DB models
│   ├── schemas/                 # Request/response schemas
│   ├── routers/                 # API endpoints
│   ├── services/                # Business logic
│   ├── ai/                      # AI agent stubs
│   └── utils/                   # Utilities
├── Dockerfile                   # Backend container
├── docker-compose.yml           # All services
├── requirements.txt             # Python dependencies
└── AI-Rooms-API.postman_collection.json  # API tests
```

## 🌐 Environment Variables

Edit `.env` file:

```env
MONGO_URI=mongodb://mongodb:27017
MONGO_DB_NAME=ai_rooms
POC_MODE=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 📝 API Endpoints Summary

### Authentication

- `POST /auth/register` - Register user
- `POST /auth/login` - Login
- `GET /auth/me` - Get current user

### Rooms

- `GET /rooms` - List user's rooms
- `POST /rooms` - Create room
- `POST /rooms/join` - Join room with code
- `GET /rooms/{id}/members` - Get room members

### Messages

- `GET /rooms/{id}/messages` - Get messages (paginated)
- `POST /rooms/{id}/messages` - Send message

### Tasks

- `GET /rooms/{id}/tasks` - List room tasks
- `POST /rooms/{id}/tasks` - Create task
- `PATCH /tasks/{id}` - Update task

### AI (Stubs)

- `POST /ai/rewrite` - Rewrite text
- `POST /ai/translate` - Translate text
- `POST /ai/summarize-room` - Summarize room

### Health

- `GET /health` - Health check
- `GET /` - API info

## 🚢 Deployment Testing

To test deployment before full implementation:

1. Build the image:

```bash
docker build -t ai-rooms-backend .
```

2. Test the container:

```bash
docker run -p 8000:8000 \
  -e MONGO_URI=mongodb://host.docker.internal:27017 \
  ai-rooms-backend
```

3. Push to registry (example):

```bash
docker tag ai-rooms-backend your-registry/ai-rooms-backend:latest
docker push your-registry/ai-rooms-backend:latest
```

## 📞 Support

For issues or questions:

1. Check logs: `docker-compose logs -f backend`
2. Check MongoDB: http://localhost:8081
3. Check API docs: http://localhost:8000/docs
4. Verify services: `docker-compose ps`

## 🎯 Next Steps

1. ✅ Test all endpoints with Postman
2. ✅ Verify data in MongoDB
3. ✅ Test Docker deployment
4. ⏭️ Implement actual business logic (currently stubs)
5. ⏭️ Add proper authentication (JWT)
6. ⏭️ Implement AI features (LangChain)
7. ⏭️ Add WebSocket functionality

---

**Ready to test!** 🎉

Run `docker-compose up -d` and start testing with Postman!
