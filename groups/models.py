from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from accounts.models import *
from post.models import *
import datetime
import uuid
from mimetypes import guess_type
import os

# Create your models here.
private_choice=(
    ('1','publish'),
    ('2','private')
)
class Group(models.Model):
    admin=models.ForeignKey(User, on_delete=models.CASCADE)
    group_name=models.CharField(max_length=200,null=True)
    private=models.CharField(max_length=200,choices=private_choice)
    image_cover=models.ImageField(null=True)
    description=models.TextField(null=True)
    members=models.ManyToManyField(User,related_name='members')