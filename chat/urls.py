from django.urls import path
from .views import chat, upload_file

urlpatterns = [
    path("<str:room_name>/", chat, name="chat"),
    path("upload/", upload_file, name="upload"),
]