from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from .models import Message, Channel


@login_required
def chat(request, room_name):

    # create channel if it doesn't exist
    channel, created = Channel.objects.get_or_create(name=room_name)

    messages = Message.objects.filter(channel=channel).order_by("timestamp")

    channels = Channel.objects.all()

    return render(request, "chat/index.html", {
        "room_name": room_name,
        "messages": messages,
        "channels": channels
    })


@csrf_exempt
@login_required
def upload_file(request):

    if request.method == "POST":

        user = request.POST.get("user") or request.user.username
        message = request.POST.get("message", "")
        room = request.POST.get("room")
        file = request.FILES.get("file")

        if not room:
            return JsonResponse({"error": "room is required"}, status=400)

        channel, _ = Channel.objects.get_or_create(name=room)

        if file:
            msg = Message.objects.create(
                user=user,
                content=message,
                channel=channel,
                file=file
            )
        else:
            msg = Message.objects.create(
                user=user,
                content=message,
                channel=channel
            )

        return JsonResponse({
            "status": "ok",
            "file_url": msg.file.url if msg.file else "",
            "user": user,
            "message": message
        })

    return JsonResponse({"error": "method not allowed"}, status=405)


def register(request):

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("/login/")

    else:
        form = UserCreationForm()

    return render(request, "chat/register.html", {"form": form})


@login_required
def create_channel(request):

    if request.method == "POST":

        channel_name = request.POST.get("channel_name")

        if channel_name:

            channel_name = channel_name.strip().replace(" ", "-").lower()

            Channel.objects.get_or_create(name=channel_name)

            return redirect("/chat/" + channel_name + "/")

    return redirect("/chat/general/")