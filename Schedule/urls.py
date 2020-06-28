from django.urls import path
from Schedule import views

urlpatterns = [
    path('', views.Index.as_view()),
    path('login', views.Login.as_view()),
    path('logout', views.Logout.as_view()),
    path('temple', views.Temple.as_view()),
    path('create_mass', views.CreateMass.as_view()),
    path('consult_mass', views.ConsultMass.as_view()),
    path('select_mass', views.SelectMass.as_view()),
    path('register', views.Register.as_view()),
]
