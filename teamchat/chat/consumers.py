import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message, Channel
from datetime import datetime

online_users = set()


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_" + self.room_name

        user = self.scope.get("user")

        if user and user.is_authenticated:
            self.username = user.username
        else:
            self.username = "Guest"

        online_users.add(self.username)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "presence_update",
                "users": list(online_users)
            }
        )


    async def disconnect(self, close_code):

        if self.username in online_users:
            online_users.remove(self.username)

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "presence_update",
                "users": list(online_users)
            }
        )


    @sync_to_async
    def save_message(self, user, message):

        channel, created = Channel.objects.get_or_create(name=self.room_name)

        Message.objects.create(
            user=user,
            content=message,
            channel=channel
        )


    async def receive(self, text_data):

        data = json.loads(text_data)
        msg_type = data.get("type")

        if msg_type == "chat":

            timestamp = datetime.now().strftime("%H:%M")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "user": data["user"],
                    "message": data["message"],
                    "timestamp": timestamp
                }
            )

            # GLOBAL NOTIFICATION
            await self.channel_layer.group_send(
                "global_notifications",
                {
                    "type": "notify",
                    "room": self.room_name,
                    "user": data["user"],
                    "message": data["message"]
                }
            )


        elif msg_type == "typing":

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_event",
                    "user": data["user"]
                }
            )


        elif msg_type == "stop_typing":

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "stop_typing_event"
                }
            )


    async def chat_message(self, event):

        await self.send(text_data=json.dumps({
            "type": "chat",
            "user": event["user"],
            "message": event["message"],
            "timestamp": event.get("timestamp")
        }))


    async def typing_event(self, event):

        await self.send(text_data=json.dumps({
            "type": "typing",
            "user": event["user"]
        }))


    async def stop_typing_event(self, event):

        await self.send(text_data=json.dumps({
            "type": "stop_typing"
        }))


    async def presence_update(self, event):

        await self.send(text_data=json.dumps({
            "type": "presence",
            "users": event["users"]
        }))



class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.group_name = "global_notifications"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()


    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )


    async def notify(self, event):

        await self.send(text_data=json.dumps({
            "type": "notification",
            "room": event["room"],
            "user": event["user"],
            "message": event["message"]
        }))