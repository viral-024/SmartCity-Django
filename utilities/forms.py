from django import forms
from .models import Complaint, UtilityType

class ComplaintForm(forms.ModelForm):
    """Form for citizens to submit utility complaints"""
    
    class Meta:
        model = Complaint
        fields = [
            'utility_type',
            'title',
            'description',
            'priority',
            'address',
            'landmark',
            'location_lat',
            'location_lng',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'location_lat': forms.HiddenInput(),
            'location_lng': forms.HiddenInput(),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'utility_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make location fields optional
        self.fields['location_lat'].required = False
        self.fields['location_lng'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        address = cleaned_data.get('address')
        
        # At least address must be provided
        if not address:
            self.add_error('address', 'Address is required.')
        
        return cleaned_data