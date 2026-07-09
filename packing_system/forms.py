from django import forms
from .models import KitItem

class KitItemForm(forms.ModelForm):
    class Meta:
        model = KitItem
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
                'capture': 'environment'
            })
        }