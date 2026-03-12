from django.contrib import admin
from .models import Channel, Message


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["user", "channel", "timestamp", "has_file"]
    list_filter = ["channel"]
    search_fields = ["user", "content"]
    readonly_fields = ["timestamp"]

    def has_file(self, obj):
        return bool(obj.file)
    has_file.boolean = True
    has_file.short_description = "File?"