from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django import forms

User = get_user_model()

class UserCreationForm(forms.ModelForm):
    """Custom form for creating users in admin with access_code field"""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)
    access_code = forms.CharField(
        label='Access Code (4 digits)',
        max_length=4,
        required=False,
        help_text='Leave blank to auto-generate unique code. For Gov Authority, use 1111.'
    )

    class Meta:
        model = User
        fields = ('username', 'role', 'email', 'phone_number', 'access_code')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        
        # Handle access code
        access_code = self.cleaned_data.get('access_code')
        if access_code:
            user.access_code = access_code
        elif user.role != 'citizen':
            # Auto-generate unique code for staff if not provided
            user.generate_unique_access_code()
        
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """Custom form for changing users in admin"""
    access_code = forms.CharField(
        label='Access Code (4 digits)',
        max_length=4,
        required=False,
        help_text='Unique 4-digit code for staff login. Leave blank to keep current code.'
    )

    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    
    # Add access_code to fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'address', 'access_code')}),
    )
    
    # Customize add_fieldsets to include access_code
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'role', 'email', 'phone_number', 'password1', 'password2', 'access_code'),
        }),
    )
    
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active', 'access_code_display')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone_number')
    
    def access_code_display(self, obj):
        """Display access code with security note"""
        if obj.role == 'citizen':
            return 'N/A (Citizen)'
        return obj.access_code if obj.access_code else '⚠️ NOT SET'
    access_code_display.short_description = 'Access Code'
    access_code_display.admin_order_field = 'access_code'