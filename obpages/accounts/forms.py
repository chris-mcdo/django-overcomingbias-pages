from django import forms
from django.contrib.auth.forms import UserCreationForm, UsernameField

from obpages.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email Address")

    class Meta:
        model = User
        fields = ("username", "email")
        field_classes = {"username": UsernameField}
