from django import forms
from .models import Complaint


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

        self.fields['location_lat'].required = False
        self.fields['location_lng'].required = False

    def clean(self):
        cleaned_data = super().clean()
        address = cleaned_data.get('address')

        if not address:
            self.add_error('address', 'Address is required.')

        return cleaned_data


class ComplaintFeedbackForm(forms.Form):
    """Citizen feedback for resolved complaints."""

    RATING_CHOICES = [
        (5, '5 - Excellent'),
        (4, '4 - Good'),
        (3, '3 - Average'),
        (2, '2 - Poor'),
        (1, '1 - Very Poor'),
    ]

    satisfaction_rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Service Rating',
    )
    feedback_text = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional: Tell us what went well or what to improve.',
            }
        ),
        label='Feedback (Optional)',
    )
