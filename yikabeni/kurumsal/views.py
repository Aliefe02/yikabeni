from rest_framework.views import APIView
from .serializers import *
from rest_framework.response import Response
from .models import *
from core.models import *
import jwt, datetime
from django.utils import timezone
from datetime import timedelta
from core.models import Tokens
from django.http import HttpResponse
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


def get_photo(request, photo_id):
    try:
        photo = Photo.objects.get(photo='photos/'+photo_id)
        with open(photo.photo.path, 'rb') as photo_file:
            response = HttpResponse(photo_file.read(), content_type='image/jpeg')
            return response
    except Photo.DoesNotExist:
        return HttpResponse(status=404)
    

class Register(APIView):
    def post(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        if Shop.objects.filter(email__exact=request.data['email']).first() is not None:
            response.status_code = 422
            response.data = {'status_code':422,'Problem':'email','Message':'Email already taken'}
            return response
        
        if User.objects.filter(email__exact=request.data['email']).first() is not None:
            response.status_code = 422
            response.data = {'status_code':422,'Problem':'email','Message':'Email already taken'}
            return response
        
        try:
            while True:
                characters = string.ascii_lowercase + string.digits
                generated_id = ''.join(random.choice(characters) for _ in range(12))
                if not User.objects.filter(id=generated_id).exists() and not Shop.objects.filter(id=generated_id).exists():
                    break
            request.data['id'] = generated_id
            serializer = ShopSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            shop = Shop.objects.get(id=generated_id)
            new_shop_details = ShopDetails.objects.create(shop=shop,shop_name=request.data['shop_name'],phone_number=request.data['phone_number'])
            new_shop_details.save()
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
            response.data = {'status_code':201}
        except Exception as e:  
            response.status_code = 500
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        return response
    
class CreatePrivateCompanyPaymentAccount(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.get(shop=payload['id'])

            iyzico_request = dict([('locale', 'en')])
            iyzico_request['conversationId'] = '123456789'  # Change this for unique number for each api call 
            iyzico_request['subMerchantExternalId'] = payload['id']
            iyzico_request['subMerchantType'] = 'PRIVATE_COMPANY'
            iyzico_request['address'] = request.data['address']
            iyzico_request['taxOffice'] = request.data['taxOffice']
            iyzico_request['legalCompanyTitle'] = request.data['legalCompanyTitle']
            iyzico_request['email'] = shop.email
            iyzico_request['gsmNumber'] = shop.phone_number
            iyzico_request['name'] = shop.shop_name
            iyzico_request['iban'] = request.data['iban']
            iyzico_request['identityNumber'] = shop.identityNumber
            iyzico_request['currency'] = 'TRY'

            sub_merchant = iyzipay.SubMerchant()
            sub_merchant_response = sub_merchant.create(iyzico_request, iyzico_options)
            str_data = sub_merchant_response.read().decode('utf-8')
            data_dict = dict(eval(str_data))
            if data_dict['status'] == 'success':
                shop.subMerchantType = 'PRIVATE_COMPANY'
                shop.iban = request.data['iban']
                shop.address = request.data['address']
                shop.save()
                response.status_code = 200
                response.data = {'status_code':200}
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

class UpdatePrivateCompanyPaymentAccount(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.get(shop=payload['id'])

            iyzico_request = dict([('locale', 'en')])
            iyzico_request['conversationId'] = '123456789'     # Change this for unique number for each api call 
            iyzico_request['subMerchantKey'] = payload['id']
            iyzico_request['address'] = request.data['address']
            iyzico_request['taxOffice'] = request.data['taxOffice']
            iyzico_request['legalCompanyTitle'] = request.data['legalCompanyTitle']
            iyzico_request['email'] = request.data['email']
            iyzico_request['gsmNumber'] = request.data['gsmNumber']
            iyzico_request['name'] = request.data['shop_name']
            iyzico_request['iban'] = request.data['iban']
            iyzico_request['identityNumber'] = shop.identityNumber
            iyzico_request['currency'] = 'TRY'

            sub_merchant = iyzipay.SubMerchant()
            sub_merchant_response = sub_merchant.update(iyzico_request, iyzico_options)
            str_data = sub_merchant_response.read().decode('utf-8')
            data_dict = dict(eval(str_data))
            if data_dict['status'] == 'success':
                shop.iban = request.data['iban']
                shop.address = request.data['address']
                shop.save()
                response.status_code = 200
                response.data = {'status_code':200}
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
    
class CreateLimitedOrJointStockPaymentAccount(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.get(shop=payload['id'])

            iyzico_request = dict([('locale', 'en')])
            iyzico_request['conversationId'] = '123456789'      # Change this for unique number for each api call 
            iyzico_request['subMerchantExternalId'] = payload['id']
            iyzico_request['subMerchantType'] = 'LIMITED_OR_JOINT_STOCK_COMPANY'
            iyzico_request['address'] = request.data['address']
            iyzico_request['taxOffice'] = request.data['taxOffice']
            iyzico_request['taxNumber'] = request.data['taxNumber']
            iyzico_request['legalCompanyTitle'] = request.data['legalCompanyTitle']
            iyzico_request['email'] = shop.email
            iyzico_request['gsmNumber'] = shop.phone_number
            iyzico_request['name'] = shop.shop_name
            iyzico_request['iban'] = request.data['iban']
            iyzico_request['currency'] = 'TRY'

            sub_merchant = iyzipay.SubMerchant()
            sub_merchant_response = sub_merchant.create(iyzico_request, iyzico_options)
            str_data = sub_merchant_response.read().decode('utf-8')
            data_dict = dict(eval(str_data))
            if data_dict['status'] == 'success':
                shop.subMerchantType = 'LIMITED_OR_JOINT_STOCK_COMPANY'
                shop.iban = request.data['iban']
                shop.address = request.data['address']
                shop.save()
                response.status_code = 200
                response.data = {'status_code':200}
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
    
class UpdateLimitedOrJointStockPaymentAccount(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.get(shop=payload['id'])
            
            iyzico_request = dict([('locale', 'en')])
            iyzico_request['conversationId'] = '123456789'     # Change this for unique number for each api call 
            iyzico_request['subMerchantKey'] = payload['id']
            iyzico_request['address'] = request.data['address']
            iyzico_request['taxOffice'] = request.data['taxOffice']
            iyzico_request['taxNumber'] = request.data['taxNumber']
            iyzico_request['legalCompanyTitle'] = request.data['legalCompanyTitle']
            iyzico_request['email'] = request.data['email']
            iyzico_request['gsmNumber'] = request.data['gsmNumber']
            iyzico_request['name'] = request.data['shop_name']
            iyzico_request['iban'] = request.data['iban']
            iyzico_request['currency'] = 'TRY'

            sub_merchant = iyzipay.SubMerchant()
            sub_merchant_response = sub_merchant.update(iyzico_request, iyzico_options)
            str_data = sub_merchant_response.read().decode('utf-8')
            data_dict = dict(eval(str_data))
            if data_dict['status'] == 'success':
                shop.iban = request.data['iban']
                shop.address = request.data['address']
                shop.save()
                response.status_code = 200
                response.data = {'status_code':200}
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
    
class GetShopPaymentDetails(APIView):
    def get(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response

        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])            
            iyzico_request = dict([('locale', 'en')])
            iyzico_request['conversationId'] = '123456789'      # Change this for unique number for each api call 
            iyzico_request['subMerchantExternalId'] = payload['id']
            sub_merchant = iyzipay.SubMerchant()
            sub_merchant_response = sub_merchant.retrieve(iyzico_request, iyzico_options)
            str_data = sub_merchant_response.read().decode('utf-8')
            data_dict = dict(eval(str_data))
            if data_dict['status'] == 'success':
                response.data = data_dict
                response.data['status_code'] = 200
            else:
                response.data = {'status_code':data_dict['errorCode'],'message':data_dict['errorMessage']}
                response.status_code = int(data_dict['errorCode'])
        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
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
        shop = Shop.objects.filter(email__exact=email).first()

        if shop is None:
            response.status_code = 404
            response.data = {'status_code':404,'Problem':'User','Message':'Kullanıcı bulunamadı'}
            return response

        if not shop.check_password(password):
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Password','Message':'Şifre yanlış'}
            return response
        
        shop.last_login = timezone.now()
        shop.save()
        payload = {
            'id':shop.id,
            'exp':datetime.datetime.utcnow()+datetime.timedelta(days=30),
            'iat':datetime.datetime.utcnow()
            }
        token = jwt.encode(payload,decode_key,algorithm='HS256')
        new_token = Tokens.objects.create(token=token)
        new_token.save()
        response.status_code = 302
        response.data = {'status_code':302}
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
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.get(id=payload['id'])
            shop.last_logout = timezone.now()
            shop.save()

            token = Tokens.objects.get(token=token)
            token.delete()
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
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = ShopDetails.objects.get(shop=payload['id'])
            shop.city = request.data['city']
            shop.district = request.data['district']
            shop.neighbourhood = request.data['neighbourhood']
            shop.save()
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

class CloseShop(APIView):
    def post(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.get(id=payload['id'])
            shop.closed = True
            shop.save()
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
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.get(id=payload['id'])
            shop.set_password(request.data['new_password'])
            shop.save()
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

class GetShopDetails(APIView):
    def get(self,request):
        response = Response()

        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response

        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.filter(id=payload['id']).first()
            if shop is None:
                response.status_code = 404
                response.data = {'Problem':'User','Message':'User not found'}
                return response
            response.status_code = 200
            serialized_data = ShopSerializer(shop)
            response.data = serialized_data.data
            response.data['status_code'] = 200

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class Settings(APIView):
    def post(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.filter(id=payload['id']).first()
            if shop is None:
                response.status_code = 404
                response.data = {'Problem':'User','Message':'User not found'}
                return response
            shop.shop_name = request.data['shop_name']
            shop.phone_number = request.data['phone_number']
            shop.city = request.data['city']
            shop.district = request.data['district']
            shop.neighbourhood = request.datæ['neighbourhood']
            shop.number_of_spots = request.data['number_of_spots']
            shop.opening_hour = request.data['openin_hour']
            shop.closing_hour = request.data['closing_hour']
            shop.save()
            response.status_code = 200
            response.data = {'status_code':200}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response
    
class Addservice(APIView):
    def post(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.filter(id=payload['id']).first()
            if shop is None:
                response.status_code = 404
                response.data = {'Problem':'User','Message':'User not found'}
                return response
            services = ShopServices.objects.get(shop=shop)
            if request.data['detailing'] == True:
                services.detailing = True
                services.save()
            if request.data['waterless'] == True:
                services.waterless = True
                services.save()
            if request.data['pressurized'] == True:
                services.pressurized = True
                services.save()
            if request.data['steam'] == True:
                services.steam = True
                services.save()
            response.status_code = 201
            response.data = {'status_code':201}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response
    
class UploadPhoto(APIView):
    def post(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.filter(id=payload['id']).first()
            if shop is None:
                response.status_code = 404
                response.data = {'Problem':'User','Message':'User not found'}
                return response
            new_photo = Photo.objects.create(photo=request.FILES['photo'],shop=shop)
            new_photo.save()
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

class DeletePhoto(APIView):
    def post(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.filter(id=payload['id']).first()
            if shop is None:
                response.status_code = 404
                response.data = {'Problem':'User','Message':'User not found'}
                return response
            photo = Photo.objects.filter(id=request.data['id']).first()
            photo.delete()
            response.status_code = 200
            response.data = {'status_code':200}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response
    
class PromoteShop(APIView):
    def post(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.filter(id=payload['id']).first()
            if shop is None:
                response.status_code = 404
                response.data = {'Problem':'User','Message':'User not found'}
                return response
            promoted_shop = PromotedShops.objects.create(shop=shop,city=shop.city,district=shop.district,neighbourhood=shop.neighbourhood)
            promoted_shop.save()
            response.status_code = 200
            response.data = {'status_code':200}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response
    
class ConfigureWorkdays(APIView):
    def post(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            shop = Shop.objects.get(id=payload['id'])
            workdays = Workdays.objects.get(shop=shop)
            if request.data['monday'] == False:
                workdays.monday = False
            if request.data['tuesday'] == False:
                workdays.tuesday = False
            if request.data['wednesday'] == False:
                workdays.wednesday = False
            if request.data['thursday'] == False:
                workdays.thursday = False
            if request.data['friday'] == False:
                workdays.friday = False
            if request.data['saturday'] == False:
                workdays.friday = False
            if request.data['sunday'] == False:
                workdays.sunday = False
            workdays.save()
            response.status_code = 200
            response.data = {'status_code':200}

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response

class GetWorkdays(APIView):
    def post(self,request):
        response = Response()
        if request.headers['apikey'] not in API_KEYS:
            response.status_code = 401
            response.data = {'status_Code': 401,'Problem':'API_key','message':'api key not valid'}
            return response
        
        token = request.COOKIES.get('jwt')

        if not token:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'authentication','Message':'Not authenticated'}
            return response
        
        if Tokens.objects.filter(token=token).first() is None:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token not valid'}
            return response
        
        try:
            payload = jwt.decode(token,decode_key,algorithms=['HS256'])
            workdays = Workdays.objects.get(id=request.data['id'])
            serialized = WorkdaysSerializer(workdays)
            response.data = serialized.data
            response.status_code = 200
            response.data['status_code'] = 200

        except jwt.ExpiredSignatureError:
            response.status_code = 401
            response.data = {'status_code':401,'Problem':'Token','Message':'Token is expired'}
            
        except Exception as e:
            response.status_code = 500
            response.data = {'status_code':500,'Problem':'Server','Message':str(e)}
        
        return response