from django import forms

from .models import BarberProfile, Barbershop, Branch, Service


class ShopGeneralForm(forms.ModelForm):
    class Meta:
        model = Barbershop
        fields = [
            'name', 'tagline', 'description', 'logo', 'cover',
            'primary_color', 'phone', 'email', 'address', 'city',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'tagline': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'primary_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'address': forms.TextInput(attrs={'class': 'form-input'}),
            'city': forms.TextInput(attrs={'class': 'form-input'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-input'}),
            'cover': forms.ClearableFileInput(attrs={'class': 'form-input'}),
        }


class BookingFormConfigForm(forms.Form):
    title = forms.CharField(max_length=120, widget=forms.TextInput(attrs={'class': 'form-input'}))
    subtitle = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))
    cta_label = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'class': 'form-input'}))
    success_message = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-input'}))
    show_barber = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    show_notes = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    show_email = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    require_phone = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'address', 'city', 'whatsapp_number', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.TextInput(attrs={'class': 'form-input'}),
            'city': forms.TextInput(attrs={'class': 'form-input'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '5491112345678'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'duration_min', 'price', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'duration_min': forms.NumberInput(attrs={'class': 'form-input'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class BarberProfileForm(forms.ModelForm):
    class Meta:
        model = BarberProfile
        fields = ['branch', 'bio', 'specialties', 'calendar_color', 'is_active']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'specialties': forms.TextInput(attrs={'class': 'form-input'}),
            'calendar_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check'}),
        }

    def __init__(self, *args, shop=None, **kwargs):
        super().__init__(*args, **kwargs)
        if shop:
            self.fields['branch'].queryset = shop.branches.filter(is_active=True)
