from urllib.parse import quote
from django.conf import settings

def generate_image_url(customer_name, customer_po, order_code, demand_code, pallet, box, element_desc, 
                       pressur_bal='1', pl1='1', employee_id='', ext=".jpeg"):
    """
    Generates image URL with new structure:
    /media/{CUSTOMER}--{PO}/{ORDER}/{DEMAND}_PRESSURBAL{pressur_bal}/PALLET_{PALLET}/BOX_{BOX}_PL{pl1}/{element}_{employee_id}.jpeg
    """
    # Clean and format - UPPERCASE
    customer = quote(f"{customer_name or 'unknown'}--{customer_po or 'none'}".replace(" ", "-").upper())
    order = quote(order_code.upper())
    demand = quote(f"{demand_code.upper()}_PRESSURBAL{pressur_bal}")
    pallet = quote(f"PALLET_{pallet or '0'}")
    box = quote(f"BOX_{box or '0'}_PL{pl1}")
    
    # Create element name with employee ID
    element_base = (element_desc or "unknown")[:50].replace(" ", "_").upper()
    if employee_id:
        element = quote(f"{element_base}_{employee_id}{ext}")
    else:
        element = quote(f"{element_base}{ext}")
    
    # No "upload/" prefix
    path = f"{customer}/{order}/{demand}/{pallet}/{box}/{element}"
    return f"{settings.MEDIA_URL}{path}"