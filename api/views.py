

# Create your views here.
from twilio.rest import Client
from django.db.models import Q
from django.conf import settings
from datetime import timedelta
from django.template.loader import get_template
from django.db.models import F
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView,
    UpdateAPIView, DestroyAPIView,GenericAPIView,
)
from rest_auth.serializers import PasswordResetConfirmSerializer
from rest_framework.authtoken.models import Token
from drf_multiple_model.views import ObjectMultipleModelAPIView
from django.core.paginator import Paginator
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Min, Count, Avg,Sum
from chat.models import *
from accounts.models import *

from rest_framework.decorators import api_view
from django_bulk_update.helper import bulk_update
from .serializers import (
UserSerializer,
UserprofileSerializer,VerifyOTPSerializer,VerifyEmailSerializer,UserinfoSerializer,
NotificationSerializer,PostSerializer,StorySerializer,StoryemojiSerializer,
UsernameSerializer,GetlistPostSerializer,CommentSerializer,
ProfileinfoSerializer,SearchSerializer,UserstorySerializer,SavedSerializer,
UserfriendSerializer,UserBirthdaySerializer,
FilepostSerializer,PostdetailSerializer,ThreadgroupSerializer,FriendsuggestedSerializer,
)
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from oauth2_provider.models import AccessToken, Application
from rest_framework.permissions import AllowAny, IsAuthenticated
import random
import string
import json
import datetime,jwt
from django.contrib.auth import authenticate,login,logout
from rest_framework import status,viewsets,generics
from django.contrib.auth.models import User
from rest_framework.exceptions import AuthenticationFailed
import paypalrestsdk
from paypalrestsdk import Sale
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters("password1", "password2")
)
paypalrestsdk.configure({
  'mode': 'sandbox', #sandbox or live
  'client_id': 'AY2deOMPkfo32qrQ_fKeXYeJkJlAGPh5N-9pdDFXISyUydAwgRKRPRGhiQF6aBnG68V6czG5JsulM2mX',
  'client_secret': 'EJBIHj3VRi77Xq3DXsQCxyo0qPN7UFB2RHQZ3DOXLmvgNf1fXWC5YkKTmUrIjH-jaKMSYBrH4-9RjiHA' })

account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN
client = Client(account_sid, auth_token)
current_date=datetime.datetime.now()
yesterday=current_date-timedelta(days=1)
def create_ref_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=14))
class RegisterView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({'error':True})

class UpdateOnline(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self,request):
        online=request.data.get('online')
        if online==False:
            Profile.objects.filter(user=request.user).update(online=False,is_online=timezone.now())
        return Response({'sucess':True})

class UserView(APIView):
    def get(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        if not token:
            raise AuthenticationFailed('Unauthenticated!')
        try:
            user=request.user
            Profile.objects.filter(user=user).update(online=True)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')
        serializer = UserinfoSerializer(user)

        return Response(serializer.data)

class CheckuserView(APIView):
    def post(self,request):
        username=request.data.get('username')
        email=request.data.get('email')
        check_user=User.objects.filter(Q(username=username) | Q(email=email))
        if check_user.exists():
            return Response({'error':True})
        else:
            usr_otp = random.randint(100000, 999999)
            Verifyemail.objects.create(email = email, code = usr_otp)
            email_html_template = get_template('register.html').render({'code':usr_otp})
            email_subject=f"{usr_otp} is your verification code - Verification Code To verify your account"
            email = EmailMessage(email_subject, email_html_template,to=[email])
            email.content_subtype = 'html'
            email.send()
            return Response({'error':False})

class SendOTPemailView(APIView):
    def post(self,request):
        email=request.data.get('email')
        reset=request.data.get('reset')
        user=User.objects.filter(email=email)
        if user.exists():
            usr_otp = random.randint(100000, 999999)
            Verifyemail.objects.create(email = email, code = usr_otp)
            context_data =  {'code': usr_otp,'user':user.first().username}
            email_html_template = get_template('reset.html').render(context_data)
            email_subject=f"{usr_otp} is your verification code - Change your password"
            email = EmailMessage(email_subject, email_html_template,to=[email])
            email.content_subtype = 'html'
            email.send()
            return Response({'error':False})
        else:
            return Response({'error':True})
            
class VerifyEmailView(APIView):
    serializer_class = VerifyEmailSerializer
    def post(self, request,*args, **kwargs):
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            email=serializer.validated_data['email']
            code=serializer.validated_data['code']
            reset=request.data.get('reset')
            verifyemail=Verifyemail.objects.filter(email=email).last()
            current_time=timezone.now()
            time_experi=current_time-verifyemail.created
            time=time_experi.seconds
            if verifyemail.code==code and time<60*15:
                if reset:
                    user=User.objects.get(email=email)
                    uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
                    token = default_token_generator.make_token(user)
                    return Response({'verify':True,'token':token,'uidb64':uidb64})
                else:
                    return Response({'verify':True})   
            else:
                return Response({'verify':False})
        else:
            return Response({'error':True})

class SendOTPphoneView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request, *args, **kwargs):
        phone=request.data.get('phone')
        login=request.data.get('login')
        reset=request.data.get('reset')
        usr_otp = random.randint(100000, 999999)
        otp=SMSVerification.objects.create(code=usr_otp,phone=phone)
        if login: 
            message = client.messages.create(
                body=f"DE DANG NHAP TAI KHOAN VUI LONG NHAP MA XAC THUC {otp.code}. Co hieu luc trong 15 phut. Khong chia se ma nay voi nguoi khac",
                from_=settings.TWILIO_FROM_NUMBER,
                to=str(phone)
            )
        elif reset:
            message = client.messages.create(
                body=f"DE CAP NHAT MAT KHAU VUI LONG NHAP MA XAC THUC {otp.code}. Co hieu luc trong 15 phut. Khong chia se ma nay voi nguoi khac",
                from_=settings.TWILIO_FROM_NUMBER,
                to=str(phone)
            )
        else:
            message = client.messages.create(
                body=f"DE DANG KY TAI KHOAN VUI LONG NHAP MA XAC THUC {otp.code}. Co hieu luc trong 15 phut. Khong chia se ma nay voi nguoi khac",
                from_=settings.TWILIO_FROM_NUMBER,
                to=str(phone)
            )
        data={'id':otp.id}
        return Response(data)

