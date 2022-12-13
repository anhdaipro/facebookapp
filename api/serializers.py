from rest_framework import serializers
from accounts.models import *
from notifications.models import *
from post.models import *
from comment.models import *
from chat.models import *
from django.contrib import auth
from djoser.serializers import UserCreateSerializer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from datetime import timedelta
import datetime,jwt
current_date=datetime.datetime.now()
yesterday=current_date-timedelta(days=1)
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

class ProfilesingupSerializer(serializers.ModelSerializer):
    class Meta:
        model=Profile
        fields = ('phone','date_of_birth',)
        extra_kwargs = {'date_of_birth': {'required': False},
        'phone': {'required': False}} 

class UserSerializer(serializers.ModelSerializer):
    profile = ProfilesingupSerializer()
    class Meta:
        model = User
        fields = ['id', 'username','first_name','last_name', 'email', 'password','profile',]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        profile_data= validated_data.pop('profile', None)
        user = User.objects.create(**validated_data)
        if Profile.objects.filter(user=user).exists():
            Profile.objects.filter(user=user).update(**profile_data)
        return user

class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True},
        'email': {'read_only': True},
        'username': {'read_only': True},'email': {'read_only': True}}

class VerifyEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verifyemail
        fields=('id', 'email', 'code')
        extra_kwargs = {'code': {'write_only': True}}

class VerifyOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSVerification
        fields=('id', 'phone', 'code',)
        extra_kwargs = {'code': {'write_only': True}}
class UserhomeSerializer(serializers.ModelSerializer):
    avatar=serializers.SerializerMethodField()
    name=serializers.SerializerMethodField()
    class Meta:
        model=User
        fields=['username','id','avatar','name']
    def get_avatar(self,obj):
        return obj.profile.avatar.url
    def get_name(self,obj):
        return obj.profile.name

class UserinfoSerializer(UserhomeSerializer):
    count_notify_unseen=serializers.SerializerMethodField()
    count_message_unseen=serializers.SerializerMethodField()
    class Meta(UserhomeSerializer.Meta):
        fields =UserhomeSerializer.Meta.fields+['count_notify_unseen','count_message_unseen']
    def get_count_notify_unseen(self,obj):
        return obj.profile.count_notify_unseen
    def get_count_message_unseen(self,obj):
        return Member.objects.filter(user=obj,is_seen=False).count()

class FriendSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    class Meta:
        model=Friend
        fields=('id','username','id','avatar','name','isonline',)
    def get_user(self,obj):
        return {'username':obj.user.username,'avatar':obj.user.profile.avatar.url,'id':obj.user_id,'name':obj.user.profile.name}

class UserprofileSerializer(UserhomeSerializer):
    online=serializers.SerializerMethodField()
    is_online=serializers.SerializerMethodField()
    class Meta(UserhomeSerializer.Meta):
        fields=UserhomeSerializer.Meta.fields+['online','is_online']
    def get_online(self,obj):
        return obj.profile.online
    def get_is_online(self,obj):
        return obj.profile.is_online

class UserBirthdaySerializer(UserhomeSerializer):
    date_of_birth=serializers.SerializerMethodField()
    class Meta(UserhomeSerializer.Meta):
        fields =UserhomeSerializer.Meta.fields+['date_of_birth']
    def get_date_of_birth(self,obj):
        return obj.profile.date_of_birth
class UserfriendSerializer(UserhomeSerializer): 
    follow=serializers.SerializerMethodField()
    blocked=serializers.SerializerMethodField()
    friend=serializers.SerializerMethodField()
    friend_invitation=serializers.SerializerMethodField()
    class Meta(UserhomeSerializer.Meta):
        fields=UserhomeSerializer.Meta.fields+['follow','blocked','friend','friend_invitation']
    def get_follow(self,obj):
        request=self.context.get("request")
        follow=False
        profile=Profile.objects.get(user=request.user)
        if obj in profile.followers.all():
            follow= True
        return follow
    def get_friend_invitation(self,obj):
        invitation=False
        request=self.context.get("request") 
        profile=Profile.objects.get(user=request.user)
        if request.user in profile.friend_invitation.all():
            invitation=True
        return invitation
    def get_friend(self,obj):
        request=self.context.get("request")
        friend=False
        profile=Profile.objects.get(user=request.user)
        if Friend.objects.filter(user=obj,profile=profile).exists():
            friend=True
        return friend
    def get_blocked(self,obj):
        request=self.context.get("request")
        blocked=False
        profile=Profile.objects.get(user=request.user)
        if obj in profile.blocked_users.all():
            blocked= True
        return blocked
