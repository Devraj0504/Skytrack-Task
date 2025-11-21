from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from task.models import Master_User, Master_Project, Master_Task
from task.forms import LoginForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def login(request):
    request.session.flush()
    msg = None

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email_id"]
            password = form.cleaned_data["password"]

            try:
                user_obj = Master_User.objects.get(email_id=email)
                username = user_obj.email_id
            except Master_User.DoesNotExist:
                username = None

            if username:
                user = authenticate(request, username=username, password=password)
            else:
                user = None

            if user is not None:
                request.session["user_type"] = user_obj.user_type
                request.session["user_name"] = user_obj.user_name
                auth_login(request, user)
                return redirect("dashboard")
            else:
                msg = "Invalid credentials"
        else:
            msg = "Error validating the form"
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


def logout(request):
    for key in list(request.session.keys()):
        if not key.startswith("_"):
            del request.session[key]
    return redirect("login")