class VerifyPhoneView(APIView):
    serializer_class = VerifyOTPSerializer
    def post(self, request,*args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone=serializer.validated_data['phone']
            code=serializer.validated_data['code']
            reset=request.data.get('reset')
            verifysms=SMSVerification.objects.filter(phone=phone).last()
            profile=Profile.objects.filter(phone=phone)
            current_time=timezone.now()
            time_experi=current_time-verifysms.created
            time=time_experi.seconds
            if verifysms.code==code and time<15*60:
                verifysms.verified=True
                verifysms.save()
                if profile.exists():
                    if reset:
                        user=profile.first().user
                        uidb64 = urlsafe_base64_encode(smart_bytes(user=profile.first().user_id))
                        token = default_token_generator.make_token(profile.first().user)
                        return Response({'verify':True,'token':token,'uidb64':uidb64})
                    return Response({'verify':True,'image':profile.first().image.url,'username':profile.first().user.username,'user_id':profile.first().user_id})
                else:
                    return Response({'verify':True})
            else:
                return Response({'verify':False})
        else:
            return Response({'error':True})


class LoginView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request,):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        token=request.data.get('token')
        user_id=request.data.get('user_id')
        if token:
            token = AccessToken.objects.get(token=token)
            user = token.user
        elif user_id:
            user=User.objects.get(id=user_id)
        else:
            if email:
                user = authenticate(request, email=username, password=password)
            else:
                user = authenticate(request, username=username, password=password)
        try:
            refresh = RefreshToken.for_user(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'access_expires': timezone.now()+settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
            }
            return Response(data)
        except Exception:
            raise AuthenticationFailed('Unauthenticated!')
class Listtag(APIView):
    def get(self,request):
        keyword=request.GET.get('keyword')
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(profile=profile)
        listuser=User.objects.filter(friend_user__in=listfriend,profile__name__startswith=keyword).select_related('profile').order_by('profile__name')
        if keyword:
            listuser=listuser.filter(profile__name__startswith=keyword)
        serializer = UserinfoSerializer(listuser[:10],many=True, context={"request": request})
        return Response(serializer.data)

class FileloadAPI(APIView):
    def post(self,request):
        file=request.FILES.get('file')
        file_preview=request.FILES.get('file_preview')
        duration=request.POST.get('duration')
        id=request.POST.get('id')
        edit=request.POST.get('edit')
        data={}
        if edit:
            fileupload=Fileupload.objects.get(id=id)
            fileupload.duration=float(duration)
            if file:
                fileupload.file=file
            if file_preview:
                fileupload.file_preview=file_preview
            fileupload.save()
            data.update({'id':video.id,'file':video.file.url,'file_preview':video.get_file_preview(),'duration':video.duration})
        elif id:
            Fileupload.objects.get(id=id).delete()
        else:
            duration=float(duration)
            video=Fileupload.objects.create(user=request.user,file=file,file_preview=file_preview,duration=int(duration))
            data.update({'id':video.id,'file':video.file.url,'file_preview':video.get_file_preview(),'duration':video.duration})
        return Response(data)

class Uploadstory(APIView):
    def post(self,request):
        file=request.FILES.get('file')
        file_preview=request.FILES.get('file_preview')
        duration=request.POST.get('duration')
        caption=request.POST.get('caption')
        list_tags=request.POST.getlist('tag')
        viewer=request.POST.getlist('viewer')
        story=Story.objects.create(caption=caption,user=request.user,viewer=viewer)
        if file:
            fileupload=Fileupload.objects.create(user=request.user,file=file,file_preview=file_preview,duration=duration)
            story.fileupload=fileupload
        story.tags.add(*list_tags)
        story.save()
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(profile=profile)
        listuser=User.objects.filter(friend_user__in=listfriend)
        listremain=listuser.exclude(id__in=list_tags)
        listnotifitag=[Notification(receiver_id=list_tags[i],user=request.user,notification_type=4,story=story) for i in range(len(list_tags))]
        listnotififriend=[Notification(receiver=listuser[i],user=request.user,notification_type=6,story=story) for i in range(listremain.count())]
        listnotifi=listnotifitag.extend(listnotififriend)
        Notification.objects.bulk_create(listnotifi)
        Profile.objects.filter(user__in=listuser).update(count_notify_unseen=F('count_notify_unseen')+1)
        return Response([{'receiver_id':user.id,'notification_type':6} for user in listuser])

class FilepostAPI(APIView):
    def get(self,request):
        id=request.GET.get('id')
        post_id=request.GET.get('post_id')
        post=Post.objects.get(id=post_id)
        file=Fileuploadpost.objects.get(id=id)
        serializer = FilepostSerializer(file, context={"request": request})
        return Response(serializer.data)
    def post(self,request):
        id=request.POST.get('id')
        tagfile=request.POST.get('tagfile')
        note=request.POST.get('note')
        file=Fileuploadpost.objects.get(id=id)
        if tagfile:
            file.tags=tagfile
        else:
            file.note=note
        file.save()
        return Response({'ok':'ok'})

class ListfrienduserAPI(APIView):
    def get(self,request):
        keyword=request.GET.get('keyword')
        offset=request.GET.get('offset')
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(profile=profile)
        listuser=User.objects.filter(friend_user__in=listfriend).select_related('profile')
        if keyword:
            listuser=listuser.filter(profile__name__startswith=keyword)
        count=listuser.count()
        from_item=0
        if offset:
            from_item=int(offset)
        to_item=from_item+10
        if from_item+10>=count:
            to_item=count
        serializer = UserfriendSerializer(listuser[from_item:to_item],many=True, context={"request": request})
        return Response({'listfriend':serializer.data,'count':count})

