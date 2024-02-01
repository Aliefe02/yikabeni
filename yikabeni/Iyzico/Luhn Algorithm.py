def Luhn(number):
    sum = 0
    number_list = list(number)
    for i in reversed(range(len(number_list))):
        if i%2 == 0:
            number_list[i] = int(number_list[i])*2
            if int(number_list[i]) > 9:
                number_list[i] = int(number_list[i])-9
        sum += int(number_list[i])
    print(number_list)
    print(sum)
    return sum%10 == 0
        

# print(Luhn('4642180128513062'))