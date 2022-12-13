from django.shortcuts import render
from django.contrib.auth.models import User
from django.conf import settings
from django_bulk_update.helper import bulk_update
from django.utils import timezone
# Create your views here.
from .models import *
from django.db.models import Q
from django.db.models import Max, Min, Count, Avg,Sum
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView,
    UpdateAPIView, DestroyAPIView,GenericAPIView,
)
from .serializers import ThreadinfoSerializer,MessageSerializer,MediathreadSerializer,FileThreadSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

class CountmessageAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,id):
        listmessage=Message.objects.filter(thread_id=id)
        count_message=listmessage.count()
        data = {
           'count':count_message
        }
        return Response(data)
class UploadfileMessage(APIView):
    def delete(self,request,id):
        UploadFile.objects.get(id=id).delete()
        return Response({'ok':'pj'})
       
class ActionThread(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,id):
        listmessage=Message.objects.filter(thread_id=id).prefetch_related('message_file').order_by('-id')
        count_message=listmessage.count()
        item_from=0
        offset=request.GET.get('offset') 
        if offset:
            item_from=int(offset)
        to_item=item_from+10
        if item_from>=count_message:
            to_item=count_message
        listmessage=listmessage[item_from:to_item]
        serializer = MessageSerializer(listmessage,many=True, context={"request": request})
        return Response(serializer.data)
    def post(self,request,id,*args, **kwargs):
        action=request.data.get('action')
        gim=request.POST.get('gim')
        unread=request.data.get('unread')
        sent_by_id = request.data.get('send_by')
        listmessage=list()
        thread=Thread.objects.get(id=id)
        if action=='gim':
            if gim=='true':
                thread.gim=True
                data.update({'gim':True})
            else:
                thread.gim=False
                data.update({'gim':False})
            thread.save()
        elif action=='unread':
            if unread=='true':
                messages=Message.objects.filter(thread=thread)
                if messages.exists():
                    messages.last().seen=False
                    messages.last().save()
            else:
                Message.objects.filter(thread=thread).update(seen=True)
        elif action=='create-message':
            msg = request.data.get('message')
            image=request.FILES.getlist('image')
            file=request.FILES.getlist('file')
            file_preview=request.FILES.getlist('file_preview')
            duration=request.POST.getlist('duration')
            name=request.POST.getlist('name') 
            story_id=request.POST.get('story_id') 
            if msg:    
                message=Message.objects.create(thread_id=id,user=request.user,message=msg,story_id=story_id)
                listmessage.append({'id':message.id,'message':message.message,'filetype':message.get_message_filetype(),
                'user_id':message.user_id,'date_created':message.date_created,'story_id':message.story_id,'media_story':message.get_story(),
                'list_file':[]})
            if image:
                message=Message.objects.create(thread_id=id,user=request.user)
                list_file_chat=Filechat.objects.bulk_create([Filechat(upload_by=request.user,file=image[i],message=message) for i in range(len(image))])
                listmessage.append({'id':message.id,'message':message.message,'filetype':message.get_message_filetype(),
                        'user_id':message.user_id,'date_created':message.date_created,
                        'list_file':[{'id':uploadfile.id,'file':uploadfile.file.url,'filetype':uploadfile.get_filetype()}
                for uploadfile in list_file_chat
                ]})
            if file: 
                list_file_preview=[None for i in range(len(file))]
                for i in range(len(list_file_preview)):
                    for j in range(len(file_preview)):
                        if i==j:
                            list_file_preview[i]=file_preview[j]
                count=Message.objects.last().id
                messages=Message.objects.bulk_create([
                Message(thread_id=id,
                    id=count+i+1,
                    user=request.user
                ) for i in range(len(file))]) 
                        
                Filechat.objects.bulk_create([Filechat(message_id=messages[i].id,upload_by=request.user,duration=float(duration[i]),file_preview=list_file_preview[i],file=file[i],file_name=name[i]) for i in range(len(file))])
                listmessage=[{'id':message.id,'message':message.message,'filetype':message.get_message_filetype(),
                'user_id':message.user_id,'date_created':message.date_created,
                'list_file':[{'id':uploadfile.id,'file':uploadfile.file.url,'file_name':uploadfile.filename(),
                'file_preview':uploadfile.get_file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.get_filetype()}
                for uploadfile in message.message_file.all()
                ]} for message in messages]
            return Response(listmessage)
        else:
            thread.delete()
            