class Uploadpost(APIView):
    def post(self,request):
        image=request.FILES.getlist('image')
        video=request.FILES.getlist('video')
        video_preview=request.FILES.getlist('video_preview')
        duration=request.POST.getlist('duration')
        caption=request.POST.get('caption')
        list_tags=request.POST.getlist('tag')
        viewer=request.POST.get('viewer')
        tagfile=request.POST.getlist('tagfile')
        except_id=request.POST.getlist('except_id')
        specific_id=request.POST.getlist('specific_id')
        noteimage=request.POST.getlist('noteimage')
        notevideo=request.POST.getlist('notevideo')
        emotion=request.POST.get('emotion')
        group_id=request.POST.get('group_id')
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(profile=profile)
        post,created = Post.objects.get_or_create(user=request.user,viewer=viewer,caption=caption,emotion=emotion,group_id=group_id)
        if viewer=='3' or viewer=='6':
            post.exception_viewer.set(except_id)
        if viewer=='5' or viewer=='6':
            post.accept_viewer.set(specific_id)
        if viewer=='7':
            listfriend=listfriend.filter(best_friend=True)
        if viewer=='8':
            listfriend=listfriend.filter(acquaintance=True)
        if viewer=='9':
            listfriend=listfriend.filter(unnamed_list =True)
        listuser=User.objects.filter(friend_user__in=listfriend)
        if viewer=='7' or viewer=='8' or viewer=='9':
            post.accept_viewer.add(*listuser)
        listremain=listuser.exclude(id__in=list_tags)
        listnotifi=list()
        if len(list_tags)>0:
            post.tags.set(list_tags)
        notifitag=[Notification(receiver_id=list_tags[i],user=request.user,post=post,notification_type=4) for i in range(len(list_tags))]
        notififriend=[Notification(receiver=receiver,user=request.user,post=post,notification_type=6) for receiver in listremain]
        listnotifi=notifitag+notififriend
        Profile.objects.filter(user__in=listuser).update(count_notify_unseen=F('count_notify_unseen')+1)
        listimage=[Fileuploadpost(
                user=request.user,
                file=image[i],
                tags=tagfile[i],
                post=post,
                note=noteimage[i]
            ) for i in range(len(image))]
        
        listvideo=[Fileuploadpost(
            user=request.user,
            file=video[i],
            note=notevideo[i],
            duration=duration[i],
            file_preview=video_preview[i],
            post=post,
        ) for i in range(len(video))]
        listfile=listimage+listvideo
        Fileuploadpost.objects.bulk_create(listfile)
        Notification.objects.bulk_create(listnotifi)
        return Response({'y':'f'})

class SearchAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class=SearchSerializer
    def get(self,request):
        listsearch=Searchcurrent.objects.filter(user=request.user).order_by('-id')
        serializer = SearchSerializer(listsearch,many=True, context={"request": request})
        return Response(serializer.data)
    def post(self,request):
        keyword=request.data.get('keyword')
        user_id=request.data.get('user_id')
        search_id=request.data.get('search_id')
        if search_id:
            Searchcurrent.objects.get(id=search_id).delete()
        else:
            Searchcurrent.objects.get_or_create(user=request.user,keyword=keyword,user_search_id=user_id)
        return Response({'ok':'ok'})

class TopsearchAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class=SearchSerializer
    def get(self,request):
        keyword=request.GET.get('keyword')
        listsearch=Searchcurrent.objects.filter(user_search=None)
        if keyword:
            listsearch=listsearch.filter(keyword__startswith=keyword)
        serializer = SearchSerializer(listsearch,many=True, context={"request": request})
        return Response(serializer.data)

