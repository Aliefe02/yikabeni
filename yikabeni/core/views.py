from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from kurumsal.serializers import *
from django.utils import timezone
from ipware import get_client_ip
from yikabeni import settings
from kurumsal.models import *
from .serializers import *
from .models import *
import jwt, datetime
import threading
import iyzipay
import random
import string

API_KEYS = ['qR9eL2uT5pX7aBzW8vYcN1sM0oK3gF4hD6jVlIyZnGxEwQb']

decode_key = 'yikabeni'

iyzico_options = {
    'api_key': 'sandbox-vDBKmuFRdGcgPweVcqievHD8MpPcYgqI',
    'secret_key': 'sandbox-JiNIAFAB0QdzY6aoeM7g8Coqhi4hbaLR',
    'base_url': 'sandbox-api.iyzipay.com'
}


def UpdateRating(shop):
    shop_details = ShopDetails.objects.get(shop=shop)
    reviews = Review.objects.filter(shop=shop)
    review_count = len(reviews)
    n = 0
    for review in reviews:
        n += review.rating

    new_review = n/review_count
    shop_details.rating = new_review
    shop_details.save()

def SendEmailVerificationCode(receiver,code):
    subject = 'Yıkabeni - '+str(code)
    txt_ = 'Yıkabeni onaylama kodunuz: '+str(code)
    from_email = settings.DEFAULT_FROM_EMAIL
    receivers = []
    receivers.append(receiver)
    receivers = list(receivers)

    send_mail(
        subject=subject,
        message=txt_,
        from_email=from_email,
        recipient_list=receivers,
        fail_silently=False,
    )
    return code

