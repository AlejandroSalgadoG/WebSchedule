import pytz
from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.models import User

from schedule import models
from schedule.utilities import to_local_time
from schedule.decorators import login_required, collaboration_required

class Index(TemplateView):
    template = "Index.html"

    def get(self, request):
        return render(request, self.template, {})

class Register(TemplateView):
    template = "Register.html"
    error_template = "AlreadyRegistered.html"

    def get(self, request):
        return render(request, self.template, {})

    def search_participant(self, id_num):
        try: 
            return models.Participant.objects.get(id_num=id_num)
        except ObjectDoesNotExist:
            return None

    def post(self, request):
        id_num = request.POST["id_num"]
        participant = self.search_participant(id_num)

        if participant: return render(request, self.error_template, {"participant": participant})

        name, age = request.POST["name"], request.POST["age"]
        address, phone = request.POST["address"], request.POST["phone"]
        participant = models.Participant(id_num=id_num, name=name, age=age, address=address, phone=phone)
        participant.save()

        return redirect('/select_city?participant=%d' % participant.pk)

class Login(TemplateView):
    def post(self, request):
        try:
            participant = models.Participant.objects.get(id_num=request.POST["id_num"])
            return redirect("/select_city?participant=%d" % participant.pk )
        except ObjectDoesNotExist:
            return redirect("/not_participant?id_num=" + request.POST["id_num"])

class SelectCity(TemplateView):
    template = "SelectCity.html"

    def get(self, request):
        participant = models.Participant.objects.get(pk=request.GET["participant"])
        return render(request, self.template, {"cities": models.City.objects.all(), "participant": participant})

class NotParticipant(TemplateView):
    template = "NotParticipant.html"

    def get(self, request):
        return render(request, self.template, {"id_num": request.GET["id_num"]})

class SelectTemple(TemplateView):
    template = "SelectTemple.html"

    def get(self, request):
        city = models.City.objects.get(pk=request.GET["city"])
        participant = models.Participant.objects.get(pk=request.GET["participant"])
        return render(request, self.template, {"participant": participant, "city": city, "temples": models.Temple.objects.filter(city=city)})

class SelectMass(TemplateView):
    template = "SelectMass.html"

    def get(self, request):
        city = models.City.objects.get(pk=request.GET["city"])
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        participant = models.Participant.objects.get(pk=request.GET["participant"])
        masses = temple.mass_set.filter(schedule__gte = to_local_time( datetime.now() ) )
        return render(request, self.template, {"participant": participant, "city": city, "temple": temple, "masses": masses})

class ConfirmReservation(TemplateView):
    template = "ConfirmReservation.html"

    def get(self, request):
        city = models.City.objects.get(pk=request.GET["city"])
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        mass = models.Mass.objects.get(pk=request.GET["mass"])
        if mass.get_space_available() == 0: return redirect('/full_mass?city=%d&temple=%d&mass=%d' % (city.pk, temple.pk, mass.pk))
        participant = models.Participant.objects.get(pk=request.GET["participant"])
        return render(request, self.template, {"participant": participant, "city": city, "temple": temple, "mass": mass})

    def post(self, request):
        city_pk = int(request.POST["city"])
        temple_pk = int(request.POST["temple"])
        mass = models.Mass.objects.get(pk=request.POST["mass"])
        if mass.get_space_available() == 0: return redirect('/full_mass?city=%d&temple=%d&mass=%d' % (city_pk, temple_pk, mass.pk))

        participant = models.Participant.objects.get(pk=request.POST["participant"])
        _, created = models.Reservation.objects.get_or_create(mass=mass, participant=participant)

        if created: return redirect('/confirmation?participant=%d&city=%s&temple=%d&mass=%d' % (participant.pk, city_pk, temple_pk, mass.pk))
        return redirect('/already_inscribed?participant=%d&city=%s&temple=%d&mass=%d' % (participant.pk, city_pk, temple_pk, mass.pk))

class AlreadyInscribed(TemplateView):
    template = "AlreadyInscribed.html"

    def get(self, request):
        city = models.City.objects.get(pk=request.GET["city"])
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        mass = models.Mass.objects.get(pk=request.GET["mass"])
        participant = models.Participant.objects.get(pk=request.GET["participant"])
        return render(request, self.template, {"participant": participant, "city": city, "temple": temple, "mass": mass})

class FullMass(TemplateView):
    template = "FullMass.html"

    def get(self, request):
        city = models.City.objects.get(pk=request.GET["city"])
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        mass = models.Mass.objects.get(pk=request.GET["mass"])
        return render(request, self.template, {"city": city, "temple": temple, "mass": mass})

class Confirmation(TemplateView):
    template = "Confirmation.html"

    def get(self, request):
        city = models.City.objects.get(pk=request.GET["city"])
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        mass = models.Mass.objects.get(pk=request.GET["mass"])
        participant = models.Participant.objects.get(pk=request.GET["participant"])
        return render(request, self.template, {"participant": participant, "city": city, "temple": temple, "mass": mass})

class AdminLogin(TemplateView):
    template = "AdminLogin.html"

    def get(self, request):
        if request.user.is_authenticated: return redirect("/temple?temple=" + request.GET["temple"])
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        return render(request, self.template, {"temple": temple})

    def post(self, request):
        username, password = request.POST["user"], request.POST["pass"]
        user = authenticate(username=username, password=password)
        if not user: return redirect('/')
        login(request, user)
        return redirect("/temple?temple=" + request.POST["temple"] )

