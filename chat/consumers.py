import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message, Channel
from datetime import datetime

# Per-room online user tracking: { room_group_name: set(usernames) }
online_users = {}


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_" + self.room_name

        user = self.scope.get("user")

        if user and user.is_authenticated:
            self.username = user.username
        else:
            self.username = "Guest"

        # Add user to this room's online set
        if self.room_group_name not in online_users:
            online_users[self.room_group_name] = set()
        online_users[self.room_group_name].add(self.username)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "presence_update",
                "users": list(online_users[self.room_group_name])
            }
        )


    async def disconnect(self, close_code):

        # Guard: attributes may not be set if connect() raised before setting them
        username = getattr(self, "username", None)
        room_group_name = getattr(self, "room_group_name", None)

        if username and room_group_name:
            room_set = online_users.get(room_group_name, set())
            room_set.discard(username)

            await self.channel_layer.group_discard(
                room_group_name,
                self.channel_name
            )

            await self.channel_layer.group_send(
                room_group_name,
                {
                    "type": "presence_update",
                    "users": list(room_set)
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

            message = data.get("message", "")
            user = data.get("user", self.username)

            # SAVE MESSAGE TO DATABASE
            await self.save_message(user, message)

            timestamp = datetime.now().strftime("%H:%M")

            # SEND TO USERS IN CHANNEL
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "user": user,
                    "message": message,
                    "timestamp": timestamp
                }
            )

            # GLOBAL NOTIFICATION
            await self.channel_layer.group_send(
                "global_notifications",
                {
                    "type": "notify",
                    "room": self.room_name,
                    "user": user,
                    "message": message
                }
            )


        elif msg_type == "typing":

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_event",
                    "user": data.get("user", self.username),
                    "sender_channel": self.channel_name
                }
            )


        elif msg_type == "stop_typing":

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "stop_typing_event",
                    "sender_channel": self.channel_name
                }
            )


    async def chat_message(self, event):

        await self.send(text_data=json.dumps({
            "type": "chat",
            "user": event["user"],
            "message": event["message"],
            "timestamp": event.get("timestamp", "")
        }))


    async def typing_event(self, event):

        # Don't echo typing indicator back to the sender
        if event.get("sender_channel") == self.channel_name:
            return

        await self.send(text_data=json.dumps({
            "type": "typing",
            "user": event["user"]
        }))


    async def stop_typing_event(self, event):

        if event.get("sender_channel") == self.channel_name:
            return

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