class UserstorySerializer(UserhomeSerializer): 
    online=serializers.SerializerMethodField()
    is_online=serializers.SerializerMethodField()
    count_new_story=serializers.SerializerMethodField()
    class Meta(UserhomeSerializer.Meta):
        fields=UserhomeSerializer.Meta.fields+['online','is_online','count_new_story']
    def get_online(self,obj):
        return obj.profile.online
    def get_is_online(self,obj):
        return obj.profile.is_online
    def get_count_new_story(self,obj):
        request=self.context.get("request")
        count=0
        if obj.id!=request.user.id:
            liststory= Story.objects.filter(user=obj,created__gte=yesterday)
            view_count=Story_emotions.objects.filter(user=request.user,story__in=liststory).count()
            count=liststory.count()-view_count
        return count
class FriendsuggestedSerializer(serializers.ModelSerializer): 
    mutual_friends=serializers.SerializerMethodField()
    avatar=serializers.SerializerMethodField()
    username=serializers.SerializerMethodField()
    friend=serializers.SerializerMethodField()
    friend_invitation=serializers.SerializerMethodField()
    follow=serializers.SerializerMethodField()
    class Meta:
        model=Profile
        fields=['id','username','user_id','name','avatar','mutual_friends','avatar','friend_invitation','follow','friend']
    def get_avatar(self,obj):
        return obj.avatar.url
    def get_username(self,obj):
        return obj.user.username
    def get_friend(self,obj):
        friend=False
        request=self.context.get("request") 
        listfriend=Friend.objects.filter(profile=obj,user=request.user)
        if listfriend.exists():
            friend=True
        return friend
    def get_follow(self,obj):
        follow=False
        request=self.context.get("request") 
        if request.user in obj.followers.all():
            follow=True
        return follow
    def get_friend_invitation(self,obj):
        invitation=False
        request=self.context.get("request") 
        
        if request.user in obj.friend_invitation.all():
            invitation=True
        return invitation
    def get_mutual_friends(self,obj):
        request=self.context.get("request")  
        listfriend1=Friend.objects.filter(profile=obj)
        listfriend2=Friend.objects.filter(profile=request.user.profile)
        listfriend=User.objects.filter(friend_user__in=listfriend1).filter(friend_user__in=listfriend2)
        return {'count':listfriend.count(),'listfriend':[friend.profile.avatar.url for friend in listfriend[:4]]}
class ProfileinfoSerializer(FriendsuggestedSerializer): 
    cover_image=serializers.SerializerMethodField()
    count_friend=serializers.SerializerMethodField()
    list_friend=serializers.SerializerMethodField()
    count_friend=serializers.SerializerMethodField()
    
    class Meta(FriendsuggestedSerializer.Meta):
        fields=FriendsuggestedSerializer.Meta.fields+['online','is_online','cover_image','list_friend','count_friend','story']
    def get_cover_image(self,obj):
        return obj.get_cover_image()
    def get_count_friend(self,obj):
        return obj.count_friend()
    def get_list_friend(self,obj):
        listfriend=Friend.objects.filter(profile=obj)
        return([friend.user.profile.avatar.url for friend in listfriend[:4]])
    
class SearchSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model=Searchcurrent
        fields=('id','keyword','user',)
    def get_user(self,obj):
        if obj.user_search:
            return {'username':obj.user.username,'avatar':obj.user.profile.avatar.url,'id':obj.user_id,'name':obj.user.profile.name}

class ProfileSerializer(serializers.ModelSerializer):
    user = UserinfoSerializer()
    following=serializers.SerializerMethodField()
    exists=serializers.SerializerMethodField()
    thread=serializers.SerializerMethodField()
    class Meta:
        model= Profile
        fields = ('user','profile_info','following','exists','thread',)
    def get_following(self,obj):
        request=self.context.get("request") 
        follow=False
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        if token:
            user=request.user
            if user in obj.followers_profile.all():
                follow=True
        return follow
    def get_exists(self,obj):
        request=self.context.get("request") 
        exist=False
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        if token:
            user=request.user
            threads = Thread.objects.filter(participants=user).filter(participants=obj.user).order_by('timestamp')
            if threads.exists():
                exist=True
        return exist
    def get_thread(self,obj):
        request=self.context.get("request") 
        thread_id=None
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        if token:
            user=request.user
            threads = Thread.objects.filter(participants=user).filter(participants=obj.user).order_by('timestamp')
            if threads.exists():
                thread_id=threads.first().id
        return thread_id

class StoryemojiSerializer(serializers.ModelSerializer):
    user=serializers.SerializerMethodField()
    class Meta:
        model=Story_emotions
        fields = ('user','id','list_emoji',)
    def get_user(self,obj):
        return {'username':obj.user.username,'avatar':obj.user.profile.avatar.url,'id':obj.user_id,'name':obj.user.profile.name}

