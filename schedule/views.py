import pytz
from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login as dj_login, logout as dj_logout

from django.contrib.auth.models import User

from schedule import models
from schedule.utilities import to_local_time
from schedule.decorators import login_required, collaboration_required

def get_participant(id_num):
    try: return models.Participant.objects.get(id_num=id_num)
    except ObjectDoesNotExist: return None

def fatal_error(request, exception=None):
    return render(request, "FatalError.html", {})

def index(request):
    return render(request, "Index.html", {})

def ask_registration(request):
    return render(request, "Register.html", {})

def privacy_policy(request):
   return render(request, "PrivacyPolicy.html", {})

def register(request):
    id_num = str(request.POST["id_num"])
    participant = get_participant(id_num)

    if participant: return render(request, "AlreadyRegistered.html", {"participant": participant})

    name, age = request.POST["name"], request.POST["age"]
    address, phone = request.POST["address"], str(request.POST["phone"])
    participant = models.Participant(id_num=id_num, name=name, age=age, address=address, phone=phone)
    participant.save()

    return redirect('/select_city?participant=%d' % participant.pk)

def login(request):
    participant = get_participant(request.POST["id_num"])
    if not participant: return redirect("/not_participant?id_num=" + request.POST["id_num"])
    return redirect("/select_city?participant=%d" % participant.pk )

def not_participant(request):
    return render(request, "NotParticipant.html", {"id_num": request.GET["id_num"]})

def select_city(request):
    participant = models.Participant.objects.get(pk=request.GET["participant"])
    return render(request, "SelectCity.html", {"cities": models.City.objects.all(), "participant": participant})

def select_temple(request):
    city = models.City.objects.get(pk=request.GET["city"])
    participant = models.Participant.objects.get(pk=request.GET["participant"])
    return render(request, "SelectTemple.html", {"participant": participant, "city": city, "temples": models.Temple.objects.filter(city=city)})

def select_mass(request):
    city = models.City.objects.get(pk=request.GET["city"])
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    participant = models.Participant.objects.get(pk=request.GET["participant"])
    masses = temple.mass_set.filter(schedule__gte = to_local_time( datetime.now() ) )
    return render(request, "SelectMass.html", {"participant": participant, "city": city, "temple": temple, "masses": masses})

def confirm_reservation(request):
    city = models.City.objects.get(pk=request.GET["city"])
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    mass = models.Mass.objects.get(pk=request.GET["mass"])
    if mass.get_space_available() == 0: return redirect('/full_mass?city=%d&temple=%d&mass=%d' % (city.pk, temple.pk, mass.pk))
    participant = models.Participant.objects.get(pk=request.GET["participant"])
    return render(request, "ConfirmReservation.html", {"participant": participant, "city": city, "temple": temple, "mass": mass})

def perform_reservation(request):
    city_pk = int(request.POST["city"])
    temple_pk = int(request.POST["temple"])
    mass = models.Mass.objects.get(pk=request.POST["mass"])
    if mass.get_space_available() == 0: return redirect('/full_mass?city=%d&temple=%d&mass=%d' % (city_pk, temple_pk, mass.pk))

    participant = models.Participant.objects.get(pk=request.POST["participant"])
    _, created = models.Reservation.objects.get_or_create(mass=mass, participant=participant)

    if created: return redirect('/confirmation?participant=%d&city=%s&temple=%d&mass=%d' % (participant.pk, city_pk, temple_pk, mass.pk))
    return redirect('/already_inscribed?participant=%d&city=%s&temple=%d&mass=%d' % (participant.pk, city_pk, temple_pk, mass.pk))

def confirmation(request):
    city = models.City.objects.get(pk=request.GET["city"])
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    mass = models.Mass.objects.get(pk=request.GET["mass"])
    participant = models.Participant.objects.get(pk=request.GET["participant"])
    return render(request, "Confirmation.html", {"participant": participant, "city": city, "temple": temple, "mass": mass})

def already_inscribed(request):
    city = models.City.objects.get(pk=request.GET["city"])
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    mass = models.Mass.objects.get(pk=request.GET["mass"])
    participant = models.Participant.objects.get(pk=request.GET["participant"])
    return render(request, "AlreadyInscribed.html", {"participant": participant, "city": city, "temple": temple, "mass": mass})

def full_mass(request):
    city = models.City.objects.get(pk=request.GET["city"])
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    mass = models.Mass.objects.get(pk=request.GET["mass"])
    return render(request, "FullMass.html", {"city": city, "temple": temple, "mass": mass})

def ask_admin_login(request):
    if request.user.is_authenticated: return redirect("/temple?temple=" + request.GET["temple"])
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    return render(request, "AdminLogin.html", {"temple": temple})

def admin_login(request):
    user = authenticate(username=request.POST["user"], password=request.POST["pass"])
    if not user: return redirect('/')
    dj_login(request, user)
    return redirect("/temple?temple=" + request.POST["temple"] )

