from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.text import slugify
from django.utils import timezone
from comment.models import *
import datetime
from accounts.models import *
# Create your models here.
viewer_choice=(
    ('1','Public'),
    ('2','Friend'),
    ('3','Excepttion people'),
    ('4','Private'),
    ('5','Specific friends'),
    ('6','Custom'),
    ('7','Best friend'),
    ('8','Unnamed list'),
    ('9','Acquaintance'),
)
commentchoice=(
    ('1','Public'),
    ('2','Friend'),
    ('3','Specific friends')
)
emotion_choice=(
    ('like','like'),
    ('love','love'),
    ('wow','wow'),
    ('sad','sad'),
    ('smile','smile'),
    ('indignant','indignant'),
)
class Fileupload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file= models.FileField(upload_to='post/')
    file_preview=models.ImageField(upload_to='post/',null=True)
    duration=models.FloatField(default=0.0)
    created = models.DateTimeField(auto_now_add=True)
    def get_file_preview(self):
        if self.file_preview and hasattr(self.file_preview,'url'):
            return self.file_preview.url

class Story(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fileupload=models.ForeignKey(Fileupload, on_delete=models.CASCADE,null=True,related_name='videos')
    link=models.URLField(blank=True)
    caption = models.TextField(max_length=1500,null=True)
    tags = models.ManyToManyField(User, related_name='tags_story',blank=True)
    viewer=models.CharField(max_length=100,choices=viewer_choice,default="Public")
    created = models.DateTimeField(auto_now_add=True)
    exception_viewer=models.ManyToManyField(User, related_name='exception_viewer_story',blank=True)
    class Meta:
        ordering=['-id']
    def count_express_emotions(self):
        return Story_emotions.objects.filter(story=self).count()
    def get_file(self):
        if self.fileupload:
            return self.fileupload.file.url
    def get_file_preview(self):
        if self.fileupload:
            return self.fileupload.file_preview()
    def get_duration(self):
        if self.fileupload:
            return self.fileupload.duration
class Post(models.Model):
    caption = models.TextField(max_length=1500)
    posted = models.DateTimeField(auto_now=True)
    emotion= models.CharField(max_length=100,null=True)
    tags = models.ManyToManyField(User, related_name='tags_post',blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group=models.ForeignKey(to="groups.Group", on_delete=models.CASCADE,related_name='post_group',null=True)
    commenters =models.ManyToManyField(User, related_name='accept_commenters',blank=True)
    comment=models.CharField(max_length=100,choices=viewer_choice,default="1")
    viewer=models.CharField(max_length=100,choices=viewer_choice,default="1")
    gim=models.BooleanField(default=False)
    hide_post=models.ManyToManyField(User,blank=True,related_name='hide_post')
    turn_off_notifications=models.ManyToManyField(User,blank=True,related_name='turn_off_notifications')
    turn_on_notifications=models.ManyToManyField(User,blank=True,related_name='turn_on_notifications')
    accept_viewer=models.ManyToManyField(User, related_name='accept_viewer_post',blank=True)
    exception_viewer=models.ManyToManyField(User, related_name='exception_viewer_post',blank=True)
    class Meta:
        ordering=['-posted']
    def __str__(self):
    	return self.user.username
    def count_express_emotions(self):
        return Post_emotions.objects.filter(post=self).count()
    def count_file(self):
        return Fileuploadpost.objects.filter(post=self).count()
    def count_comment(self):
        return Comment.objects.filter(post=self).count()
    def count_comment_parent(self):
        return Comment.objects.filter(post=self,parent=None).count()
    
    def count_share(self):
        return Sharepost.objects.filter(post=self).count()

class Fileuploadpost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post=models.ForeignKey(Post, on_delete=models.CASCADE,related_name='file_post')
    file= models.FileField(upload_to='post/')
    file_preview=models.ImageField(upload_to='post/',null=True)
    turn_off_file=models.ManyToManyField(User,blank=True,related_name='turn_off_file')
    turn_on_file=models.ManyToManyField(User,blank=True,related_name='turn_on_file')
    duration=models.FloatField(default=0)
    tags=models.TextField(null=True)
    note=models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    def get_file_preview(self):
        if self.file_preview and hasattr(self.file_preview,'url'):
            return self.file_preview.url
    def count_comment(self):
        return Comment.objects.filter(filepost=self).count()
    def count_express_emotions(self):
            return Filepost_emotions.objects.filter(filepost=self).count()
    def count_comment_parent(self):
        return Comment.objects.filter(filepost=self,parent=None).count()
    def get_count_file(self):
        count=0
        if self.post:
            count=Fileuploadpost.objects.filter(post=self.post).count()
        return count
class Story_emotions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    story=models.ForeignKey(Story, on_delete=models.CASCADE,related_name='story')
    list_emoji=models.TextField(max_length=1000,null=True,default="")  
    created = models.DateTimeField(auto_now=True)

class Post_emotions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post=models.ForeignKey(Post, on_delete=models.CASCADE,related_name='post')
    emotion=models.CharField(max_length=10,choices=emotion_choice)
    created = models.DateTimeField(auto_now=True)

    class Meta:
        ordering=['-created']
class Filepost_emotions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    filepost=models.ForeignKey(Fileuploadpost, on_delete=models.CASCADE,related_name='filepost')
    emotion=models.CharField(max_length=10,choices=emotion_choice)
    created = models.DateTimeField(auto_now=True)

    class Meta:
        ordering=['-created']
class Sharepost(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    post=models.ForeignKey(Post,on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
class Hideuser(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    hide_user=models.ManyToManyField(User, related_name='hide_user',blank=True)
    created = models.DateTimeField(auto_now_add=True)

class Reportpost(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    post=models.ForeignKey(Post,on_delete=models.CASCADE)
    reason=models.CharField(max_length=2000)
    created = models.DateTimeField(auto_now_add=True)
class Reportfilepost(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    filepost=models.ForeignKey(Fileuploadpost,on_delete=models.CASCADE)
    reason=models.CharField(max_length=2000)
    created = models.DateTimeField(auto_now_add=True)
class Reportstory(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    story=models.ForeignKey(Story,on_delete=models.CASCADE)
    reason=models.CharField(max_length=2000)
    created = models.DateTimeField(auto_now_add=True)

class Saved(models.Model):
    folder=models.CharField(null=True,max_length=50)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    viewer=models.CharField(max_length=100,choices=viewer_choice,default="4")
    accept_viewer=models.ManyToManyField(User, related_name='accept_viewer_save',blank=True)
    posts=models.ManyToManyField(Post,blank=True,related_name='post_save')
    created = models.DateTimeField(auto_now_add=True)

