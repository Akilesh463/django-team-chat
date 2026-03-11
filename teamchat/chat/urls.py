from django.urls import path
from .views import chat

urlpatterns = [
    path("<str:room_name>/", chat, name="chat"),
]

from .views import upload_file

urlpatterns = [
    path("upload/", upload_file, name="upload"),
]