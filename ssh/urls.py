from django.urls import path
from . import views


urlpatterns = [
    path('', views.index),
    path('upload_ssh_key', views.upload_ssh_key)
]