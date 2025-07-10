from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.forms.fields import CharField
from django.forms.models import ModelForm

from authentication.models import User

class RegisterModelForm(ModelForm):
    confirm_password =  CharField(max_length=255 , required=True)
    class Meta:
        model= User
        fields = "fullname" , 'email' , 'password' , 'confirm_password'

    def clean_confirm_password(self):
        password = self.data.get("password")
        confirm_password = self.data.get("confirm_password")
        if password != confirm_password:
            raise ValidationError('Password tastigi xatoo !')

    def clean_password(self):
        return make_password(self.cleaned_data.get("password"))

    def save(self, commit = False):
        data = self.cleaned_data
        data.pop("confirm_password")
        return User.objects.create(**data)


class LoginModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
    class Meta:
        model = User
        fields = "email" , "password"

    def clean(self):
        data = self.cleaned_data
        email = data.get("email")
        password = data.get("password")
        query = User.objects.filter(email = email)
        if query.exists():
            user = query.first()
            if not check_password(password , user.password):
                raise ValidationError("password xato")
            self.user = user
        else:
            raise ValidationError("Topilmadi ")
        return data
