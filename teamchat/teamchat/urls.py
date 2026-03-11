from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

from chat.views import chat, upload_file, register, create_channel

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('', lambda request: redirect('/chat/general/')),

    path('admin/', admin.site.urls),

    path('register/', register),

    path('login/', auth_views.LoginView.as_view(template_name='chat/login.html'), name="login"),
    path('logout/', auth_views.LogoutView.as_view(), name="logout"),

    path('upload/', upload_file),

    path('create-channel/', create_channel),

    path('chat/<str:room_name>/', chat),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)