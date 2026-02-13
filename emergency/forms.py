from django import forms
from .models import EmergencyRequest, EmergencyType, EmergencyVehicle  # ← Added EmergencyVehicle import

class EmergencyRequestForm(forms.ModelForm):
    """Form for citizens to submit emergency requests"""
    
    # Add a manual location field as fallback
    manual_location = forms.CharField(
        required=False,
        label='Or enter location manually',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter landmark, area, or address'
        })
    )
    
    class Meta:
        model = EmergencyRequest
        fields = [
            'emergency_type',
            'priority',
            'location_lat',
            'location_lng',
            'address',
            'landmark',
            'description',
            'contact_number',
            'additional_info',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'additional_info': forms.Textarea(attrs={'rows': 3}),
            'location_lat': forms.HiddenInput(),
            'location_lng': forms.HiddenInput(),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'emergency_type': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill contact number from user profile
        if self.user and self.user.phone_number:
            self.fields['contact_number'].initial = self.user.phone_number
        
        # Make location fields optional in form validation
        self.fields['location_lat'].required = False
        self.fields['location_lng'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        location_lat = cleaned_data.get('location_lat')
        location_lng = cleaned_data.get('location_lng')
        address = cleaned_data.get('address')
        
        # At least address must be provided
        if not address:
            self.add_error('address', 'Address is required.')
        
        return cleaned_data


class EmergencyVehicleForm(forms.ModelForm):
    """Form for managing emergency vehicles"""
    
    class Meta:
        model = EmergencyVehicle  # ← Now properly imported
        fields = ['vehicle_type', 'vehicle_number', 'driver_name', 'driver_contact', 'current_location']
        widgets = {
            'vehicle_type': forms.Select(attrs={'class': 'form-control'}),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'current_location': forms.TextInput(attrs={'class': 'form-control'}),
        }