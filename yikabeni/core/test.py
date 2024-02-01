import random
import string

def generate_user_id(length=12):
    # Define the characters to use for the user ID
    characters = string.ascii_letters + string.digits

    # Generate a random user ID of the specified length
    user_id = ''.join(random.choice(characters) for _ in range(length))

    return user_id

print(generate_user_id())