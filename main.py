from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import os
from supabase import create_client
from upstash_redis import Redis

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
redis = Redis(url=UPSTASH_REDIS_URL, token=UPSTASH_REDIS_TOKEN)

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

combined_app = socketio.ASGIApp(sio, app)

connected_users = {}

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    connected_users[sid] = sid

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    connected_users.pop(sid, None)

@sio.event
async def send_notification(sid, data):
    print(f"Notification received: {data}")

    supabase.table("notifications").insert({
        "message": data["message"],
        "type": data.get("type", "info"),
        "is_read": False
    }).execute()

    await sio.emit('receive_notification', {
        'message': data['message'],
        'type': data.get('type', 'info'),
    })

@app.get("/")
async def home():
    return {"status": "Notification server is running!"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "connected_users": len(connected_users)
    }

@app.get("/notifications")
async def get_notifications():
    result = supabase.table("notifications").select("*").order("created_at", desc=True).execute()
    return {"notifications": result.data}