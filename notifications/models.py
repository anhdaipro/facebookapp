from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Notification(models.Model):
	NOTIFICATION_TYPES = ((1,'Emotions'),(2,'Comment'), (3,'Follow'),(5,'Addfriend'),(7,'Accept friend request'), (4,'Mentions'),(6,'Post'))
	story=models.ForeignKey('post.Story', on_delete=models.CASCADE, related_name="noti_story", blank=True, null=True)
	post = models.ForeignKey('post.Post', on_delete=models.CASCADE, related_name="noti_post", blank=True, null=True)
	comment = models.ForeignKey('comment.Comment', on_delete=models.CASCADE, blank=True, null=True)
	filepost = models.ForeignKey('post.Fileuploadpost', on_delete=models.CASCADE, blank=True, null=True)
	group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='group_user', null=True)
	image_preview=models.FileField(upload_to='post/',null=True)
	accept=models.BooleanField(default=False)
	tag=models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
	message=models.ForeignKey('chat.Message', on_delete=models.CASCADE, blank=True, null=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="noti_to_user")
	receiver=models.ForeignKey(User,null=True,blank=True,related_name='receiver',on_delete=models.CASCADE)
	notification_type = models.IntegerField(choices=NOTIFICATION_TYPES)
	text_preview = models.TextField(max_length=90, blank=True)
	date = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering=['-date']

class Searchcurrent(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_serach")
	keyword=models.TextField(max_length=90,null=True)
	date = models.DateTimeField(auto_now_add=True)
	user_search=models.ForeignKey(User, on_delete=models.CASCADE, related_name="resut_seach",null=True)