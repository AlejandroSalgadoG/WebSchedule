from django.db import models
from django.contrib.auth.models import User

from schedule.utilities import as_local_time

class City(models.Model):
    name = models.CharField(max_length = 64)

class Temple(models.Model):
    name = models.CharField(max_length = 64)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

class Collaboration(models.Model):
    collaborator = models.ForeignKey(User, on_delete=models.CASCADE)
    temple = models.ForeignKey(Temple, on_delete=models.DO_NOTHING)

class Mass(models.Model):
    temple = models.ForeignKey(Temple, on_delete=models.CASCADE)
    schedule = models.DateTimeField()
    max_participants = models.IntegerField()

    def get_formatted_schedule(self):
        return as_local_time(self.schedule).strftime("%d/%m - %I:%M %p") 

    def get_space_reserved(self):
        return self.reservation_set.all().count()

    def get_space_available(self):
        return self.max_participants - self.get_space_reserved()

class Participant(models.Model):
    id_num = models.CharField(max_length=16)
    name = models.CharField(max_length = 128)
    age = models.IntegerField()
    address = models.CharField(max_length = 128)
    phone = models.CharField(max_length=16)

class Reservation(models.Model):
    mass = models.ForeignKey(Mass, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)
