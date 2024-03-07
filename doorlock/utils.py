import random
import string


def generate_random_imei(length=15):
    imei_characters = string.digits
    return "".join(random.choice(imei_characters) for _ in range(length))