@login_required
def logout(request):
    dj_logout(request)
    return redirect("/")

@login_required
@collaboration_required
def temple(request):
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    masses = temple.mass_set.filter(schedule__gte = to_local_time( datetime.now() ) )
    return render(request, "Temple.html", {"temple": temple, "masses": masses})

@login_required
@collaboration_required
def ask_create_mass(request):
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    return render(request, "CreateMass.html", {"temple": temple})

@login_required
@collaboration_required
def create_mass(request):
    temple_pk, schedule, max_participants = request.POST["temple"], request.POST["schedule"], request.POST["max_participants"]
    temple = models.Temple.objects.get(pk=temple_pk)
    schedule = to_local_time( datetime.strptime(schedule, "%Y-%m-%dT%H:%M") )
    models.Mass(temple=temple, schedule=schedule, max_participants=max_participants).save()
    return redirect("/temple?temple=" + temple_pk)

@login_required
@collaboration_required
def mass_history(request):
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    masses = temple.mass_set.all()
    return render(request, "MassHistory.html", {"temple": temple, "masses": masses})

@login_required
@collaboration_required
def ask_search_participant(request):
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    return render(request, "SearchParticipant.html", {"temple": temple})

@login_required
@collaboration_required
def search_participant(request):
    id_num = request.POST["id_num"]
    name = request.POST["name"]
    temple = models.Temple.objects.get(pk=request.POST["temple"])
    participants = models.Participant.objects.filter(pk__in=temple.get_participants())
    return render(request, "SearchResults.html", {"temple": temple, "participants": participants} )

@login_required
@collaboration_required
def consult_mass(request):
    mass = models.Mass.objects.get(pk=request.GET["mass"])
    reservations = mass.reservation_set.all()
    return render(request, "ConsultMass.html", {"temple": mass.temple, "mass": mass, "reservations": reservations})

@login_required
@collaboration_required
def consult_participant(request):
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    participant = models.Participant.objects.get(pk=request.GET["participant"])
    if participant.pk not in temple.get_participants(): logout(request)
    reservations = participant.get_temple_reservations(temple)
    return render(request, "ConsultParticipant.html", {"temple": temple, "participant": participant, "reservations": reservations})

@login_required
@collaboration_required
def modify_participant(request):
    temple = models.Temple.objects.get(pk=request.POST["temple"])
    participant = models.Participant.objects.get(pk=request.POST["participant"])
    if participant.pk not in temple.get_participants(): logout(request)
    participant.name = request.POST["name"]
    participant.age = request.POST["age"]
    participant.address = request.POST["address"]
    participant.phone = request.POST["phone"]
    participant.save()
    return redirect('/consult_participant?temple=%d&participant=%d' % (temple.pk, participant.pk) )

@login_required
@collaboration_required
def ask_delete_participant(request):
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    participant = models.Participant.objects.get(pk=request.GET["participant"])
    if participant.pk not in temple.get_participants(): logout(request)
    return render(request, "DeleteParticipant.html", {"temple": temple, "participant": participant})

@login_required
@collaboration_required
def delete_participant(request):
    temple = models.Temple.objects.get(pk=request.POST["temple"])
    participant = models.Participant.objects.get(pk=request.POST["participant"])
    if participant.pk not in temple.get_participants(): logout(request)
    participant.delete()
    return redirect('/temple?temple=%d' % temple.pk )

@login_required
@collaboration_required
def ask_confirm_mass(request):
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    mass = models.Mass.objects.get(pk=request.GET["mass"])
    reservations = mass.reservation_set.all()
    return render(request, "ConfirmMass.html", {"temple": temple, "mass": mass, "reservations": reservations})

@login_required
@collaboration_required
def filter_participants(request):
    temple = models.Temple.objects.get(pk=request.POST["temple"])
    mass = models.Mass.objects.get(pk=request.POST["mass"])
    reservations = mass.reservation_set.filter(participant__id_num__startswith=request.POST["id_num"])
    return render(request, "ConfirmMass.html", {"temple": temple, "mass": mass, "reservations": reservations})

@login_required
@collaboration_required
def confirm_mass(request):
    mass = models.Mass.objects.get(pk=request.POST["mass"])
    for reservation in models.Reservation.objects.filter(mass=mass):
        if str(reservation.participant.id_num) in request.POST: reservation.confirmed = True
        else: reservation.confirmed = False
        reservation.save()
    return redirect("/temple?temple=" + request.POST["temple"])

@login_required
@collaboration_required
def ask_remove_mass(request):
    temple = models.Temple.objects.get(pk=request.GET["temple"])
    mass = models.Mass.objects.get(pk=request.GET["mass"])
    return render(request, "RemoveMass.html", {"temple": temple, "mass": mass})

@login_required
@collaboration_required
def remove_mass(request):
    temple = models.Temple.objects.get(pk=request.POST["temple"])
    mass = models.Mass.objects.get(pk=request.POST["mass"]).delete()
    return redirect("/temple?temple=%d" % temple.pk)