class StorySerializer(serializers.ModelSerializer):
    file=serializers.SerializerMethodField()
    file_preview=serializers.SerializerMethodField()
    duration=serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    count_express_emotions=serializers.SerializerMethodField()
    express_emotions=serializers.SerializerMethodField()
    tags=serializers.SerializerMethodField()
    express_emotions=serializers.SerializerMethodField()
    reported=serializers.SerializerMethodField()
    class Meta:
        model=Story
        fields=('id','file','created','file_preview','caption','user','count_express_emotions','duration','express_emotions','reported','tags',)
    def get_file(self,obj):
        if obj.fileupload:
            return obj.fileupload.file.url
    def get_duration(self,obj):
        if obj.fileupload:
            return obj.fileupload.duration
    def get_file_preview(self,obj):
        if obj.fileupload:
            return obj.fileupload.get_file_preview()
    def get_tags(self,obj):
        return [{'username':tag.username,'name':tag.profile.name,'id':tag.id} for tag in obj.tags.all()]
    def count_express_emotions(self,obj):
        return obj.count_express_emotions()
    def get_user(self,obj):
        return {'username':obj.user.username,'picture':obj.user.profile.avatar.url,'id':obj.user_id,'name':obj.user.profile.name}
    def get_express_emotions(self,obj):
        request=self.context.get("request") 
        user=request.user
        emotioned=False
        express_emotions=Story_emotions.objects.filter(user=user,story=obj)
        if express_emotions.exists():
            emotioned=True
        return emotioned
    def get_reported(self,obj):
        request=self.context.get("request") 
        reported=False
        user=request.user
        if Reportstory.objects.filter(story=obj,user=user).exists():
            reported=True
        return reported

class UsernameSerializer(serializers.ModelSerializer):
    name=serializers.SerializerMethodField()
    class Meta:
        model=User
        fields=('name',)
    def get_name(self,obj):
        return obj.profile.name

class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model=Notification
        fields=('id','user','accept','date','notification_type','text_preview','story','post','comment',)
    def get_user(self,obj):
        return {'username':obj.user.username,'avatar':obj.user.profile.avatar.url,'id':obj.user_id,'name':obj.user.profile.name,'gender':obj.user.profile.gender}


class FilepostSerializer(serializers.ModelSerializer):
    
    list_file=serializers.SerializerMethodField()
    viewer=serializers.SerializerMethodField()
    user=serializers.SerializerMethodField()
    count_comment=serializers.SerializerMethodField()
    express_emotions=serializers.SerializerMethodField()
    list_emoji=serializers.SerializerMethodField()
    commented=serializers.SerializerMethodField()
    reported=serializers.SerializerMethodField()
    commented=serializers.SerializerMethodField()
    class Meta:
        model=Fileuploadpost
        fields=('id','file_preview','user','viewer','file','express_emotions',
        'count_express_emotions','reported','commented','list_emoji',
        'count_comment','duration','tags','note','list_file','post',)
    
    def get_user(self,obj):
        return {'avatar':obj.user.profile.avatar.url,'id':obj.user_id,'name':obj.user.profile.name,'online':obj.user.profile.online,'is_online':obj.user.profile.is_online}
    
    def get_viewer(self,obj):
        return obj.post.viewer
    def get_list_file(self,obj):
        post= obj.post
        listfile=Fileuploadpost.objects.filter(post=post)
        return ([file.id for file in listfile])
    def get_count_comment(self,obj):
        if obj.get_count_file()>1:
            return obj.count_comment()
        else:
            return obj.post.count_comment()
    def get_express_emotions(self,obj):
        request=self.context.get("request") 
        user=request.user
        express_emotions=Filepost_emotions.objects.filter(user=user,filepost=obj)
        if obj.get_count_file()>1:
            if express_emotions.exists():
                return express_emotions.first().emotion
        else:
            express_emotions=Post_emotions.objects.filter(user=user,post=obj.post)
            if express_emotions.exists():
                return express_emotions.first().emotion
    def get_count_express_emotions(self,obj):
        if obj.get_count_file()>1:
            return obj.count_express_emotions()
        else:
            return obj.post.count_express_emotions()
    def get_list_emoji(self,obj):
        request=self.context.get("request") 
        express_emotions=Filepost_emotions.objects.filter(filepost=obj).exclude(user=request.user).order_by()
        if obj.get_count_file()>1:
            if express_emotions.exists():
                return express_emotions.values('emotion').distinct()
        else:
            express_emotions=Post_emotions.objects.filter(post=obj.post).exclude(user=request.user).order_by()
            if express_emotions.exists():
                return express_emotions.values('emotion').distinct()
    def get_reported(self,obj):
        request=self.context.get("request") 
        reported=False
        user=request.user
        if obj.get_count_file()>1:
            if Reportfilepost.objects.filter(filepost=obj,user=user).exists():
                reported=True
        else:
            if Reportpost.objects.filter(post=obj.post,user=user).exists():
                reported=True
        return reported
    def get_commented(self,obj):
        request=self.context.get("request") 
        commented=False
        user=request.user
        if obj.get_count_file()>1:
            if Comment.objects.filter(filepost=obj,user=user).exists():
                commented=True
        else:
            if Comment.objects.filter(post=obj.post,user=user).exists():
                commented=True
        return commented