class Listgroupchat(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class=ThreadgroupSerializer
    def get(self,request):
        listgroup=Thread.objects.filter(participant=request.user,group=True)
        serializer = ThreadgroupSerializer(listgroup,many=True, context={"request": request})
        return Response(serializer.data)

class ListfriendAPI(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class=UserprofileSerializer
    def get(self,request):
        keyword=request.GET.get('keyword')
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(profile=profile)
        listuser=User.objects.filter(friend_user__in=listfriend).select_related('profile')
        if keyword:
            listuser=listuser.filter(profile__name__startswith=keyword)
        serializer = UserprofileSerializer(listuser,many=True, context={"request": request})
        return Response(serializer.data)
    
class ListpostAPI(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializers_class=PostSerializer
    def get(self,request):
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(Q(profile=profile) & ~Q(user__in=profile.hide_post_user.all()))
        listuser=User.objects.filter(friend_user__in=listfriend)
        listpostuser=Post.objects.filter(Q(user=request.user)).select_related('user__profile').prefetch_related('file_post').prefetch_related('post').prefetch_related('tags')
        listpostfriend=Post.objects.filter((Q(user__in=listuser) & (Q(viewer='2') | Q(viewer='3') | Q(viewer='1') ))|((Q(viewer='5') | Q(viewer='6')| Q(viewer='7')|Q(viewer='8')|Q(viewer='9')) & Q(accept_viewer=request.user))).exclude(Q(exception_viewer=request.user)).exclude(viewer='4').exclude(hide_post=request.user).select_related('user__profile').prefetch_related('file_post').prefetch_related('post').prefetch_related('tags')
        count_post=listpostuser.count()+listpostfriend.count()
        listpost=listpostuser.union(listpostfriend)
        item_from=0
        from_to=request.GET.get('from_item') 
        if from_to:
            item_from=int(from_to)
        to_item=item_from+3
        if item_from>=count_post:
            to_item=count_post
        listpost=listpost[item_from:to_item]
        serializer = PostSerializer(listpost,many=True, context={"request": request})
        return Response(serializer.data)

class Storyfriend(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializers_class=StorySerializer
    def get(self,request,id):
        liststory=Story.objects.filter(user_id=id,created__gte=yesterday).select_related('user').prefetch_related('fileupload')
        serializer = StorySerializer(liststory,many=True, context={"request": request})
        return Response(serializer.data)

class Getfriendstory(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class=UserstorySerializer
    def get_queryset(self):
        request=self.request
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(profile=profile).exclude(user__in=profile.hide_story_user.all())
        liststory=Story.objects.filter((Q(user=request.user) | Q(user__friend_user__in=listfriend)) & Q(created__gte=yesterday)).select_related('user__profile').prefetch_related('fileupload')  
        listuser=User.objects.filter(story__in=liststory).distinct()
        return listuser

class Actionstory(APIView):   
    def post(self,request,id):
        user=request.user
        emoji=request.data.get('emoji')
        action=request.data.get('action')
        story=Story.objects.get(id=id)
        if user.id!=story.user_id:
            if action=='view':
                story_emotions=Story_emotions.objects.get_or_create(user=request.user,story_id=id)
            elif action=='emotion':
                story_emotions,created=Story_emotions.objects.get_or_create(user=request.user,story_id=id)
                story_emotions.list_emoji=story_emotions.list_emoji+','+emoji
                story_emotions.save()
                notification=Notification.objects.filter(story_id=id,notification_type=1,user=request.user)
                if notification.exists():
                    pass
                else:
                    Notification.objects.create(receiver_id=story.user_id,story_id=id,notification_type=1,user=request.user,text_preview=emoji)
                    
                    Profile.objects.filter(user=story.user).update(count_notify_unseen=F('count_notify_unseen')+1)
            elif action=='turnoff':
                profile=Profile.objects.get(user=request.user)
                profile.hide_story.add(story.user_id)
            else:
                reportstory,created=Reportstory.objects.get_or_create(user=request.user,story_id=id)
                reportstory.reason=reason
                reportstory.save()
        return Response({'ok':'ok'})
    def delete(self,request,id):
        Story.objects.get(id=id).delete()
        return Response({'ọk':'oj'})

class Actionpost(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,id):
        emoji=request.GET.get('emoji')
        action=request.GET.get('action')
        post=Post.objects.get(id=id)
        if emoji:
            listemoji=Post_emotions.objects.filter(post_id=id,emotion=emoji).select_related('user')
            listuser=User.objects.filter(post_emotions__in=listemoji)
            serializer = UsernameSerializer(listuser,many=True, context={"request": request})
            return Response(serializer.data)
        else:
            if action=='editpost':
                serializer = PostdetailSerializer(post,context={"request": request})
                return Response(serializer.data)
            elif action=='savepost':
                saved=Saved.objects.filter(user=request.user)
                serializer=SavedSerializer(saved,many=True,context={"request": request})
                return Response(serializer.data)
            else:
                serializer =GetlistPostSerializer(post,context={"request": request})
                return Response(serializer.data)
    def post(self,request,id):
        user=request.user
        action=request.data.get('action')
        body=request.data.get('body')
        list_tags=request.POST.getlist('tag')
        reason=request.data.get('reason')
        parent_id=request.data.get('parent_id')
        text_preview=request.data.get('text_preview')
        emoji=request.data.get('emoji')
        file_id=request.POST.get('file_id')
        viewer=request.POST.get('viewer')
        except_id=request.POST.getlist('except_id')
        specific_id=request.POST.getlist('specific_id')
        fileupdate_id=request.POST.getlist('fileupdate_id')
        filevideoupdate_id=request.POST.getlist('filevideoupdate_id')
        image=request.FILES.getlist('image')
        video=request.FILES.getlist('video')
        video_preview=request.FILES.getlist('video_preview')
        videoupdate_preview=request.FILES.getlist('videoupdate')
        duration=request.POST.getlist('duration')
        caption=request.POST.get('caption')
        tagfile=request.POST.getlist('tagfile')
        noteimage=request.POST.getlist('noteimage')
        notevideo=request.POST.getlist('notevideo')
        notefileupdate=request.POST.getlist('notefileupdate')
        tagfileupdate=request.POST.getlist('tagfileupdate')
        save_id=request.POST.get('save_id')
        folder=request.POST.get('folder')
        date=request.POST.get('date')
        post=Post.objects.get(id=id)
        data={}
        listnotifications=list()
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(profile=profile)
        listuser=User.objects.filter(friend_user__in=listfriend)
        if action=='emotion':
            post_emotions=Post_emotions.objects.filter(user=request.user,post_id=id)
            if emoji:
                if post_emotions.exists():
                    post_emotions.update(emotion=emoji)     
                else:
                    Post_emotions.objects.create(user=request.user,post_id=id,emotion=emoji)
                    post.turn_on_notifications.add(request.user)
                notification=Notification.objects.filter(post_id=id,notification_type=1,user=request.user)
                if notification.exists():
                    pass
                else:
                    if post.user not in post.turn_off_notifications.all() and post.user!=request.user:
                        notification=Notification.objects.create(receiver_id=post.user_id,post_id=id,notification_type=1,user=request.user,text_preview=emoji) 
                        listnotifications.append({'id':notification.id,'notification_type':1,'receiver_id':post.user_id,'user_id':request.user.id,'avatar':request.user.profile.avatar.url,'name':request.user.profile.name,'gender':user.profile.gender})
                        Profile.objects.filter(user=post.user).update(count_notify_unseen=F('count_notify_unseen')+1)
            else:
                Post_emotions.objects.filter(user=request.user,post_id=id).delete()
            
            post_emotions=Post_emotions.objects.filter(post_id=id).order_by()
            data.update({'listnotifications':listnotifications,'list_emoji':post_emotions.values('emotion').distinct()})
            
        elif action=='share':
            Sharepost.objects.get_or_create(user=user,post_id=id)
            data.update({'count_share':uploadvideo.count_share()})
        elif action=='hidden':
            if user in post.hide_post.all():
                post.hide_post.remove(user)
            else:
                post.hide_post.add(user)
            
        elif action=='update':
            
            listfileupdate=Fileuploadpost.objects.filter(id__in=fileupdate_id)
            Fileuploadpost.objects.filter(post_id=id).exclude(id__in=fileupdate_id).delete()
            post.viewer=viewer
            if viewer=='3' or viewer=='6':
                post.exception_viewer.set(except_id)
            if viewer=='5' or viewer=='6':
                post.accept_viewer.set(specific_id)
            if viewer=='7':
                listfriend=listfriend.filter(best_friend=True)
            if viewer=='8':
                listfriend=listfriend.filter(acquaintance=True)
            if viewer=='9':
                listfriend=listfriend.filter(unnamed_list =True)
            if viewer=='7' or viewer=='8' or viewer=='9':
                post.accept_viewer.set(listuser)
            
            listimage=[Fileuploadpost(
                user=request.user,
                file=image[i],
                tags=tagfile[i],
                post_id=id,
                note=noteimage[i]
            ) for i in range(len(image))]
        
            listvideo=[Fileuploadpost(
                    user=request.user,
                    file=video[i],
                    note=notevideo[i],
                    duration=duration[i],
                    file_preview=video_preview[i],
                    post_id=id,
                ) for i in range(len(video))]
            listfile=listimage+listvideo
            Fileuploadpost.objects.bulk_create(listfile)
            listvideoupdate=listfileupdate.filter(id__in=filevideoupdate_id)
            listimageupdate=listfileupdate.exclude(id__in=filevideoupdate_id)
            for filevideo in listvideoupdate:
                for i in range(len(videoupdate_preview)):
                    if i==list(listvideoupdate).index(filevideo):
                        filevideo.file_preview=videoupdate_preview[i]
            for fileimage in listimageupdate:
                for i in range(len(notefileupdate)):
                    if i==list(listimageupdate).index(fileimage):
                        fileimage.tags=tagfileupdate[i] 
                        fileimage.note=notefileupdate[i]            
            post.save()
            bulk_update(listvideoupdate,update_fields=['file_preview'])
            bulk_update(listimageupdate,update_fields=['note','tags'])
        elif action=='editviewer':
            profile=Profile.objects.get(user=request.user)
            listfriend=Friend.objects.filter(profile=profile)
            post.viewer=viewer
            if viewer=='3' or viewer=='6':
                post.exception_viewer.set(except_id)
            if viewer=='5' or viewer=='6':
                post.accept_viewer.set(specific_id)
            if viewer=='7':
                listfriend=listfriend.filter(best_friend=True)
            if viewer=='8':
                listfriend=listfriend.filter(acquaintance=True)
            if viewer=='9':
                listfriend=listfriend.filter(unnamed_list =True)
            listuser=User.objects.filter(friend_user__in=listfriend)
            if viewer=='7' or viewer=='8' or viewer=='9':
                post.accept_viewer.set(listuser)
            post.save()
        elif action=='comment':
            comment,created=Comment.objects.get_or_create(uploadfile_id=file_id,post=post,user=user,body=body,parent_id=parent_id,text_preview=text_preview)
            listuser=listuser.filter(id__in=list_tags)
            listusseron=post.turn_on_notifications.all().exclude(id__in=list_tags).exclude(id=post.user_id)
            for tag in listuser:
                if tag not in post.turn_off_notifications.all():
                    listnotifications.append(Notification(receiver=tag,post_id=id,user=request.user,notification_type=4))
            for tag in listusseron:
                listnotifications.append(Notification(receiver=tag,post_id=id,user=request.user,notification_type=2))
            comment.tags.add(*list_tags)
            if post.user!=request.user and post.user_id not in list_tags and post.user not in post.turn_off_notifications.all():
                notification,created=Notification.objects.get_or_create(receiver_id=post.user_id,post_id=id, user=request.user, notification_type=2) 
            Notification.objects.bulk_create(listnotifications)
            data.update({'id':comment.id,'listnotifications':[{'id':notification.id,'notification_type':notification.notification_type,'receiver_id':notification.receiver_id,'user_id':notification.user_id,'avatar':notification.user.profile.avatar.url,'name':notification.user.profile.name,'gender':notification.user.profile.gender} for notification in listnotifications]})
        elif action=='savepost':
            saved=Saved.objects.filter(posts=post,user=request.user)
            if saved.exists():
                saved.first().posts.remove(post)
            else:
                if folder:
                    saved,created=Saved.objects.get_or_create(folder=folder,user=request.user)
                    saved.posts.add(post)
                else:
                    saved=Saved.objects.get(id=save_id)
                    saved.posts.add(post)
        elif action=='editday':
            post.posted=date
            post.save()
        elif action=='turnoff':
            if user in post.turn_off_notifications.all():
                post.turn_off_notifications.remove(user)
                post.turn_on_notifications.add(user)
            else:
                post.turn_off_notifications.add(user)
                post.turn_on_notifications.remove(user)
            data.update({'action':action})
        else:
            if Reportpost.objects.filter(post_id=id,user=user).exists():
                Reportpost.objects.filter(post_id=id,user=user).update(reason=reason)
            else:
                Reportpost.objects.get_or_create(post_id=id,user=user,reason=reason)
        return Response(data)

    def delete(self,request,id):
        Post.objects.get(id=id).delete()
        return Response({'ọk':'oj'})

class Actionfilepost(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,id):
        emoji=request.GET.get('emoji')
        if emoji:
            listemoji=Filepost_emotions.objects.filter(filepost_id=id,emotion=emoji).select_related('user')
            listuser=User.objects.filter(filepost_emotions__in=listemoji)
            serializer = UsernameSerializer(listuser,many=True, context={"request": request})
            return Response(serializer.data)
        else:
            filepost=Fileuploadpost.objects.get(id=id)
            serializer =GetlistPostSerializer(filepost,context={"request": request})
            return Response(serializer.data)
    def post(self,request,id):
        user=request.user
        action=request.data.get('action')
        body=request.data.get('body')
        list_tags=request.POST.getlist('tag')
        reason=request.data.get('reason')
        parent_id=request.data.get('parent_id')
        text_preview=request.data.get('text_preview')
        emoji=request.data.get('emoji')
        file_id=request.POST.get('file_id')
        filepost=Fileuploadpost.objects.get(id=id)
        data={}
        if action=='emotion':
            filepost_emotions=Filepost_emotions.objects.filter(user=request.user,filepost_id=id)
            if emoji:
                if filepost_emotions.exists():
                    filepost_emotions.update(emotion=emoji)     
                else:
                    Filepost_emotions.objects.create(user=request.user,filepost_id=id,emotion=emoji)
                    filepost.post.turn_on_notifications.add(request.user)
                notification=Notification.objects.filter(filepost_id=id,notification_type=1,user=request.user)
                if notification.exists():
                    pass
                else:
                    if filepost.user not in filepost.turn_off_file.all():
                        notification=Notification.objects.create(receiver_id=post.user_id,filepost_id=id,notification_type=1,user=request.user,text_preview=emoji) 
                        listnotifications.append({'id':notification.id,'notification_type':1,'receiver_id':filepost.user_id,'user_id':request.user.id,'avatar':request.user.profile.avatar.url,'name':request.user.profile.name,'gender':user.profile.gender})
                        Profile.objects.filter(user=post.user).update(count_notify_unseen=F('count_notify_unseen')+1)
            else:
                Filepost_emotions.objects.filter(user=request.user,post_id=id).delete()
            filepost_emotions=Filepost_emotions.objects.filter(filepost_id=id).order_by()
            data.update({'listnotifications':listnotifications,'list_emoji':filepost_emotions.values('emotion').distinct()})
       
        elif action=='comment':
            comment,created=Comment.objects.get_or_create(uploadfile_id=file_id,filepost=filepost,user=user,body=body,parent_id=parent_id,text_preview=text_preview)
            listuser=listuser.filter(id__in=list_tags)
            listusseron=filepost.post.turn_on_file.all().exclude(id__in=list_tags).exclude(id=filepost.user_id)
            for tag in listuser:
                if tag not in filepost.turn_off_file.all():
                    listnotifications.append(Notification(receiver=tag,filepost_id=id,user=request.user,notification_type=4))
            for tag in listusseron:
                listnotifications.append(Notification(receiver=tag,filepost_id=id,user=request.user,notification_type=2))
            comment.tags.add(*list_tags)
            if filepost.user!=request.user and filepost.user_id not in list_tags and filepost.user not in filepost.turn_off_file.all():
                notification,created=Notification.objects.get_or_create(receiver_id=filepost.user_id,filepost_id=id, user=request.user, notification_type=2) 
            Notification.objects.bulk_create(listnotifications)
            data.update({'id':comment.id,'listnotifications':[{'id':notification.id,'notification_type':notification.notification_type,'receiver_id':notification.receiver_id,'user_id':notification.user_id,'avatar':notification.user.profile.avatar.url,'name':notification.user.profile.name,'gender':notification.user.profile.gender} for notification in listnotifications]})
        else:
            if Reportfilepost.objects.filter(filepost_id=id,user=user).exists():
                Reportpost.objects.filter(filepost_id=id,user=user).update(reason=reason)
            else:
                Reportfilepost.objects.get_or_create(filepost_id=id,user=user,reason=reason)
        return Response(data)

    def delete(self,request,id):
        Filepost.objects.get(id=id).delete()
        return Response({'ọk':'oj'})

class ListEmojStory(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializers_class=StoryemojiSerializer
    def get(self,request,id):
        story_emotions=Story_emotions.objects.filter(story_id=id)
        serializer = StoryemojiSerializer(story_emotions,many=True, context={"request": request})
        return Response(serializer.data)

class Listfriendsuggested(ListAPIView):
    def get(self,request):
        profile=Profile.objects.get(user=request.user)
        listuser=[]
        listfriend=Friend.objects.filter(profile=profile)
        for friend in listfriend:
            listsuggested=friend.user.profile
            listuser.append(listsuggested)
        listfriendsuggested=Friend.objects.filter(profile__in=listuser)
        listfriendsuggesteds=Profile.objects.filter(user__friend_user__in=listfriendsuggested).exclude(user=request.user).exclude(user__friend_user__in=listfriend).distinct()
        serializer = FriendsuggestedSerializer(listfriendsuggesteds,many=True, context={"request": request})
        return Response(serializer.data)

class ListcommentAPI(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializers_class=CommentSerializer
    def get(self,request,post_id): 
        listcomment=Comment.objects.filter(post_id=post_id).select_related('user__profile').select_related('uploadfile').prefetch_related('tags')
        serializer = CommentSerializer(listcomment,many=True, context={"request": request})
        return Response(serializer.data)

class ListcommentfilepostAPI(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializers_class=CommentSerializer
    def get(self,request,filepost_id,*args, **kwargs): 
        listcomment=Comment.objects.filter(filepost_id=filepost_id).select_related('user__profile').select_related('uploadfile').prefetch_related('tags')
        serializer = CommentSerializer(listcomment,many=True, context={"request": request})
        return Response(serializer.data)       

class FriendsBirthday(APIView):
    def get(self,request):
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(profile=profile)
        listuser=User.objects.filter(friend_user__in=listfriend).select_related('profile').order_by('profile__date_of_birth')
        serializer = UserBirthdaySerializer(listuser,many=True,context={"request": request})
        return Response(serializer.data)  
class Liststoryfriend(APIView):
    def get(self,request):
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(profile=profile).exclude(user__in=profile.hide_story_user.all())
        listuser=User.objects.filter(Q(friend_user__in=listfriend) | Q(id=request.user.id)).distinct()
        list_story=[]
        for user in listuser:
            story=Story.objects.filter(Q(created__gte=yesterday) & Q(user=user)).select_related('user__profile').prefetch_related('fileupload')
            if story.exists():
                story=story.last()
                list_story.append({'user_id':user.id,'caption':story.caption,
                'id':story.id,'avatar':user.profile.avatar.url,'name':user.profile.name,'file':story.get_file()}) 
        return Response(list_story)  

class Liststory(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializers_class=StorySerializer
    def get(self,request):
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(profile=profile)
        listuser=User.objects.filter(friend_user__in=listfriend).exclude(user__in=profile.hide_story_user.all())
        liststory=Story.objects.filter(user__in=listuser,created__gte=yesterday).select_related('user__profile').prefetch_related('fileupload')
        serializer = StorySerializer(liststory,many=True, context={"request": request})
        return Response(serializer.data)

class Actionfriend(APIView):
    def post(self,request):
        action=request.data.get('action')
        receiver_id=request.data.get('receiver_id')
        friend_type=request.data.get('friend_type')
        friend=Profile.objects.get(user_id=receiver_id)
        profile=Profile.objects.get(user=request.user)
        frienduser=User.objects.get(id=receiver_id)
        data={}
        if action=='hide_suggested':
            profile.hide_suggested.add(receiver_id)
        elif action=='follow':
            if frienduser in profile.followers.all():
                profile.followers.remove(receiver_id)
                data.update({'action':{'follow':False}})
            else:
                profile.followers.add(receiver_id)
                data.update({'action':{'follow':True}})
        elif action=='block':
            if frienduser in profile.blocked_users.all():
                profile.blocked_users.remove(receiver_id)
                data.update({'action':{'blocked':False}})
            else:
                profile.blocked_users.add(receiver_id)
                data.update({'action':{'blocked':True}})
        elif action=='unfriend':
            Friend.objects.filter((Q(user=request.user) & Q(profile=friend)) |(Q(user_id=receiver_id) & Q(profile=profile))).delete()
            Notification.objects.filter((Q(user=request.user) & Q(receiver=friend.user) & (Q(notification_type=5) | Q(notification_type=7)) ) |(Q(user_id=receiver_id) & (Q(notification_type=5) | Q(notification_type=7)) & Q(receiver=request.user))).delete()
            data.update({'action':{'friend':False}})
        elif action=='accept friend request':
            Friend.objects.bulk_create(
                [Friend(user=request.user,profile=friend),
                Friend(user_id=receiver_id,profile=profile),
                ]
            )
            profile.followers.add(receiver_id)
            profile.friend_invitation.remove(receiver_id)
            notification=Notification.objects.create(receiver_id=receiver_id,notification_type=7,user=request.user)
            Notification.objects.filter(notification_type=5,receiver=request.user,user_id=receiver_id).update(accept=True)
            friend.count_notify_unseen+=1
            friend.save()
            data.update({'action':{'friend':True,'friend_invitation':False},'listnotifications':[{'id':notification.id,'receiver_id':receiver_id,'notification_type':7,'user_id':request.user.id,'avatar':request.user.profile.avatar.url,'name':request.user.profile.name}]})
        elif action=='favorite':
            if frienduser in profile.likers.all():
                profile.likers.remove(receiver_id)
                data.update({'action':{'like':False}})
            else:
                profile.likers.add(receiver_id)
                data.update({'action':{'like':True}})
        elif action=='friend_invitation':
            if request.user in friend.friend_invitation.all():
                profile.followers.remove(receiver_id)
                friend.friend_invitation.remove(request.user)
                data.update({'action':{'friend_invitation':False}})    
                Notification.objects.filter(notification_type=5,user=request.user,receiver_id=receiver_id).delete()
                friend.count_notify_unseen-=1
                friend.save()
            else:
                friend.friend_invitation.add(request.user)
                profile.followers.add(receiver_id)
                notification=Notification.objects.create(receiver_id=receiver_id,notification_type=5,user=request.user)
                friend.count_notify_unseen+=1
                friend.save()
                data.update({'action':{'friend_invitation':True},'listnotifications':[{'id':notification.id,'receiver_id':notification.receiver_id,'notification_type':5,'user_id':request.user.id,'avatar':request.user.profile.avatar.url,'name':request.user.profile.name}]})
        else:
            friend=Friend.objects.get(user_id=receiver_id,profile=profile)
            if friend_type=='best_friend':
                if friend.best_friend==True:
                    friend.best_friend=False
                else:
                    friend.best_friend=True
            elif friend_type=='acquaintance':
                if friend.acquaintance==True:
                    friend.acquaintance=False
                else:
                    friend.acquaintance=True
            elif friend_type=='restricted':
                if friend.restricted==True:
                    friend.restricted=False
                else:
                    friend.acquaintance=True
            else :
                if friend.unnamed_list ==True:
                    friend.unnamed_list =False
                else:
                    friend.unnamed_list =True
            friend.save()
        return Response(data)

class ListFriendinvitationAPI(APIView):
    def get(self,request):
        profile=Profile.objects.get(user=request.user)
        listuser=profile.friend_invitation.all()
        listFriendinvitation=Profile.objects.filter(user__in=listuser)
        serializer =FriendsuggestedSerializer(listFriendinvitation,many=True,context={"request": request})
        return Response(serializer.data)

class Profileinfo(APIView):
    permission_classes = (IsAuthenticated,)
    serializers_class=ProfileinfoSerializer
    def get(self,request,username):
        profile=Profile.objects.get(user__username=username)
        serializer = ProfileinfoSerializer(profile,context={"request": request})
        return Response(serializer.data)
    def post(self,request,username):
        cover_image=request.FILES.get('cover_image')
        avatar=request.FILES.get('avatar')
        name=request.data.get('name')
        story=request.data.get('story')
        profile=Profile.objects.get(user__username=username)
        if cover_image:
            profile.cover_image=cover_image
        if avatar:
            profile.avatar=avatar
        if name:
            profile.name=name
        if story:
            profile.story=story
        profile.save()
        data={'story':profile.story,'cover_image':profile.get_cover_image(),'avatar':profile.avatar.url}
        return Response(data)

class GetcountNotifi(APIView):
    def get(self,request):
        user=request.user
        count=Notification.objects.filter(receiver=user).prefetch_related('receiver').select_related('user').count()
        return Response({'count':count})

class GetcountPost(APIView):
    def get(self,request):
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(Q(profile=profile) & ~Q(user__in=profile.hide_post_user.all()))
        listuser=User.objects.filter(friend_user__in=listfriend)
        listpostuser=Post.objects.filter(Q(user=request.user)).select_related('user__profile').prefetch_related('file_post')
        listpostfriend=Post.objects.filter((Q(user__in=listuser) & (Q(viewer='2') | Q(viewer='3') | Q(viewer='1') ))|((Q(viewer='5') | Q(viewer='6')| Q(viewer='7')|Q(viewer='8')|Q(viewer='9')) & Q(accept_viewer=request.user))).exclude(Q(exception_viewer=request.user)).exclude(viewer='4').exclude(hide_post=request.user).select_related('user__profile').prefetch_related('file_post')
        count=listpostuser.count()+listpostfriend.count()
        return Response({'count':count})

class Getcountstory(APIView):
    def get(self,request):
        profile=Profile.objects.get(user=request.user)
        listfriend=Friend.objects.filter(profile=profile)
        listuser=User.objects.filter(user=request.user,created__gte=yesterday)
        liststoryuser=Story.objects.filter(friend_user__in=listfriend)
        liststoryfriend=Story.objects.filter(user__in=listuser,created__gte=yesterday).exclude(user__in=profile.hide_story_user.all()).select_related('user').prefetch_related('fileupload')
        count=liststoryuser.count()+liststoryfriend.count()
        return Response({'count':count})

class ListNotifyAPI(APIView):
    permission_classes = (IsAuthenticated,)
    serializers_class=NotificationSerializer
    def get(self,request):
        user=request.user
        listnotify1= Notification.objects.filter(Q(receiver=user) & (Q(notification_type=5) | Q(notification_type=7))).select_related('user__profile')
        listnotify2= Notification.objects.filter(Q(receiver=user)).exclude(Q(notification_type=5) & Q(notification_type=7)).select_related('user__profile')   
        listnotify=listnotify1.union(listnotify2).order_by('-id')
        count_notifi=listnotify1.count()+listnotify2.count()
        Profile.objects.filter(user=user).update(count_notify_unseen=0)
        item_from=0
        from_to=request.GET.get('item_from') 
        if from_to:
            item_from=from_to
        to_item=item_from+10
        if item_from>=count_notifi:
            to_item=count_notifi
        listnotify=listnotify[item_from:to_item]
        serializer = NotificationSerializer(listnotify,many=True, context={"request": request})
        return Response(serializer.data)

class ActionNotification(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self,request,id):
        notification_type=request.data.get('notification_type')
        sender_id=request.data.get('id')
        return Response({'ok':'ok'})
    def delete(self,request,id):
        Notification.objects.get(id=id).delete()
        return Response({'ok':'ok'})

class Actioncomemnt(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class=UserprofileSerializer
    def get(self,request,id):
        listemoji=Comment_emotions.objects.filter(comment_id=id).values('emotion').annotate(count=Count('emotion')).order_by('-count')
        return Response(listemoji)
    def post(self,request,id):
        user=request.user
        action=request.data.get('action')
        body=request.data.get('body')
        list_tags=request.POST.getlist('tag')
        reason=request.data.get('reason')
        text_preview=request.data.get('text_preview')
        emoji=request.data.get('emoji')
        post_id=request.POST.get('post_id')
        filepost_id=request.POST.get('filepost_id')
        comment=Comment.objects.get(id=id)
        listnotifications=list()
        data={}
        if action=='emotion':
            comment_emotions=Comment_emotions.objects.filter(user=request.user,comment_id=id)
            if emoji:
                if comment_emotions.exists():
                    comment_emotions.update(emotion=emoji)
                else:
                    Comment_emotions.objects.create(user=request.user,comment_id=id,emotion=emoji)
                
                notification,created=Notification.objects.get_or_create(post_id=post_id,filepost_id=filepost_id,receiver_id=comment.user_id,comment_id=id,notification_type=1,user=request.user)
                notification.text_preview=emoji
                notification.save()
                if created:
                    listnotifications=[{'id':notification.id,'receiver_id':comment.user_id,'comment':id,'notification_type':1,'user_id':notification.user_id,'avatar':request.user.profile.avatar.url,'name':request.user.profile.name,'text_preview':emoji}]
                Profile.objects.filter(user=comment.user).update(count_notify_unseen=F('count_notify_unseen')+1)
            else:
                comment_emotions.delete()
            
            list_emoji=Comment_emotions.objects.filter(comment_id=id).values('emotion').distinct()
            data.update({'list_emoji':list_emoji,'listnotifications':listnotifications})
        elif action=='edit':
            comment.text_preview=text_preview
            comment.tags.set([None])
            comment.tags.add(*list_tags)
            comment.body=body
            comment.save()
        elif action=='hidden':
            hiddencomment,created=Hidecomment.get_or_create(user=request.user)
            hiddencomment.comments.add(id)
        elif action=='delete':
            Comment.objects.get(id=id).delete()
        else:
            if Reportcomment.objects.filter(comment_id=id,user=user).exists():
                Reportcomment.objects.filter(comment_id=id,user=user).update(reason=reason)
            else:
                Reportcomment.objects.get_or_create(comment_id=id,user=user,reason=reason)
        return Response(data)


    def delete(self,request,id):
        Comment.objects.get(id=id).delete()
        return Response({'ọk':'oj'})
        
class StoryuserAPI(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializers_class=StorySerializer
    def get(self,request):
        liststory=Story.objects.filter(user=request.user,created__gte=yesterday).select_related('user').prefetch_related('fileupload')
        serializer = StorySerializer(liststory,many=True, context={"request": request})
        return Response(serializer.data)

class PasswordResetView(APIView):
    def post(self, request, *args, **kwargs):
        email=request.data.get('email',None)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise NotAcceptable(_("Please enter a valid email."))
        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        token = default_token_generator.make_token(user)

        absurl = 'http://localhost:3000/forgot_password/' +uidb64+ '/'+token+'?email='+email
    
        email_body =f"Xin chao {user.username}, \nChúng tôi nhận được yêu cầu thiết lập lại mật khẩu cho tài khoản Anhdai của bạn.\nNhấn tại đây để thiết lập mật khẩu mới cho tài khoản Anhdai của bạn. \n{absurl}"
        data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': f"Thiết lập lại mật khẩu đăng nhập {user.username}"}
        
        email = EmailMessage(
            subject=data['email_subject'], body=data['email_body'], to=[data['to_email']])
        email.send()
        return Response(
            {"detail": "Password reset e-mail has been sent."},
            status=status.HTTP_200_OK,
        )



