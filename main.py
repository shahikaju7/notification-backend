from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import os
from supabase import create_client
from upstash_redis import Redis
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
UPSTASH_REDIS_URL = os.environ.get("UPSTASH_REDIS_URL", "")
UPSTASH_REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_TOKEN", "")

print("DEBUG SUPABASE_URL:", SUPABASE_URL)

from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
redis = Redis(url=UPSTASH_REDIS_URL, token=UPSTASH_REDIS_TOKEN)

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    ping_timeout=60,
    ping_interval=25,
    logger=True,
    engineio_logger=True,
    allow_upgrades=True
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

combined_app = socketio.ASGIApp(sio, app)
connected_users = {}

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    connected_users.pop(sid, None)

@sio.event
async def register_user(sid, data):
    username = data.get('username')
    connected_users[username] = sid
    print(f"User registered: {username} -> {sid}")

@sio.event
async def send_order_update(sid, data):
    order_id = data.get('order_id')
    customer = data.get('customer')
    status = data.get('status')
    message = data.get('message')

    notification = {
        "order_id": order_id,
        "customer": customer,
        "status": status,
        "message": message,
        "is_read": False,
        "created_at": datetime.utcnow().isoformat()
    }

    supabase.table("notifications").insert(notification).execute()

    if customer in connected_users:
        await sio.emit('order_update', notification, to=connected_users[customer])

    await sio.emit('admin_update', notification)

@app.get("/")
async def home():
    return {"status": "Order Notification server is running!"}

@app.get("/notifications/{customer}")
async def get_notifications(customer: str):
    result = supabase.table("notifications")\
        .select("*")\
        .eq("customer", customer)\
        .order("created_at", desc=True)\
        .execute()
    return {"notifications": result.data}

@app.get("/all-notifications")
async def get_all_notifications():
    result = supabase.table("notifications")\
        .select("*")\
        .order("created_at", desc=True)\
        .execute()
    return {"notifications": result.data}