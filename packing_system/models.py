import os
import re
from django.db import models
from django.utils.text import slugify

def clean_filename(value):
    """Sanitize filenames by removing special characters"""
    return re.sub(r'[\\/*?:"<>|]', '_', str(value).strip())

def kit_image_path(instance, filename):
    """Generate consistent upload path matching new requirements"""
    customer = slugify(instance.packing_data.customer_name or 'unknown').upper()
    po = slugify(instance.packing_data.customer_po or 'none').upper()
    order = slugify(instance.packing_data.production_order_code).upper()
    
    # Get PressurBal and PL1 from packing_data
    pressur_bal = instance.packing_data.pressur_bal
    pl1 = instance.packing_data.pl1
    
    # Demand code with PRESSURBAL suffix
    demand = f"{slugify(instance.packing_data.production_demand_code).upper()}_PRESSURBAL{pressur_bal}"
    
    pallet = slugify(instance.pallet_number or '0').upper()
    box = slugify(instance.box_sequence or '0').upper()
    element = slugify(instance.element_desc or 'no_description').upper()
    
    # Generate the new path format
    return os.path.join(
        r'\\192.168.4.32\Corekit',
        'upload',
        f"{customer}--{po}",
        order,
        demand,
        f"PALLET_{pallet}",
        f"BOX_{box}_PL{pl1}",
        f"{element}.jpeg"
    )

def generate_image_path(self):
    """Generate the exact path format with new structure"""
    customer = slugify(self.packing_data.customer_name or 'unknown').upper()
    po = slugify(self.packing_data.customer_po or 'none').upper()
    order = slugify(self.packing_data.production_order_code).upper()
    
    # Get PressurBal and PL1 from packing_data
    pressur_bal = self.packing_data.pressur_bal
    pl1 = self.packing_data.pl1
    
    # Demand code with PRESSURBAL suffix
    demand = f"{slugify(self.packing_data.production_demand_code).upper()}_PRESSURBAL{pressur_bal}"
    
    pallet = self.pallet_number.upper()
    box = self.box_sequence.upper()
    element = slugify(self.element_desc).upper()
    
    # Include employee ID in filename if available
    if self.employee_id:
        filename = f"{element}_{self.employee_id}.jpeg"
    else:
        filename = f"{element}.jpeg"
    
    return f"upload/{customer}--{po}/{order}/{demand}/PALLET_{pallet}/BOX_{box}_PL{pl1}/{filename}"

class PackingData(models.Model):
    production_order_code = models.CharField(max_length=20)
    production_demand_code = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=100)
    customer_po = models.CharField(max_length=50)
    customer_code = models.CharField(max_length=20)
    pressur_bal = models.CharField(max_length=10, default='1')
    pl1 = models.CharField(max_length=10, default='1')
    subcode03 = models.CharField(max_length=50, blank=True, null=True)
    # ... other fields as needed ...

    def __str__(self):
        return f"{self.production_order_code} - {self.customer_name}"

class KitElement(models.Model):
    packing_data = models.ForeignKey(PackingData, on_delete=models.CASCADE, related_name='kit_elements')
    pallet_number = models.CharField(max_length=10)
    box_sequence = models.CharField(max_length=10)
    element_desc = models.TextField()
    image = models.ImageField(
        upload_to=kit_image_path,
        null=True,
        blank=True,
        max_length=500
    )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    employee_id = models.CharField(max_length=20, blank=True, null=True)

    def generate_image_path(self):
        """Generate the exact path format with new structure"""
        customer = slugify(self.packing_data.customer_name or 'unknown').upper()
        po = slugify(self.packing_data.customer_po or 'none').upper()
        order = slugify(self.packing_data.production_order_code).upper()
        
        # Get PressurBal and PL1 from packing_data
        pressur_bal = self.packing_data.pressur_bal
        pl1 = self.packing_data.pl1
        
        # Demand code with PRESSURBAL suffix
        demand = f"{slugify(self.packing_data.production_demand_code).upper()}_PRESSURBAL{pressur_bal}"
        
        pallet = self.pallet_number.upper()
        box = self.box_sequence.upper()
        element = slugify(self.element_desc).upper()
        
        # Include employee ID in filename if available
        if self.employee_id:
            filename = f"{element}_{self.employee_id}.jpeg"
        else:
            filename = f"{element}.jpeg"
        
        return f"upload/{customer}--{po}/{order}/{demand}/PALLET_{pallet}/BOX_{box}_PL{pl1}/{filename}"

    @property
    def image_url(self):
        """Direct URL generation without checks"""
        return f"/media/{self.generate_image_path()}"
    
    def __str__(self):
        return f"{self.pallet_number}-{self.box_sequence}: {self.element_desc[:50]}"