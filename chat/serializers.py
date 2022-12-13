from .models import *
from accounts.models import *
from rest_framework import serializers
from django.contrib.auth.models import User
from datetime import timedelta
import datetime,jwt

class ThreadinfoSerializer(serializers.ModelSerializer):
    message_last=serializers.SerializerMethodField()
    count_message=serializers.SerializerMethodField()
    members=serializers.SerializerMethodField()
    class Meta:
        model=Thread
        fields=('id','group','message_last','members','count_message','name',)
    def get_message_last(self,obj):
        message=Message.objects.filter(thread=obj)
        if message.exists():
            message=message.last()
            return {'text':message.message,'filetype':message.get_message_filetype(),
            'user_id':message.user_id,'date_created':message.date_created,
            'list_file':[{'file':uploadfile.file.url,
            'file_preview':uploadfile.get_file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.get_filetype()}
            for uploadfile in message.message_file.all()
        ]}
    def get_count_message(self,obj):
        return Message.objects.filter(thread=obj).count()
    def get_members(self,obj):
        request=self.context.get("request") 
        listmember=Member.objects.filter(thread=obj).select_related('user__profile')
        return [{'id':member.id,'avatar':member.user.profile.avatar.url,'name':member.user.profile.name,'user_id':member.user_id,
        'online':member.user.profile.online,'is_online':member.user.profile.is_online} for member in listmember]
class FileThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model=Filechat
        fields=('id','file','message_id',)
class MediathreadSerializer(serializers.ModelSerializer):
    file=serializers.SerializerMethodField()
    file_preview=serializers.SerializerMethodField()
    list_file=serializers.SerializerMethodField()
    class Meta:
        model=Filechat
        fields=('id','file_preview','file','duration','list_file','message_id',)
    def get_file_preview(self,obj):
        return obj.get_file_preview()
    def get_list_file(self,obj):
        list_media=Filechat.objects.filter(message__thread=obj.message.thread).filter((~Q(file=None) & Q(file_name=None)) | ~Q(file_preview=None))
        if list_media.count()<=21:
            list_media=list_media
        else:
            if obj in list_media[:20]:
                list_media=list_media.filter(id__gte=obj.id)[:20]
            else:
                list_media=list_media.filter(id__lte=obj.id)[:20]
        return [{'id':media.id,'file':media.file.url,'file_preview':media.get_file_preview()} for media in list_media]
    def get_file(self,obj):
        return obj.file.url
    


class MessageSerializer(serializers.ModelSerializer):
    list_file=serializers.SerializerMethodField()
    media_story=serializers.SerializerMethodField()
    filetype=serializers.SerializerMethodField()
    class Meta:
        model=Message
        fields=('thread','id','user_id','date_created','filetype','message','list_file','story_id','media_story',)
    def get_list_file(self,obj):
        return [{'id':uploadfile.id,'file':uploadfile.file.url,
        'file_preview':uploadfile.get_file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.get_filetype()}
        for uploadfile in obj.message_file.all()]
    def get_media_story(self,obj):
        return obj.get_story()
    def get_filetype(self,obj):
        return obj.get_message_filetype()