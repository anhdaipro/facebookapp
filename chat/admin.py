from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(Thread)
admin.site.register(Member)
admin.site.register(Message)
admin.site.register(UploadFile)
admin.site.register(Filechat)