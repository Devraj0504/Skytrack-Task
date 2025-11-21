import hmac, hashlib, base64
from django.conf import settings
import re
from django.shortcuts import redirect
from functools import wraps

def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def validate_mobile(mobile):
    phone_regex = r'^\d{10}$'  # 10 digit number check
    return re.match(phone_regex, mobile)


def generate_hash(pk: int) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(),      
        str(pk).encode(),                 
        hashlib.sha256 
    ).hexdigest()

def verify_hash(pk, given_hash):
    return generate_hash(pk) == given_hash


def generate_composite_hash(*ids):
    print("DEBUG ids =>", ids)
    data = ":".join(str(i) for i in ids)
    sig = hmac.new(settings.SECRET_KEY.encode(), data.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode()  

def verify_composite_hash(hash_value, *ids):
    expected = generate_composite_hash(*ids)
    return hmac.compare_digest(expected, hash_value)
