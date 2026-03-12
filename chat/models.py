from django.db import models


class Channel(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"#{self.name}"


class Message(models.Model):

    user = models.CharField(max_length=100)
    content = models.TextField(blank=True)
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE)

    file = models.FileField(upload_to="chat_files/", null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        preview = self.content[:40] if self.content else "[file]"
        return f"{self.user}: {preview}"

    class Meta:
        ordering = ["timestamp"]