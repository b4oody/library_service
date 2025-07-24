from django import forms
from django.contrib.auth.forms import UserCreationForm

from library.models import User, Genre, Author


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class BookFilterForm(forms.Form):
    genre = forms.ModelChoiceField(
        queryset=Genre.objects.all(),
        required=False,
    )
    author = forms.ModelChoiceField(
        queryset=Author.objects.all(),
        required=False
    )
    query = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={"placeholder": "Search"}
        )
    )

