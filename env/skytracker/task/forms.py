from django import forms
from task.models import Master_User

class LoginForm(forms.Form):
    email_id = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter Email",
                "class": "form-control rounded-1"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control rounded-1"
            }
        ))