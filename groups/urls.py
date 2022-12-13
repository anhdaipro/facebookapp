from django.urls import path
from . import views
from django.conf.urls import include
from .views import (
    Creategroup,
    DetailgroupAPI
)

urlpatterns = [ 
    path( "groups/create", Creategroup.as_view()), 
    path( "groups/<int:id>", DetailgroupAPI.as_view()), 
]