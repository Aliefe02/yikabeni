from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
from django.db import models
import hashlib
# import pytz
# import uuid

class Shop(models.Model):
    id = models.CharField(max_length=20,unique=True,primary_key=True)
    owner_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=64)
    shop_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=12,null=True)
    last_login = models.DateTimeField(default=timezone.now)
    last_logout = models.DateTimeField(null=True)
    profile_photo = models.ImageField(upload_to='photos/',null=True)
    number_of_spots = models.IntegerField(default=1)
    identitiyNumber = models.CharField(max_length=15)
    iban = models.CharField(max_length=55,null=True)
    address = models.CharField(max_length=255)
    subMerchantType = models.CharField(max_length=36,null=True)
    taxOffice = models.CharField(max_length=36,null=True)
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        # self.password = hashlib.sha256(self.password.encode()).hexdigest()
        super(Shop, self).save(*args, **kwargs)

    def set_password(self, raw_password):
        hashed_password = hashlib.sha256(raw_password.encode()).hexdigest()
        self.password = hashed_password

    def check_password(self, raw_password):
        hashed_password = hashlib.sha256(raw_password.encode()).hexdigest()
        return self.password == hashed_password

class ShopDetails(models.Model):
    shop = models.OneToOneField(Shop,on_delete=models.CASCADE)
    owner_name = models.CharField(max_length=150,null=True)
    shop_name = models.CharField(max_length=150)
    about = models.TextField(null=True)
    rating = models.FloatField(default=0)
    profile_photo = models.ImageField(upload_to='photos/',null=True)
    website = models.CharField(max_length=100,null=True)
    city = models.CharField(max_length=55,null=True)
    district = models.CharField(max_length=100,null=True)
    neighbourhood = models.CharField(max_length=100,null=True)
    phone_number = models.CharField(max_length=12,null=True)
    opening_hour = models.TimeField(null=True)
    closing_hour = models.TimeField(null=True)
    closed = models.BooleanField(default=False)
    number_of_spots = models.IntegerField(default=1)

class Workdays(models.Model):
    shop = models.OneToOneField(Shop,on_delete=models.CASCADE)
    rating = models.FloatField(null=True)
    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=True)
    sunday = models.BooleanField(default=True)

class ShopServices(models.Model):
    shop = models.OneToOneField(Shop,on_delete=models.CASCADE,unique=True)
    detailing = models.BooleanField(default=False)
    detailing_price = models.FloatField()
    waterless = models.BooleanField(default=False)
    waterless_price = models.FloatField()
    pressurized = models.BooleanField(default=False)
    pressurized_price = models.FloatField()
    steam = models.BooleanField(default=False)
    steam_price =models.FloatField()

class Service(models.Model):
    name = models.CharField(max_length=36)
    shop = models.ForeignKey(Shop,on_delete=models.CASCADE)
    description = models.TextField(null=True)
    price = models.FloatField

class Photo(models.Model):
    photo = models.ImageField(upload_to='photos/')
    shop = models.ForeignKey(Shop,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)

class Reservation(models.Model):
    user = models.ForeignKey('core.User',on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop,on_delete=models.CASCADE)
    car = models.ForeignKey('core.Car',on_delete=models.CASCADE)
    plate = models.CharField(max_length=15)
    shop_name = models.CharField(max_length=150,null=True)
    shop_profile_photo = models.CharField(max_length=150,null=True)
    date = models.DateField()
    time = models.CharField(max_length=5)
    price = models.FloatField()
    status = models.CharField(max_length=30)
    completed = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    #Add options

class NoAvailableSpot(models.Model):
    shop = models.ForeignKey(Shop,on_delete=models.CASCADE)
    date = models.DateField()
    time = models.CharField(max_length=5)

#Add more price options
class Price(models.Model):
    shop = models.ForeignKey(Shop,on_delete=models.CASCADE)
    price = models.FloatField()

class PromotedShops(models.Model):
    shop = models.ForeignKey(Shop,on_delete=models.CASCADE)
    city = models.CharField(max_length=55)
    district = models.CharField(max_length=100,null=True)
    neighbourhood = models.CharField(max_length=100,null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(default=timezone.now() + timedelta(days=7))