class CountThread(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        count=Thread.objects.filter(participant=request.user).count()
        return Response({'count':count})
class ListThreadAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user=request.user
        threads=Thread.objects.filter(participant=user).exclude(message_thread=None)
        serializer = ThreadinfoSerializer(threads,many=True, context={"request": request})
        return Response(serializer.data)
    def post(self, request, *args, **kwargs):
        user=request.user
               
class MediathreadAPI(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        id=request.GET.get('id')
        file=Filechat.objects.get(id=id)
        serializer = MediathreadSerializer(file, context={"request": request})
        return Response(serializer.data)

class FilethreadAPI(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        id=request.GET.get('id')
        file=Filechat.objects.get(id=id)
        serializer = FileThreadSerializer(file, context={"request": request})
        return Response(serializer.data)

class Checkgroup(APIView):
    def post(self,request):
        member=request.data.get('member')
        group=request.data.get('group')
        thread=Thread.objects.filter(group=False)
        listuser=User.objects.filter(id__in=member).select_related('profile')
        listmessage=list()
        if group:
            thread=thread.filter(group=True)
        for user in listuser:
            thread=thread.filter(participant=user)
        if thread.exists():
            listmember=Member.objects.filter(thread=thread[0]).select_related('user__profile')
            messages=Message.objects.filter(thread=thread.first()).prefetch_related('message_file').order_by('-id')[:10]
            listmessage=[{'id':message.id,'message':message.message,'filetype':message.get_message_filetype(),
                'user_id':message.user_id,'date_created':message.date_created,
                'list_file':[{'id':uploadfile.id,'file':uploadfile.file.url,'file_name':uploadfile.filename(),
                'file_preview':uploadfile.get_file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.get_filetype()}
                for uploadfile in message.message_file.all()
                ]} for message in messages
                ]
            data={'exist':True,
            'messages':listmessage,'thread':{'id':thread[0].id,'count_message':thread[0].count_message(),'group_name':thread[0].group_name,'emoticon':thread[0].emoticon},
            'members':[{'nickname':member.nickname,'user_id':member.user_id,'id':member.id,
            'avatar':member.user.profile.avatar.url,'username':member.user.username,
            'name':member.user.profile.name,'online':member.user.profile.online,'is_online':member.user.profile.is_online} for member in listmember]}
            return Response(data)
        else:
            return Response({'exist':False})

class CreateThread(APIView):
    def post(self,request):
        member=request.data.get('member')
        group=request.data.get('group')
        listmessage=list()
        listuser=User.objects.filter(id__in=member).select_related('profile')
        thread=Thread.objects.filter(group=False)
        if group:
            thread=thread.filter(group=True)
        for user in listuser:
            thread=thread.filter(participant=user)
        if thread.exists():
            listmember=Member.objects.filter(thread=thread[0]).select_related('user__profile')
            messages=Message.objects.filter(thread=thread.first()).prefetch_related('message_file').order_by('-id')[:10]
            listmessage=[{'id':message.id,'message':message.message,'story_id':message.story_id,'media_story':message.get_story(),'filetype':message.get_message_filetype(),
                'user_id':message.user_id,'date_created':message.date_created,
                'list_file':[{'id':uploadfile.id,'file':uploadfile.file.url,'file_name':uploadfile.filename(),
                'file_preview':uploadfile.get_file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.get_filetype()}
                for uploadfile in message.message_file.all()
                ]} for message in messages
                ]
            data={'messages':listmessage,
            'thread':{'id':thread[0].id,'count_message':thread[0].count_message(),
            'group_name':thread[0].group_name,'emoticon':thread[0].emoticon},
            'members':[{'nickname':member.nickname,'user_id':member.user_id,'id':member.id,
            'avatar':member.user.profile.avatar.url,'username':member.user.username,
            'name':member.user.profile.name,'online':member.user.profile.online,'is_online':member.user.profile.is_online} for member in listmember]}
            return Response(data)
        else:
            thread=Thread.objects.create(admin=request.user)
            if group:
                thread.group=True
            thread.participant.add(*member)
            thread.save()
            Member.objects.bulk_create([
                Member(user=listuser[i],nickname=listuser[i].profile.name,thread=thread)
                for i in range(len(list(listuser)))
            ])
            data={'messages':listmessage,'thread':{'id':thread.id,'count_message':0},'members':[{'user_id':member.id,'avatar':member.profile.avatar.url,'username':member.username,
            'name':member.profile.name,'online':member.profile.online,'is_online':member.profile.is_online} for member in listuser]}
            return Response(data)
   


