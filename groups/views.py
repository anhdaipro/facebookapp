from django.shortcuts import render
from django.core.paginator import Paginator
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
from .serializers import GroupSerializer
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
# Create your views here.
class Creategroup(APIView):
    def post(self,request):
        group_name=request.data.get('group_name')
        private=request.data.get('private')
        members=request.data.get('members',[])

        group=Group.objects.create(group_name=group_name,private=private,admin=request.user)
        group.members.add(*members)
        return Response({'id':group.id}) 

class DetailgroupAPI(APIView):
    def get(self,request,id):
        group=Group.objects.get(id=id)
        serializer= GroupSerializer(group,context={"request": request})
        return Response(serializer.data)
    def post(self,request,id):
        group=Group.objects.get(id=id)
        image_cover=request.FILES.get('file')
        description=request.data.get('description')
        group_name=request.data.get('group_name')
        private=request.data.get('private')
        members=request.data.get('members',[])
        if image_cover:
            group.image_cover=image_cover
        if description:
            group.description=description
        group.group_name=group_name
        group.private=private
        group.save()
        group.members.add(*members)
        return Response({'success':True})