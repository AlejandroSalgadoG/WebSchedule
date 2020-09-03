from django.urls import path
from schedule import views

urlpatterns = [
    path('', views.Index.as_view()),
    path('login', views.Login.as_view()),
    path('logout', views.Logout.as_view()),
    path('select_temple', views.SelectTemple.as_view()),
    path('temple', views.Temple.as_view()),
    path('create_mass', views.CreateMass.as_view()),
    path('mass_history', views.MassHistory.as_view()),
    path('search_participant', views.SearchParticipant.as_view()),
    path('consult_mass', views.ConsultMass.as_view()),
    path('consult_participant', views.ConsultParticipant.as_view()),
    path('confirm_mass', views.ConfirmMass.as_view()),
    path('remove_mass', views.RemoveMass.as_view()),
    path('select_mass', views.SelectMass.as_view()),
    path('register', views.Register.as_view()),
    path('already_inscribed', views.AlreadyInscribed.as_view()),
    path('confirmation', views.Confirmation.as_view()),
    path('full_mass', views.FullMass.as_view()),
]