class GetlistPostSerializer(serializers.ModelSerializer):
    list_specific=serializers.SerializerMethodField()
    list_except=serializers.SerializerMethodField()
    class Meta:
        model=Post
        fields=('list_specific','list_except',)
    def get_list_specific(self,obj):
        return [{'username':user.username,'avatar':user.profile.avatar.url,'id':user.id,'name':user.profile.name} for user in obj.accept_viewer.all().select_related('profile')]
    def get_list_except(self,obj):
        return [{'username':user.username,'avatar':user.profile.avatar.url,'id':user.id,'name':user.profile.name} for user in obj.exception_viewer.all().select_related('profile')]

class ThreadgroupSerializer(serializers.ModelSerializer):
    count_message=serializers.SerializerMethodField()
    members=serializers.SerializerMethodField()
    class Meta:
        model= Thread
        fields=('id','group_name','group','members','count_message',)
    def get_count_message(self,obj):
        return Message.objects.filter(thread=obj).count()
    def get_members(self,obj):
        request=self.context.get("request") 
        listmember=Member.objects.filter(thread=obj).select_related('user__profile')
        return [{'id':member.id,'avatar':member.user.profile.avatar.url,'name':member.user.profile.name,'user_id':member.user_id,
        'online':member.user.profile.online,'is_online':member.user.profile.is_online} for member in listmember]

class PostSerializer(serializers.ModelSerializer):
    fileupload=serializers.SerializerMethodField()
    tags=serializers.SerializerMethodField()
    count_express_emotions=serializers.SerializerMethodField()
    count_share=serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    count_comment=serializers.SerializerMethodField()
    express_emotions=serializers.SerializerMethodField()
    reported=serializers.SerializerMethodField()
    list_emoji=serializers.SerializerMethodField()
    count_file=serializers.SerializerMethodField()
    list_emotioner=serializers.SerializerMethodField()
    commented=serializers.SerializerMethodField()
    saved=serializers.SerializerMethodField()
    turnon=serializers.SerializerMethodField()
    friend=serializers.SerializerMethodField()
    class Meta:
        model=Post
        fields=('id','list_emoji','viewer','commented','list_emotioner','fileupload',
        'count_file','count_comment','caption','posted','tags','user','saved',
        'count_express_emotions','count_share','comment','viewer','express_emotions',
        'reported','turnon','friend',)
    def get_list_emoji(self,obj):
        request=self.context.get("request") 
        express_emotions=Post_emotions.objects.filter(post=obj).exclude(user=request.user).order_by()
        if express_emotions.exists():
            return express_emotions.values('emotion').distinct()
    def get_list_emotioner(self,obj):
        express_emotions=Post_emotions.objects.filter(post=obj)
        return [item.user.profile.name for item in express_emotions[:10]]
    def get_fileupload(self,obj):
        fileupload=Fileuploadpost.objects.filter(post=obj)
        return [{'id':file.id,'file':file.file.url,'file_preview':file.get_file_preview()} for file in fileupload[:4] ]
    def get_saved(self,obj):
        request=self.context.get("request") 
        user=request.user
        saved=False
        savedpost=Saved.objects.filter(posts=obj,user=user)
        if savedpost.exists():
            saved=True
        return saved
    def get_tags(self,obj):
        return [{'username':tag.username,'name':tag.profile.name,'id':tag.id} for tag in obj.tags.all()]
    def get_count_express_emotions(self,obj):
        return obj.count_express_emotions()
    def get_count_share(self,obj):
        return obj.count_share()
    def get_count_file(self,obj):
        return obj.count_file()
    def get_user(self,obj):
        return {'avatar':obj.user.profile.avatar.url,'id':obj.user_id,'name':obj.user.profile.name,'online':obj.user.profile.online,'is_online':obj.user.profile.is_online}
    def get_count_comment(self,obj):
        return obj.count_comment()
    def get_friend(self,obj):
        friend=False
        request=self.context.get("request") 
        listfriend=Friend.objects.filter(profile=obj.user.profile,user=request.user)
        if listfriend.exists():
            friend=True
        return friend
    def get_express_emotions(self,obj):
        request=self.context.get("request") 
        user=request.user
        express_emotions=Post_emotions.objects.filter(user=user,post=obj)
        if express_emotions.exists():
            return express_emotions.first().emotion
    def get_reported(self,obj):
        request=self.context.get("request") 
        reported=False
        user=request.user
        if Reportpost.objects.filter(post=obj,user=user).exists():
            reported=True
        return reported
    def get_commented(self,obj):
        request=self.context.get("request") 
        commented=False
        user=request.user
        if Comment.objects.filter(post=obj,user=user).exists():
            commented=True
        return commented
    def get_turnon(self,obj):
        request=self.context.get("request") 
        turnon=False
        user=request.user
        listuseroff=obj.turn_off_notifications.all()
        listuseron=obj.turn_on_notifications.all()
        if user in listuseroff:
            turnon=False
        if Notification.objects.filter(post=obj,receiver=user).exclude(notification_type=6).exists() and user not in listuseroff:
            turnon=True
        if user in listuseron:
            turnon=True
        return turnon

