from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import logout

from schedule.models import Collaboration

def login_required(method):
    def enforce_login_decorator(self, request):
        if not request.user.is_authenticated:
            return redirect("/")
        return method(self, request)
    return enforce_login_decorator

def collaboration_required(method):
    def enforce_colaboration_decorator(self, request):
        try:
            if request.method == "GET": Collaboration.objects.get(temple=request.GET["temple"], collaborator=request.user)
            if request.method == "POST": Collaboration.objects.get(temple=request.POST["temple"], collaborator=request.user)
        except ObjectDoesNotExist:
            logout(request)
            return redirect("/")
        return method(self, request)
    return enforce_colaboration_decorator
