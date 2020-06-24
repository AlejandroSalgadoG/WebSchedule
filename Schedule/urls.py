from django.urls import path
from Schedule.views import Index

urlpatterns = [
    path('', Index.as_view())
]