class PostdetailSerializer(serializers.ModelSerializer):
    fileupload=serializers.SerializerMethodField()
    tags=serializers.SerializerMethodField()
    listspecific=serializers.SerializerMethodField()
    listexcept=serializers.SerializerMethodField()
    class Meta:
        model=Post
        fields=('id','viewer','fileupload','caption','posted','tags','listspecific',
        'listexcept','emotion',)
    def get_listspecific(self,obj):
        return [{'username':user.username,'avatar':user.profile.avatar.url,'id':user.id,'name':user.profile.name} for user in obj.accept_viewer.all().select_related('profile')]
    def get_listexcept(self,obj):
        return [{'username':user.username,'avatar':user.profile.avatar.url,'id':user.id,'name':user.profile.name} for user in obj.exception_viewer.all().select_related('profile')]
    def get_fileupload(self,obj):
        fileupload=Fileuploadpost.objects.filter(post=obj)
        return [{'id':file.id,'media':file.file.url,'media_preview':file.get_file_preview(),'duration':file.duration,'note':file.note,'tags':file.tags} for file in fileupload ]
    def get_tags(self,obj):
        return [{'username':tag.username,'name':tag.profile.name,'id':tag.id} for tag in obj.tags.all()]
    
class CommentSerializer(serializers.ModelSerializer):
    tags=serializers.SerializerMethodField()
    user=serializers.SerializerMethodField()
    count_reply=serializers.SerializerMethodField()
    express_emotions=serializers.SerializerMethodField()
    reported=serializers.SerializerMethodField()
    list_emoji=serializers.SerializerMethodField()
    fileupload=serializers.SerializerMethodField()
    class Meta:
        model=Comment
        fields=('id','tags','fileupload','date','express_emotions','user','text_preview','body','count_express_emotions','count_reply','parent','list_emoji','reported')
    def get_user(self,obj):
        return {'avatar':obj.user.profile.avatar.url,'id':obj.user_id,'name':obj.user.profile.name}
    def get_tags(self,obj):
        return [{'name':tag.profile.name,'id':tag.id} for tag in obj.tags.all()]
    def count_express_emotions(self,obj):
        return obj.count_express_emotions()
    def get_fileupload(self,obj):
        if obj.uploadfile:
            return({'id':obj.uploadfile_id,'file':obj.uploadfile.file.url,'file_preview':obj.uploadfile.get_file_preview(),'duration':obj.uploadfile.duration})
    def count_reply(self,obj):
        return obj.count_reply()
    def get_list_emoji(self,obj):
        request=self.context.get("request") 
        express_emotions=Comment_emotions.objects.filter(comment=obj).order_by()
        return express_emotions.values('emotion').distinct()
    
    def get_express_emotions(self,obj):
        request=self.context.get("request") 
        user=request.user
        express_emotions=Comment_emotions.objects.filter(user=user,comment=obj)
        if express_emotions.exists():
            return express_emotions.first().emotion
    
    def get_reported(self,obj):
        request=self.context.get("request") 
        reported=False
        user=request.user
        if Reportcomment.objects.filter(comment=obj,user=user).exists():
            reported=True
        return reported

class SavedSerializer(serializers.ModelSerializer):
    class Meta:
        model=Saved
        fields=('id','folder','viewer',)
    