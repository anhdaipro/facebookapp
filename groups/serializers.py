from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
class GroupSerializer(serializers.ModelSerializer):
    members=serializers.SerializerMethodField()
    class Meta:
        model=Group
        fields =['id','members','private','image_cover','description','group_name']
    def get_members(self,obj):
        listusers=obj.members.all()
        return {'list_avatar':[user.profile.avatar.url for user in listusers[:6]],'count':listusers.count()}