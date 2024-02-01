import iyzipay
import http.client
import json

# https://sandbox-merchant.iyzipay.com/

options = {
    'api_key': 'sandbox-apoQx9kBdXW7EYglM8XNqLNlE9Vq4Xfv',
    'secret_key': 'sandbox-XV1BGrhSbiK5Y0ALo0Ee1g5asNwLOPiz',
    'base_url': 'sandbox-api.iyzipay.com'
}


# # Alt üye iş yeri oluşturma
# request = dict([('locale', 'en')])
# request['conversationId'] = '123456789'
# request['subMerchantExternalId'] = 'D43241'
# request['subMerchantType'] = 'PRIVATE_COMPANY'
# request['address'] = 'Nidakule Göztepe, Merdivenköy Mah. Bora Sok. No:1'
# request['taxOffice'] = 'Tax Office'
# request['legalCompanyTitle'] = 'John Smith inc'
# request['email'] = 'email@submerchantemail.com'
# request['gsmNumber'] = '+905350000000'
# request['name'] = 'John\'s market'
# request['iban'] = 'TR180006200119000006672315'
# request['identityNumber'] = '31300864721211'
# request['currency'] = 'TRY'

# # sub_merchant = iyzipay.SubMerchant()
# # sub_merchant_response = sub_merchant.create(request, options)
# # str_data = sub_merchant_response.read().decode('utf-8')
# # data_dict = json.loads(str_data)
# # print(data_dict)



# # Alt üye iş yeri sorgulama
# request = dict([('locale', 'en')])
# request['conversationId'] = '123456789'
# request['subMerchantExternalId'] = 'D43241'

# # sub_merchant = iyzipay.SubMerchant()
# # sub_merchant_response = sub_merchant.retrieve(request, options)
# # str_data = sub_merchant_response.read().decode('utf-8')
# # data_dict = json.loads(str_data)
# # json_formatted_str = json.dumps(data_dict, indent=2)
# # print(json_formatted_str)


# Ödeme oluşturma
payment_card = {
    'cardHolderName': 'John Doe',
    'cardNumber': '5890040000000016',
    'expireMonth': '12',
    'expireYear': '2030',
    'cvc': '123',
    'registerCard': '0'
}

buyer = {
    'id': 'BY789',
    'name': 'John',
    'surname': 'Doe',
    'gsmNumber': '+905350000000',
    'email': 'email@email.com',
    'identityNumber': '74300864791',
    'lastLoginDate': '2015-10-05 12:43:35',
    'registrationDate': '2013-04-21 15:12:09',
    'registrationAddress': 'Nidakule Göztepe, Merdivenköy Mah. Bora Sok. No:1',
    'ip': '85.34.78.112',
    'city': 'Istanbul',
    'country': 'Turkey',
    'zipCode': '34732'
}

address = {
    'contactName': 'Jane Doe',
    'city': 'Istanbul',
    'country': 'Turkey',
    'address': 'Nidakule Göztepe, Merdivenköy Mah. Bora Sok. No:1',
    'zipCode': '34732'
}

basket_items = [
    {
        'id': 'BI101',
        'name': 'Oto Yıkama',
        'category1': 'Detailing',
        'itemType': 'PHYSICAL',
        'price': '20000'
    }
]

request = {
    'locale': 'en',
    'conversationId': '123456789',
    'price': '20000',
    'paidPrice': '20000',
    'currency': 'TRY',
    'installment': '1',
    'basketId': 'B67832',
    'paymentChannel': 'WEB',
    'paymentGroup': 'PRODUCT',
    'paymentCard': payment_card,
    'buyer': buyer,
    'shippingAddress': address,
    'billingAddress': address,
    'basketItems': basket_items
}

payment = iyzipay.Payment().create(request, options)
result = payment.read().decode('utf-8')
result = dict(eval(result))
# print(dict(result))
print(type(result))
print(result)