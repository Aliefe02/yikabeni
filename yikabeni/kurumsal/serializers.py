from rest_framework import serializers
from .models import *


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'
        extra_kwargs={
            'password':{'write_only':True}
        }
        
    def create(self, validated_data):
        password = validated_data.pop('password',None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class ShopDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopDetails
        fields = '__all__'

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = '__all__'

class NoAvailableSpotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = '__all__'

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'

class ShopServicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopServices
        fields = '__all__'

class WorkdaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workdays
        fields = '__all__'