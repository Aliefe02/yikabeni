from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
    path('register',Register.as_view()),
    path('login',Login.as_view()),
    path('logout',Logout.as_view()),
    path('changepassword',ChangePassword.as_view()),
    path('changeaddress',ChangeAddress.as_view()),
    path('getshopdetails',GetShopDetails.as_view()),
    path('uploadphoto',UploadPhoto.as_view()),
    path('updatesettings',Settings.as_view()),
    path('uploadphoto',UploadPhoto.as_view()),
    path('deletephoto',DeletePhoto.as_view()),
    path('promoteshop',PromoteShop.as_view()),
    path('configureworkdays',ConfigureWorkdays.as_view()),
    path('getworkdays',GetWorkdays.as_view()),
    path('createprivatecompanypaymentaccount',CreatePrivateCompanyPaymentAccount.as_view()),
    path('updateprivatecompanypaymentaccount',UpdatePrivateCompanyPaymentAccount.as_view()),
    path('createlimitedorjointstockpaymentaccount',CreateLimitedOrJointStockPaymentAccount.as_view()),
    path('updatelimitedorjointstockpaymentaccount',UpdateLimitedOrJointStockPaymentAccount.as_view()),
    path('getshoppaymentdetails',GetShopPaymentDetails.as_view()),
    path('photos/<str:photo_id>/', get_photo, name='get_photo'),
]
