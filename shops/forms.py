from django import forms

from .models import BarberProfile, Barbershop, Establishment, Service


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


class EstablishmentForm(forms.ModelForm):
    class Meta:
        model = Establishment
        fields = [
            'name', 'address', 'city', 'whatsapp_number',
            'open_time', 'close_time', 'is_active', 'order',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.TextInput(attrs={'class': 'form-input'}),
            'city': forms.TextInput(attrs={'class': 'form-input'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '5491112345678'}),
            'open_time': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'close_time': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
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
        fields = ['photo', 'establishment', 'bio', 'specialties', 'calendar_color', 'is_active']
        widgets = {
            'photo': forms.ClearableFileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*',
            }),
            'establishment': forms.Select(attrs={'class': 'form-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'specialties': forms.TextInput(attrs={'class': 'form-input'}),
            'calendar_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check'}),
        }
        labels = {
            'photo': 'Foto de perfil',
        }

    def __init__(self, *args, shop=None, **kwargs):
        super().__init__(*args, **kwargs)
        if shop:
            self.fields['establishment'].queryset = shop.establishments.filter(is_active=True)
        self.fields['photo'].required = False


WEEKDAY_LABELS = (
    (0, 'Domingo'),
    (1, 'Lunes'),
    (2, 'Martes'),
    (3, 'Miércoles'),
    (4, 'Jueves'),
    (5, 'Viernes'),
    (6, 'Sábado'),
)

MAX_DAY_RANGES = 4


class BarberWorkHoursForm(forms.Form):
    """Weekly work schedule for a barber (Sunday-first, multi-range)."""

    def __init__(self, *args, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile
        hours = {}
        if profile:
            hours = profile.ensure_work_hours()
        self._range_counts = {}
        for day, label in WEEKDAY_LABELS:
            key = str(day)
            day_data = BarberProfile.normalize_day_hours(hours.get(key))
            count = self._range_count_for_day(day, day_data)
            self._range_counts[day] = count
            self.fields[f'work_{day}_on'] = forms.BooleanField(
                required=False,
                initial=not bool(day_data.get('off')),
                label=label,
                widget=forms.CheckboxInput(attrs={
                    'class': 'schedule-switch-input',
                    'data-schedule-toggle': str(day),
                }),
            )
            ranges = day_data.get('ranges') or [{'open': '09:00', 'close': '20:00'}]
            for i in range(count):
                rng = ranges[i] if i < len(ranges) else {'open': '09:00', 'close': '20:00'}
                self.fields[f'work_{day}_open_{i}'] = forms.TimeField(
                    required=False,
                    initial=rng.get('open') or '09:00',
                    label='Desde',
                    widget=forms.TimeInput(attrs={
                        'class': 'form-input schedule-time-input',
                        'type': 'time',
                    }),
                )
                self.fields[f'work_{day}_close_{i}'] = forms.TimeField(
                    required=False,
                    initial=rng.get('close') or '20:00',
                    label='Hasta',
                    widget=forms.TimeInput(attrs={
                        'class': 'form-input schedule-time-input',
                        'type': 'time',
                    }),
                )

    def _range_count_for_day(self, day, day_data):
        if self.is_bound and self.data is not None:
            count = 0
            while f'work_{day}_open_{count}' in self.data and count < MAX_DAY_RANGES:
                count += 1
            return max(1, count)
        return max(1, min(MAX_DAY_RANGES, len(day_data.get('ranges') or [])))

    def day_rows(self):
        rows = []
        for day, label in WEEKDAY_LABELS:
            on_field = self[f'work_{day}_on']
            ranges = []
            for i in range(self._range_counts[day]):
                ranges.append({
                    'index': i,
                    'open': self[f'work_{day}_open_{i}'],
                    'close': self[f'work_{day}_close_{i}'],
                })
            rows.append({
                'day': day,
                'label': label,
                'on': on_field,
                'ranges': ranges,
                'is_on': bool(on_field.value()),
                'can_add': len(ranges) < MAX_DAY_RANGES,
            })
        return rows

    def clean(self):
        cleaned = super().clean()
        for day, label in WEEKDAY_LABELS:
            if not cleaned.get(f'work_{day}_on'):
                continue
            intervals = []
            for i in range(self._range_counts[day]):
                open_t = cleaned.get(f'work_{day}_open_{i}')
                close_t = cleaned.get(f'work_{day}_close_{i}')
                if not open_t or not close_t:
                    raise forms.ValidationError(f'Completá todos los rangos de {label}.')
                if close_t <= open_t:
                    raise forms.ValidationError(
                        f'En {label}, cada cierre debe ser posterior a la apertura.'
                    )
                intervals.append((open_t, close_t))
            intervals.sort(key=lambda pair: pair[0])
            for prev, curr in zip(intervals, intervals[1:]):
                if curr[0] < prev[1]:
                    raise forms.ValidationError(
                        f'En {label}, los rangos no pueden solaparse.'
                    )
        return cleaned

    def save(self, profile=None):
        profile = profile or self.profile
        hours = {}
        for day, _label in WEEKDAY_LABELS:
            active = bool(self.cleaned_data.get(f'work_{day}_on'))
            ranges = []
            for i in range(self._range_counts[day]):
                open_t = self.cleaned_data.get(f'work_{day}_open_{i}')
                close_t = self.cleaned_data.get(f'work_{day}_close_{i}')
                ranges.append({
                    'open': open_t.strftime('%H:%M') if open_t else '09:00',
                    'close': close_t.strftime('%H:%M') if close_t else '20:00',
                })
            if not ranges:
                ranges = [{'open': '09:00', 'close': '20:00'}]
            hours[str(day)] = {
                'off': not active,
                'ranges': ranges,
            }
        profile.work_hours = hours
        profile.save(update_fields=['work_hours'])
        return profile
