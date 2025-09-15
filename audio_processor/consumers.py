"""
WebSocket consumers for real-time updates
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class ProcessingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if user is authenticated
        if self.scope["user"] == AnonymousUser():
            await self.close()
            return
        
        # Join processing room
        self.room_name = f"processing_{self.scope['user'].id}"
        self.room_group_name = f"processing_{self.scope['user'].id}"
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave processing room
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        # Handle incoming WebSocket messages (if needed)
        pass
    
    async def processing_update(self, event):
        """Send processing update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'processing_update',
            'payload': event['payload']
        }))
    
    async def processing_complete(self, event):
        """Send processing completion to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'processing_complete',
            'payload': event['payload']
        }))
    
    async def processing_error(self, event):
        """Send processing error to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'processing_error',
            'payload': event['payload']
        }))
