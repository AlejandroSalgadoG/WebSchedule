from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout

from Schedule import models
from django.contrib.auth.models import User

class Index(TemplateView):
    template = "Index.html"

    def get(self, request):
        return render(request, self.template, {"temples": models.Temple.objects.all()})

class Logout(TemplateView):
    def get(self, request):
        logout(request)
        return redirect("/")

class Login(TemplateView):
    template = "Login.html"

    def get(self, request):
        if request.user.is_authenticated: return redirect("/temple")
        return render(request, self.template, {"temple": request.GET["temple"]})

    def find_user(self, username):
        try:
            user = models.User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            return None

    def association_exists(self, temple, collaborator):
        try:
            models.Collaboration.objects.get(temple=temple, collaborator=collaborator)
            return True
        except models.Collaboration.DoesNotExist:
            return False

    def post(self, request):
        username, password = request.POST["user"], request.POST["pass"]
        temple = models.Temple.objects.get(pk=request.POST["temple"])
        user = self.find_user( username )
        if not self.association_exists(temple, user): return redirect("/")
        user = authenticate(username=username, password=password)
        if not user: return redirect('/')
        login(request, user)
        return redirect("/temple")
        
class Temple(TemplateView):
    template = "Temple.html"

    def get(self, request):
        if not request.user.is_authenticated: return HttpResponse("Error")

        temple = models.Collaboration.objects.get(collaborator=request.user).temple 
        masses = models.Mass.objects.all()
        return render(request, self.template, {"temple": temple, "masses": masses})

class CreateMass(TemplateView):
    template = "CreateMass.html"

    def get(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        return render(request, self.template, {"temple": temple})

    def post(self, request):
        temple_id, schedule, max_participants = request.POST["temple"], request.POST["schedule"], request.POST["max_participants"]
        temple = models.Temple.objects.get(pk=temple_id)
        schedule = datetime.strptime(schedule, "%Y-%m-%dT%H:%M")
        models.Mass(temple=temple, schedule=schedule, max_participants=max_participants).save()
        return redirect("/temple")

class ConsultMass(TemplateView):
    template = "ConsultMass.html"

    def get(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        mass = models.Mass.objects.get(pk=request.GET["mass"])
        reservations = mass.reservation_set.all()
        return render(request, self.template, {"temple": temple, "mass": mass, "reservations": reservations})

class SelectMass(TemplateView):
    template = "SelectMass.html"

    def get(self, request):
        temples = models.Temple.objects.all()
        temple = temples.get(pk=request.GET["temple"])
        masses = temple.mass_set.all()
        return render(request, self.template, {"temple": temple, "temples": temples, "masses": masses})

class Register(TemplateView):
    template_ok = "Register.html"

    def get(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        mass = models.Mass.objects.get(pk=request.GET["mass"])
        if mass.get_space_available() == 0: return redirect('/full_mass?temple=%d&mass=%d' % (temple.pk, mass.pk))
        return render(request, self.template_ok, {"temple": temple, "mass": mass})

    def post(self, request):
        temple_pk = int(request.POST["temple"])
        mass = models.Mass.objects.get(pk=request.POST["mass"])
        if mass.get_space_available() == 0: return redirect('/full_mass?temple=%d&mass=%d' % (temple_pk, mass.pk))

        id_num, name, age = request.POST["id_num"], request.POST["name"], request.POST["age"]
        address, phone = request.POST["address"], request.POST["phone"]
        participant, _ = models.Participant.objects.get_or_create(id_num=id_num, name=name, age=age, address=address, phone=phone)
        models.Reservation(mass=mass, participant=participant).save()
        return redirect('/confirmation?temple=%d&mass=%d&participant=%d' % (temple_pk, mass.pk, participant.pk))

class FullMass(TemplateView):
    template = "FullMass.html"

    def get(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        mass = models.Mass.objects.get(pk=request.GET["mass"])

        return render(request, self.template, {"temple": temple, "mass": mass})

class Confirmation(TemplateView):
    template = "Confirmation.html"

    def get(self, request):
        temple = models.Temple.objects.get(pk=request.GET["temple"])
        mass = models.Mass.objects.get(pk=request.GET["mass"])
        participant = models.Participant.objects.get(pk=request.GET["participant"])
        return render(request, self.template, {"temple": temple, "mass": mass, "participant": participant})
