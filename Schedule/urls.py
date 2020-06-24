from django.urls import path
from Schedule.views import index

urlpatterns = [
    path('', index)
]