class Logout(TemplateView):
    @login_required
    def get(self, request):
        logout(request)
        return redirect("/")

class Temple(TemplateView):
    template = "Temple.html"

    @login_required
    @collaboration_required
    def get(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        masses = temple.mass_set.filter(schedule__gte = to_local_time( datetime.now() ) )
        return render(request, self.template, {"temple": temple, "masses": masses})

class CreateMass(TemplateView):
    template = "CreateMass.html"

    @login_required
    @collaboration_required
    def get(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        return render(request, self.template, {"temple": temple})

    @login_required
    @collaboration_required
    def post(self, request):
        temple_pk, schedule, max_participants = request.POST["temple"], request.POST["schedule"], request.POST["max_participants"]
        temple = models.Temple.objects.get(pk=temple_pk)
        schedule = to_local_time( datetime.strptime(schedule, "%Y-%m-%dT%H:%M") )
        models.Mass(temple=temple, schedule=schedule, max_participants=max_participants).save()
        return redirect("/temple?temple=" + temple_pk)

class MassHistory(TemplateView):
    template = "MassHistory.html"

    @login_required
    @collaboration_required
    def get(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        masses = temple.mass_set.all()
        return render(request, self.template, {"temple": temple, "masses": masses})

class SearchParticipant(TemplateView):
    search_template = "SearchParticipant.html"
    result_template = "SearchResults.html"

    @login_required
    @collaboration_required
    def get(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        return render(request, self.search_template, {"temple": temple})

    @login_required
    @collaboration_required
    def post(self, request):
        id_num = request.POST["id_num"]
        name = request.POST["name"]

        participants = []
        if id_num and name: participants = models.Participant.objects.filter(id_num__icontains=id_num, name__icontains=name)
        if id_num: participants = models.Participant.objects.filter(id_num__icontains=id_num)
        if name: participants = models.Participant.objects.filter(name__icontains=name)

        temple = models.Temple.objects.get(pk=request.POST["temple"])
        masses = temple.mass_set.all()
        temple_participants = [ participant for participant in participants if models.Reservation.objects.filter(participant=participant, mass__in=masses)]

        return render(request, self.result_template, {"temple": temple, "participants": temple_participants} )

class ConfirmMass(TemplateView):
    template = "ConfirmMass.html"

    @login_required
    @collaboration_required
    def get(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        mass = models.Mass.objects.get(pk=request.GET["mass"])
        reservations = mass.reservation_set.all()
        return render(request, self.template, {"temple": temple, "mass": mass, "reservations": reservations})

    @login_required
    @collaboration_required
    def post(self, request):
        mass = models.Mass.objects.get(pk=request.POST["mass"])
        for reservation in models.Reservation.objects.filter(mass=mass):
            if str(reservation.participant.id_num) in request.POST: reservation.confirmed = True
            else: reservation.confirmed = False
            reservation.save()
        return redirect("/temple")

class RemoveMass(TemplateView):
    template = "RemoveMass.html"

    @login_required
    @collaboration_required
    def get(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        mass = models.Mass.objects.get(pk=request.GET["mass"])
        return render(request, self.template, {"temple": temple, "mass": mass})

    @login_required
    @collaboration_required
    def post(self, request):
        temple = models.Temple.objects.get(pk=request.POST["temple"])
        mass = models.Mass.objects.get(pk=request.POST["mass"]).delete()
        return redirect("/temple?temple=%d" % temple.pk)

class ConsultMass(TemplateView):
    template = "ConsultMass.html"

    @login_required
    @collaboration_required
    def get(self, request):
        mass = models.Mass.objects.get(pk=request.GET["mass"])
        reservations = mass.reservation_set.all()
        return render(request, self.template, {"temple": mass.temple, "mass": mass, "reservations": reservations})

class ConsultParticipant(TemplateView):
    template = "ConsultParticipant.html"

    @login_required
    @collaboration_required
    def get(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        participant = models.Participant.objects.get(pk=request.GET["participant"])
        reservations = models.Reservation.objects.filter(participant=participant, mass__in=temple.mass_set.all())
        if reservations: return render(request, self.template, {"temple": temple, "participant": participant, "reservations": reservations})
        logout(request)
        return redirect("/")
        
class ModifyParticipant(TemplateView):
    template = "ModifyParticipant.html"

    @login_required
    @collaboration_required
    def post(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        participant = models.Participant.objects.get(pk=request.GET["participant"])
        reservations = models.Reservation.objects.filter(participant=participant, mass__in=temple.mass_set.all())
        if reservations: return render(request, self.template, {"temple": temple, "participant": participant, "reservations": reservations})
        logout(request)
        return redirect("/")

    def post(self, request):
        temple = models.Temple.objects.get(pk=request.POST["temple"])
        participant = models.Participant.objects.get(pk=request.POST["participant"])
        participant.name = request.POST["name"]
        participant.age = request.POST["age"]
        participant.address = request.POST["address"]
        participant.phone = request.POST["phone"]
        participant.save()
        return redirect('/consult_participant?temple=%d&participant=%d' % (temple.pk, participant.pk) )
