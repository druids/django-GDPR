from datetime import date
from decimal import Decimal

CUSTOMER__FIRST_NAME = "John"
CUSTOMER__LAST_NAME = "Smith"
CUSTOMER__EMAIL = "smth@u.plus"
CUSTOMER__BIRTH_DATE = date(2000, 1, 1)
CUSTOMER__PERSONAL_ID = "0001010004"
CUSTOMER__PHONE_NUMBER = "605222111"
CUSTOMER__FB_ID = "4"
CUSTOMER__IP = "127.0.0.1"

CUSTOMER__KWARGS = {
    "first_name": CUSTOMER__FIRST_NAME,
    "last_name": CUSTOMER__LAST_NAME,
    "primary_email_address": CUSTOMER__EMAIL,
    "birth_date": CUSTOMER__BIRTH_DATE,
    "personal_id": CUSTOMER__PERSONAL_ID,
    "phone_number": CUSTOMER__PHONE_NUMBER,
    "fb_id": CUSTOMER__FB_ID,
    "last_login_ip": CUSTOMER__IP
}

ADDRESS__STREET = "Downing Street"
ADDRESS__HOUSE_NUMBER = "10"
ADDRESS__CITY = "London"
ADDRESS__POST_CODE = "SW1A 2AB"

ACCOUNT__NUMBER = "19-2000145399/0800"
ACCOUNT__OWNER = "John Smith"

PAYMENT__VALUE = Decimal("10.1")
