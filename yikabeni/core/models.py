from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from kurumsal.models import *
from django.db import models

class User(AbstractUser):
    id = models.CharField(max_length=20,unique=True,primary_key=True)
    email = models.EmailField(unique=True)
    city = models.CharField(max_length=55,null=True)
    district = models.CharField(max_length=100,null=True)
    neighbourhood = models.CharField(max_length=100,null=True)
    zipCode = models.CharField(max_length=20)
    phone_number = models.IntegerField(null=True)
    username = models.CharField(max_length=100,null=True,unique=True)
    unread_notifications = models.IntegerField(default=0)
    last_login = models.DateTimeField(default=timezone.now)
    last_logout = models.DateTimeField(null=True)
    REQUIRED_FIELDS = []
 
class Car(models.Model):
    owner = models.ForeignKey(User,on_delete=models.CASCADE)
    plate_number = models.CharField(max_length=15,unique=True)
    vehicle_type = models.CharField(max_length=20,null=True)

class Tokens(models.Model):
    token = models.CharField(max_length=255)
    init_time = models.DateTimeField(default=timezone.now)

class Service_Receipt(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop,on_delete=models.CASCADE)
    car = models.ForeignKey(Car,on_delete=models.CASCADE)
    price = models.FloatField()
    time = models.DateTimeField(default=timezone.now)
    review = models.IntegerField(null=True)

class Notifications(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification = models.CharField(max_length=256)
    timestamp = models.DateTimeField(default=timezone.now)
    
class Review(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop,on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(null=True)
    timestamp = models.DateTimeField(default=timezone.now)

class Notification(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    text = models.TextField()
    sender = models.CharField(default='Yıkabeni')
    timestamp = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)

class Payment(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop,on_delete=models.CASCADE)
    car = models.ForeignKey(Car,on_delete=models.CASCADE)
    service = models.ForeignKey(Service,on_delete=models.CASCADE)
    service_name = models.CharField(max_length=100)
    price = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)
    ip = models.CharField(max_length=36)
    address = models.TextField()
    completed = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    cancel_reason = models.CharField(max_length=50,null=True)
    cancel_reason_description = models.TextField(null=True)