class Register(APIView):
    def post(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        if User.objects.filter(email__exact=request.data['email']).first() is not None:
            response.status_code = 422
            response.data = {'status_code':422,'problem':'email','message':'email already taken'}
            return response
        try:
            while True:
                characters = string.ascii_lowercase + string.digits
                generated_id = ''.join(random.choice(characters) for _ in range(12))
                if not User.objects.filter(id=generated_id).exists():
                    break
            request.data['id'] = generated_id
            serializer = UserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            payload = {
            'id':serializer.data['id'],
            'exp':datetime.datetime.utcnow()+datetime.timedelta(days=30),
            'iat':datetime.datetime.utcnow()
            }
            token = jwt.encode(payload,decode_key,algorithm='HS256')
            new_token = Tokens.objects.create(token=token)
            new_token.save()
            response.set_cookie(key='jwt',value=token,httponly=True)
            response.status_code = 201
            response.data = {'status_code':201,'id':serializer.data['id'],'email':serializer.data['email'],'first_name':serializer.data['first_name'],'last_name':serializer.data['last_name']}

        except Exception as e:  
            response.status_code = 500
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
            print(str(e))
        return response

class Login(APIView):
    def post(self,request):
        response = Response()
        
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        email = request.data['email']
        password = request.data['password']
        user = User.objects.filter(email__exact=email).first()

        if user is None:
            response.status_code = 404
            response.data = {'status_code':404,'Problem':'User','Message':'Kullanıcı bulunamadı'}
            return response

        if not user.check_password(password):
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Password','Message':'Şifre yanlış'}
            return response
        user.last_login = timezone.now()
        user.save()
        payload = {
            'id':user.id,
            'exp':datetime.datetime.utcnow()+datetime.timedelta(days=30),
            'iat':datetime.datetime.utcnow()
            }
        token = jwt.encode(payload,decode_key,algorithm='HS256')
        new_token = Tokens.objects.create(token=token)
        new_token.save()
        response.status_code = 302
        serialized = UserSerializer(user)
        response.data = serialized.data
        response.data['status_code'] = 302
        response.set_cookie(key='jwt',value=token,httponly=True)
        return response

class Logout(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(id=payload['id'])
            user.last_logout = timezone.now()
            user.save()

            token = Tokens.objects.get(token=token)
            token.delete()
            response.data = {'status_code':200}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        return response

class ChangePassword(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(id=payload['id'])
            user.set_password(request.data['new_password'])
            user.save()
            response.status_code = 200
            response.data = {'status_code':200}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class UserDetails(APIView):
    def get(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response

        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.filter(id=payload['id']).first()
            if user is None:
                response.status_code = 404
                response.data = {'Problem':'User','Message':'User not found'}
                return response
            response.status_code = 200
            serialized_data = UserSerializer(user)
            response.data = serialized_data.data
            response.data['status_code'] = 200

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class ChangeAddress(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(id=payload['id'])
            user.city = request.data['city']
            user.district = request.data['district']
            user.neighbourhood = request.data['neighbourhood']
            user.save()
            response.status_code = 200
            response.data = {'status_code':200}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class EmailVerification(APIView):
    async def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        try:
            code = random.randint(10000,99999)
            email = request.data['email']
            thread = threading.Thread(target=SendEmailVerificationCode, args=(email,code))
            thread.start()
            response.status_code = 200
            response.data = {'Code':code,'status_code':200}
            return response
            
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class SearchShop(APIView):
    def get(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            city = request.query_params.get('city')
            district = request.query_params.get('district')
            neighbourhood = request.query_params.get('neighbourhood')
            search_results = ShopDetails.objects.filter(city=city,district=district,neighbourhood=neighbourhood,closed=False)
            serialized = ShopDetailsSerializer(search_results,many=True)
            response.status_code = 200
            data = {'status_code':200,'data':serialized.data}
            response.data = data

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class AddCar(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(id=payload['id'])
            car = Car.objects.create(owner=user,plate_number=request.data['plate_number'],vehicle_type=request.data['vehicle_type'])
            car.save()
            response.status_code = 201
            response.data = {'status_code':201}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response  

class RemoveCar(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            car = Car.objects.get(id=request.data['car_id'])
            car.delete()
            response.data = {'status_code':200}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class MakeReservation(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(id=payload['id'])
            shop = Shop.objects.get(id=request.data['shop_id'])
            car = Car.objects.get(plate_number=request.data['plate_number'])
            date = request.data['date']
            time = request.data['time']
            
            availablespot = NoAvailableSpot.objects.filter(shop=shop,date=date,time=time).first()
            if availablespot != None:
                response.data = {'empty_spot':False,'Message':'Boş yer yok'}
                response.status_code = 404
                return response
            
            reservation = Reservation.objects.create(user=user,shop=shop,car=car,date=date,time=time,price=request.data['price'],shop_name=shop.shop_name,shop_profile_photo=shop.profile_photo)
            reservation.save()

            availablespot = Reservation.objects.filter(shop=shop,date=date,time=time).count()
            if availablespot >= shop.number_of_spots:
                newUnavailableTime = NoAvailableSpot.objects.create(shop=shop,date=date,time=time)
                newUnavailableTime.save()

            response.status_code = 201
            response.data = {'status_code':201}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class CancelReservation(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(id=payload['id'])
            shop = Shop.objects.get(id=request.data['shop_id'])
            car = Car.objects.get(plate_number=request.data['plate_number'])
            date = request.data['date']
            time = request.data['time']
            
            reservation = Reservation.objects.get(user=user,shop=shop,car=car,date=date,time=time,price=request.data['price'],shop_name=shop.shop_name,shop_profile_photo=shop.profile_photo)
            reservation.delete()

            availablespot = NoAvailableSpot.objects.get(shop=shop,date=date,time=time)
            if availablespot != None:
                availablespot.delete()

            response.status_code = 204
            response.data = {'status_code':201}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response    

class GetUnavailableTimes(APIView):
    def get(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop_id = request.query_params.get('shop_id')
            date = request.query_params.get('date')
            shop = Shop.objects.get(id=shop_id)
            unavailableTimes = NoAvailableSpot.objects.filter(shop=shop,date=date)
            times = NoAvailableSpotSerializer(unavailableTimes,many=True)
            response.data = times.data
            response.status_code = 200
            response.data['status_code'] = 200

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class GetReservations(APIView):
    def get(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(id=payload['id'])
            reservations = Reservation.objects.filter(user=user).order_by('time')
            serialized = ReservationSerializer(reservations,many=True)
            response.status_code = 200
            data = {'status_code':200,'data':serialized.data}
            response.data = data

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class GetUserCars(APIView):
    def get(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(id=payload['id'])
            cars = Car.objects.filter(user=user)
            serialized = CarSerializer(cars,many=True)
            response.status_code = 200
            response.data = serialized.data
            response.data['status_code'] = 200

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class GetShopPhotos(APIView):
    def get(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop_id = request.query_params.get('shop_id')
            shop = Shop.objects.get(id=shop_id)
            photos = Photo.objects.filter(shop=shop)
            serialized = PhotoSerializer(photos,many=True)
            response.status_code = 200
            response.data = serialized.data
            response.data['status_code'] = 200

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response
    
class GetShopInfo(APIView):
    def get(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            data = {}
            shop_id = request.query_params.get('shop_id')
            shop = Shop.objects.filter(id=shop_id).first()
            photos = Photo.objects.filter(shop=shop)
            
            shop_details = ShopDetailsSerializer(shop)
            data['shop_details'] = shop_details.data

            serialized_photos = PhotoSerializer(photos,many=True)
            data['photos'] = serialized_photos.data

            services = ShopServices.objects.get(shop=shop)
            shop_services = ShopServicesSerializer(services)
            data['shop_services'] = shop_services.data

            response.status_code = 200
            response.data = data
            response.data['status_code'] = 200

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class GetPromotedShops(APIView):
    def get(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(payload['id'])
            promoted_shops = PromotedShops.objects.filter(city=user.city,district=user.district,neighbourhood=user.neighbourhood)
            
            shops = []
            for i in promoted_shops:
                j = ShopDetails.objects.get(id=i.shop)
                if j.closed == False:
                    shops.append()

            serialized_shops = ShopDetailsSerializer(shops,many=True)
            response.status_code = 200
            response.data = serialized_shops.data
            response.data['status_code'] = 200

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response
     
class MakeReview(APIView):
    async def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(id=payload['id'])
            shop = Shop.objects.get(id=request.data['shop_id'])
            new_review = Review.objects.create(user=user,shop=shop,rating=request.data['rating'],comment=request.data['comment'])
            new_review.save()
            thread = threading.Thread(target=UpdateRating, args=(shop))
            thread.start()
            response.status_code = 201
            response.data = {'status_code':201}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class GetLastTenReviews(APIView):
    def get(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop_id = request.data['shop_id']
            shop = Shop.objects.get(id=shop_id)
            reviews = Review.objects.filter(shop=shop).order_by('timestamp')[:10]
            serialized = ReviewSerializer(reviews,many=True)
            response.status_code = 200
            response.data = serialized.data
            response.data['status_code'] = 200

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response
    
class GetLastTenNotification(APIView):
    def get(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(id=payload['id'])
            notifications = Notification.objects.filter(user=user).order_by('timestamp')[:10]
            serialized = NotificationSerializer(notifications,many=True)
            response.status_code = 200
            response.data = serialized.data
            response.data['status_code'] = 200

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response
    
class GetAllNotifications(APIView):
    def get(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(id=payload['id'])
            notifications = Notification.objects.filter(user=user).order_by('timestamp')
            serialized = NotificationSerializer(notifications,many=True)
            response.status_code = 200
            response.data = serialized.data
            response.data['status_code'] = 200

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response
    
class MakePayment(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            user = User.objects.get(id=payload['id'])
            shop = Shop.objects.get(id=request.data['shop_id'])
            car = Car.objects.get(plate=request.date['plate'])
            price = request.data['price']
            client_ip, is_routable = get_client_ip(request)
            address = request.data['address']
            service_name = request.data['service']
            service = Service.objects.get(id=request.data['service_id'])
            new_payment = Payment.objects.create(user=user,shop=shop,car=car,price=price,ip=client_ip,address=address,service=service)
            new_payment.save()

            payment_card = {
                'cardHolderName': request.data['card_owner'],
                'cardNumber': request.data['cardNumber'],
                'expireMonth': request.data['expireMonth'],
                'expireYear': request.data['expireYear'],
                'cvc': request.data['cvc'],
                'registerCard': request.data['registerCard']
            }

            buyer = {
                'id': user.id,
                'name': user.first_name,
                'surname': user.last_name,
                'gsmNumber': user.phone_number,
                'email': user.email,
                'identityNumber': '74300864791',
                'lastLoginDate': user.last_login,
                'registrationDate': user.date_joined,
                'registrationAddress': 'Nidakule Göztepe, Merdivenköy Mah. Bora Sok. No:1',
                'ip': client_ip,
                'city': user.city,
                'country': 'Turkey',
                'zipCode': user.zipCode
            }

            address = {
                'contactName': user.first_name + ' ' + user.last_name ,
                'city': user.city,
                'country': 'Turkey',
                'address': address,
                'zipCode': user.zipCode
            }

            basket_items = [
                {
                    'id': new_payment.id,
                    'name': service_name,
                    'category1': 'Oto Yıkama',
                    'itemType': 'VIRTUAL',
                    'price': price
                }
            ]

            request = {
                'locale': 'en',
                'conversationId': '123456789',
                'price': price,
                'paidPrice': price,
                'currency': 'TRY',
                'installment': '1',
                'basketId': new_payment.id,
                'paymentChannel': 'WEB',
                'paymentGroup': 'PRODUCT',
                'paymentCard': payment_card,
                'buyer': buyer,
                'billingAddress': address,
                'basketItems': basket_items
            }

            payment = iyzipay.Payment().create(request, iyzico_options)
            str_data = payment.read().decode('utf-8')
            data_dict = dict(eval(str_data))
            if data_dict['status'] == 'success':
                response.status_code = 201
                response.data = {'status_code':201}
            else:
                response.status_code = 500
                response.data = {'status_code':500,'Message':data_dict['errorMessage']}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response
    
class CancelPayment(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = { 'status_code': 401,'problem':'authentication','message':'not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code': 401,'problem':'token','message':'token not valid'}
            return response
        
        try:
            jwt.decode(token,decode_key,algorithms=['HS256'])
            client_ip, is_routable = get_client_ip(request)

            reason = request.data['reason']
            cancel_reason_description = request.data['cancel_reason_description']
            paymentID = request.data['paymentID']

            request = {
                'locale': 'tr',
                'conversationId': '123456789',
                'paymentId': paymentID,
                'ip': client_ip,
                'reason': reason,
                'description': cancel_reason_description
            }

            cancel = iyzipay.Cancel().create(request, iyzico_options)
            str_data = cancel.read().decode('utf-8')
            data_dict = dict(eval(str_data))
            if data_dict['status'] == 'success':
                payment = Payment.objects.get(id=paymentID)
                payment.cancelled = True
                payment.cancel_reason = reason
                payment.cancel_reason_description = cancel_reason_description
                payment.save()
                response.status_code = 201
                response.data = {'status_code':201}
            else:
                response.status_code = 500
                response.data = {'status_code':500,'Message':data_dict['errorMessage']}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
        except Exception as e:
            response.status_code = 500
            print(str(e))
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response