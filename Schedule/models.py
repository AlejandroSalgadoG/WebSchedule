from django.db import models
from django.contrib.auth.models import User

class Temple(models.Model):
    name = models.CharField(max_length = 64)

class Collaboration(models.Model):
    collaborator = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    temple = models.ForeignKey(Temple, on_delete=models.DO_NOTHING)

class Mass(models.Model):
    temple = models.ForeignKey(Temple, on_delete=models.CASCADE)
    schedule = models.DateTimeField()
    max_participants = models.IntegerField()

class Participant(models.Model):
    id_num = models.IntegerField()
    name = models.CharField(max_length = 128)
    age = models.IntegerField()
    address = models.CharField(max_length = 128)
    phone = models.IntegerField()

class Reservation(models.Model):
    mass = models.ForeignKey(Mass, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
