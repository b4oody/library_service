from django import forms
from django.contrib.auth.forms import UserCreationForm

from library.models import User, Genre, Author, Purchase


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class BookFilterForm(forms.Form):

    ORDER_BY_YEAR_CHOICES = [
        ("publication_year", "За роком видання (старіші)"),
        ("-publication_year", "За роком видання (новіші)"),
    ]

    ORDER_BY_TITLE_CHOICES = [
        ("title", "За назвою (А-Я)"),
        ("-title", "За назвою (Я-А)"),
    ]

    ORDER_BY_PRICE_CHOICES = [
        ("price", "За ціною від дешевшої"),
        ("-price", "За ціною від дорожчої"),
    ]

    genre = forms.ModelChoiceField(
        queryset=Genre.objects.all(),
        required=False,
    )
    author = forms.ModelChoiceField(queryset=Author.objects.all(), required=False)
    query = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Search"}),
    )
    not_in_stock = forms.BooleanField(
        required=False,
        label="Out of stock",
    )
    in_stock = forms.BooleanField(required=False, label="In stock")

    price_min = forms.IntegerField(
        required=False, widget=forms.NumberInput(attrs={"placeholder": "Min. price"})
    )
    price_max = forms.IntegerField(
        required=False, widget=forms.NumberInput(attrs={"placeholder": "Max. price"})
    )

    order_by_year = forms.ChoiceField(
        choices=ORDER_BY_YEAR_CHOICES,
        required=False,
        label="Сортувати за роком",
        initial="-publication_year",
    )

    order_by_title = forms.ChoiceField(
        choices=ORDER_BY_TITLE_CHOICES,
        required=False,
        label="Сортувати за назвою",
        initial="title",
    )

    order_by_price = forms.ChoiceField(
        choices=ORDER_BY_PRICE_CHOICES,
        required=False,
        label="Сортувати за ціною",
        initial="price",
    )

    def clean_price_min(self):
        price_min = self.cleaned_data.get("price_min")
        price_max = self.cleaned_data.get("price_max")

        if price_min is not None and price_max is not None and price_min > price_max:
            raise forms.ValidationError(
                "Мінімальна ціна не може бути більшою за максимальну."
            )
        return price_min

    def clean(self):
        cleaned_data = super().clean()
        price_min = cleaned_data.get("price_min")
        price_max = cleaned_data.get("price_max")

        if price_min is not None and price_min < 0:
            raise forms.ValidationError("Мінімальна ціна не може бути від'ємною.")

        if price_max is not None and price_max < 0:
            raise forms.ValidationError("Мінімальна ціна не може бути від'ємною.")

        if price_min is not None and price_max is not None and price_min > price_max:
            raise forms.ValidationError(
                "Мінімальна ціна не може бути більшою за максимальну."
            )
        return cleaned_data


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ["first_name", "last_name", "email"]

