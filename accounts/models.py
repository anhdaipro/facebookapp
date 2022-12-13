from django.db import models
from django.contrib.auth.models import User
from post.models import *
from django.db.models.signals import post_save
from django.conf import settings
from django.core.cache import cache 
import datetime
viewer_choice=(
    ('1','Public'),
    ('2','Friend'),
    ('3','Excepttion people'),
    ('4','Specific friends'),
    ('5','Private'),
)
place_choice=(
	('1','Hometown'),
	('2','Current city'),
	('3','City')
)

GENDER_CHOICE=(
        ('1','MALE'),
        ('2','FEMALE'),
        ('3','ORTHER')
    )

class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	name=models.CharField(max_length=100,null=True)
	story=models.TextField(max_length=100, null=True, blank=True)
	language=models.TextField(null=True, blank=True)
	hobby=models.TextField(null=True, blank=True)
	created = models.DateField(auto_now_add=True)
	online=models.BooleanField(default=False)
	phone=models.CharField(max_length=100,null=True)
	is_online=models.DateTimeField(auto_now=True,null=True)
	coins=models.IntegerField(default=0)
	count_notify_unseen=models.IntegerField(default=0)
	date_of_birth=models.DateField(null=True)
	cover_image=models.ImageField(upload_to="profile/", null=True)
	hide_story_user=models.ManyToManyField(User,blank=True,related_name='hide_story_user')
	gender=models.CharField(max_length=10,choices=GENDER_CHOICE,null=True)	
	hide_post_user=models.ManyToManyField(User,blank=True,related_name='hide_post_user')
	avatar = models.ImageField(upload_to="profile/", null=True,default='profile/userno_gwinne.png')
	
	friend_invitation=models.ManyToManyField(User,blank=True,related_name='friend_invitation')
	followers=models.ManyToManyField(User,blank=True,related_name='followers')
	hide_suggested=models.ManyToManyField(User,blank=True,related_name='hide_suggested')
	likers=models.ManyToManyField(User,blank=True,related_name='likers')
	blocked_users=models.ManyToManyField(User,blank=True,related_name='blocked_users')
	def __str__(self):
		return self.user.username
	def count_friend(self):
    		return Friend.objects.filter(profile=self).count()
	def get_cover_image(self):
    		if self.cover_image:
    				return self.cover_image.url
class Friend(models.Model):
		user=models.ForeignKey(User, on_delete=models.CASCADE,related_name='friend_user')
		profile=models.ForeignKey(Profile, on_delete=models.CASCADE,related_name='profile_user')
		best_friend=models.BooleanField(default=False)
		acquaintance=models.BooleanField(default=False)
		restricted=models.BooleanField(default=False)
		unnamed_list=models.BooleanField(default=False)
		created = models.DateTimeField(auto_now_add=True)	
class Habitat(models.Model):
		name=models.CharField(max_length=100)
		profile=models.ForeignKey(Profile, on_delete=models.CASCADE)
		habitat_type=models.CharField(max_length=100,choices=place_choice)
		from_time=models.DateField(null=True)
		to_time=models.DateField(null=True)
		viewer=models.CharField(max_length=100,choices=viewer_choice,default="Public")
		exception_viewer=models.ManyToManyField(User, related_name='exception_viewer_habitat',blank=True)
class Relationship(models.Model):
		profile=models.ForeignKey(Profile, on_delete=models.CASCADE)
		status=models.CharField(max_length=100)
		viewer=models.CharField(max_length=100,choices=viewer_choice,default="Public")
		exception_viewer=models.ManyToManyField(User, related_name='exception_viewer_relationship',blank=True)
class University(models.Model):
	profile=models.ForeignKey(Profile, on_delete=models.CASCADE)
	name=models.TextField(max_length=200)
	description=models.TextField(max_length=1500, null=True)
	from_time=models.DateField(null=True)
	to_time=models.DateField(null=True)
	granduated=models.BooleanField(default=True)
	specialized=models.TextField(max_length=1500, null=True)
	degree=models.TextField(max_length=1500,null=True)
	description=models.TextField(max_length=1500, null=True)
	viewer=models.CharField(max_length=100,choices=viewer_choice,default="Public")
	exception_viewer=models.ManyToManyField(User, related_name='exception_viewer_university',blank=True)
class Highschool(models.Model):
		profile=models.ForeignKey(Profile, on_delete=models.CASCADE)
		name=models.TextField(max_length=200)
		from_time=models.DateField(null=True)
		to_time=models.DateField(null=True)
		granduated=models.BooleanField(default=True)
		description=models.TextField(max_length=1500, null=True)
		viewer=models.CharField(max_length=100,choices=viewer_choice,default="Public")
		exception_viewer=models.ManyToManyField(User, related_name='exception_viewer_highschool',blank=True)
class Workplace(models.Model):
		profile=models.ForeignKey(Profile, on_delete=models.CASCADE)
		company=models.TextField(max_length=200)
		position=models.TextField(max_length=200, null=True)
		description=models.TextField(max_length=1500, null=True)
		created = models.DateTimeField(auto_now_add=True)
		viewer=models.CharField(max_length=100,choices=viewer_choice,default="Public")
		exception_viewer=models.ManyToManyField(User, related_name='exception_viewer_workplace',blank=True)
class SMSVerification(models.Model):
		verified = models.BooleanField(default=False)
		code = models.CharField(max_length=6)
		phone = models.CharField(max_length=100)
		created = models.DateTimeField(auto_now_add=True)
class Verifyemail(models.Model):
    code=models.CharField(max_length=6)
    email=models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)	
def create_user_profile(sender, instance, created, **kwargs):
	if created:
    		
		profile=Profile.objects.create(user=instance)
		profile.name=instance.first_name+' '+instance.last_name
		profile.save()
def save_user_profile(sender, instance, **kwargs):
	instance.profile.save()

post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)
