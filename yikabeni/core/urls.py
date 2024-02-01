from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('register',Register.as_view()),
    path('login',Login.as_view()),
    path('logout',Logout.as_view()),
    path('changepassword',ChangePassword.as_view()),
    path('userdetails/',UserDetails.as_view()),
    path('changeaddress',ChangeAddress.as_view()),
    path('sendverificationmail',EmailVerification.as_view()),
    path('addcar',AddCar.as_view()),
    path('removecar',RemoveCar.as_view()),
    path('searchshop/',SearchShop.as_view()),
    path('makereservation',MakeReservation.as_view()),
    path('cancelreservation',CancelReservation.as_view()),
    path('getunavailabletimes/',GetUnavailableTimes.as_view()),
    path('getreservations/',GetReservations.as_view()),
    path('getusercars/',GetUserCars.as_view()),
    path('getshopphotos/',GetShopPhotos.as_view()),
    path('getshopinfo/',GetShopInfo.as_view()),
    path('getpromotedshops/',GetPromotedShops.as_view()),
    path('makereview',MakeReview.as_view()),
]
