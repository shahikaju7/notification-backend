from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import os

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
    await sio.emit('receive_notification', {
        'message': data['message'],
        'type': data.get('type', 'info'),
        'timestamp': data.get('timestamp', '')
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