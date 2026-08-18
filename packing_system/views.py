import os
import shutil
import re
import logging
from pathlib import Path
from datetime import datetime
from django.conf import settings
from .utils.db_queries import get_db_connection
import ibm_db
import json
import base64
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
SOURCE_DIR = r"E:\Onedrive_it_intern\OneDrive - SKAPS INDUSTRIES INDIA PVT.LTD\Jay Vyas's files - Images from Server\Results From Bot"
DESTINATION_BASE = r"\\192.168.4.32\testKit"

# ====================================================================
# 1. DATABASE QUERY FUNCTIONS (UI BASED)
# ====================================================================

def fetch_customer_data_from_ui(production_order_code, production_demand_code):
    """
    Fetch customer data using UI provided order and demand codes
    """
    print("=" * 80)
    print(f"[CUSTOMER QUERY] Fetching customer data")
    print(f"[CUSTOMER QUERY] Order Code: '{production_order_code}'")
    print(f"[CUSTOMER QUERY] Demand Code: '{production_demand_code}'")
    print("=" * 80)
    
    query = """
    SELECT 
        BP.LEGALNAME1 as CustomerName,
        SOLN.EXTERNALREFERENCE as CustomerPO,
        OP.CUSTOMERSUPPLIERCODE as CustomerCode,
        PDS.PRODUCTIONORDERCODE as ProductionOrderCode,
        PDS.PRODUCTIONDEMANDCODE as DemandCode,
        PD.SUBCODE01,
        PD.SUBCODE02,
        PD.SUBCODE03,
        PD.SUBCODE04,
        PD.SUBCODE05
    FROM PRODUCTIONDEMANDSTEP PDS 
    LEFT JOIN PRODUCTIONDEMAND PD 
        ON PDS.PRODUCTIONDEMANDCOMPANYCODE = PD.COMPANYCODE
        AND PDS.PRODUCTIONDEMANDCOUNTERCODE = PD.COUNTERCODE 
        AND PDS.PRODUCTIONDEMANDCODE = PD.CODE 
    LEFT JOIN SALESORDERLINE SOLN 
        ON PD.ORIGDLVSALORDLINESALORDCNTCOD = SOLN.SALESORDERCOUNTERCODE 
        AND PD.ORIGDLVSALORDLINESALORDERCODE = SOLN.SALESORDERCODE
        AND PD.COMPANYCODE = SOLN.SALESORDERCOMPANYCODE
        AND PD.ORIGDLVSALORDERLINEORDERLINE = SOLN.ORDERLINE 
        AND PD.ORIGDLVSALORDLINEORDERSUBLINE = SOLN.ORDERSUBLINE 
        AND PD.ORIGDLVSALORDLINECMPORDERLINE = SOLN.COMPONENTORDERLINE 
    LEFT JOIN SALESORDER SO 
        ON SOLN.SALESORDERCOMPANYCODE = SO.COMPANYCODE
        AND SOLN.SALESORDERCOUNTERCODE = SO.COUNTERCODE 
        AND SOLN.SALESORDERCODE = SO.CODE
    LEFT JOIN ORDERPARTNER OP 
        ON SO.COMPANYCODE = OP.CUSTOMERSUPPLIERCOMPANYCODE 
        AND SO.ORDERTYPE = OP.CUSTOMERSUPPLIERTYPE
        AND SO.ORDPRNCUSTOMERSUPPLIERCODE = OP.CUSTOMERSUPPLIERCODE 
    LEFT JOIN BUSINESSPARTNER BP 
        ON OP.ORDERBUSINESSPARTNERNUMBERID = BP.NUMBERID
    WHERE PDS.PRODUCTIONORDERCODE = ?
      AND PDS.PRODUCTIONDEMANDCODE = ?
    """
    
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            print("[CUSTOMER QUERY] ❌ Database connection failed!")
            return None
        
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, production_order_code)
        ibm_db.bind_param(stmt, 2, production_demand_code)
        ibm_db.execute(stmt)
        
        result = ibm_db.fetch_assoc(stmt)
        
        if result:
            normalized_result = {
                'CustomerName': result.get('CUSTOMERNAME', 'UNKNOWN').strip(),
                'CustomerPO': result.get('CUSTOMERPO', 'NONE').strip(),
                'CustomerCode': result.get('CUSTOMERCODE', '').strip(),
                'ProductionOrderCode': result.get('PRODUCTIONORDERCODE', '').strip(),
                'DemandCode': result.get('DEMANDCODE', '').strip(),
                'Subcode01': result.get('SUBCODE01', '').strip(),
                'Subcode02': result.get('SUBCODE02', '').strip(),
                'Subcode03': result.get('SUBCODE03', '').strip(),
                'Subcode04': result.get('SUBCODE04', '').strip(),
                'Subcode05': result.get('SUBCODE05', '').strip()
            }
            print("[CUSTOMER QUERY] ✅ Customer data fetched successfully!")
            return normalized_result
        else:
            print("[CUSTOMER QUERY] ❌ No result found!")
            return None
            
    except Exception as e:
        print(f"[CUSTOMER QUERY] ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if conn:
            try:
                ibm_db.close(conn)
            except:
                pass
        print("=" * 80)


def fetch_product_details_from_ui(production_order_code, production_demand_code):
    """
    Fetch product details using UI provided order and demand codes
    """
    print("=" * 80)
    print(f"[PRODUCT QUERY] Fetching product details")
    print(f"[PRODUCT QUERY] Order Code: '{production_order_code}'")
    print(f"[PRODUCT QUERY] Demand Code: '{production_demand_code}'")
    print("=" * 80)
    
    query = """
    SELECT 
        PD.ITEMTYPEAFICODE as ItemType,
        PD.SUBCODE01,
        PD.SUBCODE02,
        PD.SUBCODE03,
        PD.SUBCODE04,
        PD.SUBCODE05,
        PD.SUBCODE06,
        PD.SUBCODE07,
        PD.SUBCODE08,
        PD.SUBCODE09,
        PD.SUBCODE10
    FROM PRODUCTIONDEMANDSTEP PDS
    JOIN PRODUCTIONDEMAND PD 
        ON PDS.PRODUCTIONDEMANDCOMPANYCODE = PD.COMPANYCODE
        AND PDS.PRODUCTIONDEMANDCOUNTERCODE = PD.COUNTERCODE 
        AND PDS.PRODUCTIONDEMANDCODE = PD.CODE
    WHERE PDS.PRODUCTIONORDERCODE = ?
      AND PDS.PRODUCTIONDEMANDCODE = ?
    """
    
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            print("[PRODUCT QUERY] ❌ Database connection failed!")
            return None
        
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, production_order_code)
        ibm_db.bind_param(stmt, 2, production_demand_code)
        ibm_db.execute(stmt)
        
        result = ibm_db.fetch_assoc(stmt)
        
        if result:
            normalized_result = {
                'ItemType': result.get('ITEMTYPE', 'Not Available').strip(),
                'Subcode01': result.get('SUBCODE01', 'N/A').strip(),
                'Subcode02': result.get('SUBCODE02', 'N/A').strip(),
                'Subcode03': result.get('SUBCODE03', 'N/A').strip(),
                'Subcode04': result.get('SUBCODE04', 'N/A').strip(),
                'Subcode05': result.get('SUBCODE05', 'N/A').strip(),
                'Subcode06': result.get('SUBCODE06', 'N/A').strip(),
                'Subcode07': result.get('SUBCODE07', 'N/A').strip(),
                'Subcode08': result.get('SUBCODE08', 'N/A').strip(),
                'Subcode09': result.get('SUBCODE09', 'N/A').strip(),
                'Subcode10': result.get('SUBCODE10', 'N/A').strip()
            }
            print("[PRODUCT QUERY] ✅ Result found!")
            return normalized_result
        else:
            print("[PRODUCT QUERY] ❌ No result found!")
            return None
            
    except Exception as e:
        print(f"[PRODUCT QUERY] ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if conn:
            try:
                ibm_db.close(conn)
            except:
                pass
        print("=" * 80)


def fetch_kit_elements_from_ui(production_order_code, production_demand_code, pallet_number, box_sequence):
    """
    Fetch kit elements using UI provided order, demand, pallet and box sequence
    Note: box_sequence is BOXSEQUENCE from UI, not BOXNUMBER
    """
    print("=" * 80)
    print(f"[KIT QUERY] Fetching kit elements")
    print(f"[KIT QUERY] Order Code: '{production_order_code}'")
    print(f"[KIT QUERY] Demand Code: '{production_demand_code}'")
    print(f"[KIT QUERY] Pallet Number: '{pallet_number}'")
    print(f"[KIT QUERY] Box Sequence: '{box_sequence}'")
    print("=" * 80)
    
    # IMPORTANT: Use BOXSEQUENCE, not BOXNUMBER
    query = """
    SELECT 
        KE.PALLETNUMBER,
        KE.BOXSEQUENCE,
        KE.ELEMENTDESC,
        KE.PACKINGSEQUENCE,
        KE.PLACEMENTINBOX,
        KE.BOXNUMBER,
        KE.ELEMENTSEQ,
        KE.PARTDESC,
        KE.TOTALPCS
    FROM PRODUCTIONDEMANDSTEP PDS
    LEFT JOIN PRODUCTIONDEMAND PD 
        ON PDS.PRODUCTIONDEMANDCOMPANYCODE = PD.COMPANYCODE 
        AND PDS.PRODUCTIONDEMANDCOUNTERCODE = PD.COUNTERCODE 
        AND PDS.PRODUCTIONDEMANDCODE = PD.CODE
    LEFT JOIN SKP_KITUPLOAD KE 
        ON PD.COMPANYCODE = KE.COMPANYCODE
        AND PD.ITEMTYPEAFICODE = KE.ITEMTYPECODE 
        AND PD.SUBCODE01 = KE.DECOSUBCODE01
        AND PD.SUBCODE02 = KE.DECOSUBCODE02 
        AND PD.SUBCODE03 = KE.DECOSUBCODE03 
        AND PD.SUBCODE04 = KE.DECOSUBCODE04 
        AND PD.SUBCODE05 = KE.DECOSUBCODE05 
    WHERE PDS.PRODUCTIONDEMANDCOMPANYCODE = '100'
      AND PDS.PRODUCTIONDEMANDCODE = ?
      AND PDS.PRODUCTIONORDERCODE = ?
      AND KE.PALLETNUMBER = ?
      AND KE.BOXSEQUENCE = ?
    """
    
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            print("[KIT QUERY] ❌ Database connection failed!")
            return []
        
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, production_demand_code)
        ibm_db.bind_param(stmt, 2, production_order_code)
        ibm_db.bind_param(stmt, 3, pallet_number)
        ibm_db.bind_param(stmt, 4, box_sequence)
        ibm_db.execute(stmt)
        
        results = []
        result = ibm_db.fetch_assoc(stmt)
        
        while result:
            pallet = result.get('PALLETNUMBER')
            box_seq = result.get('BOXSEQUENCE')
            element_desc = result.get('ELEMENTDESC')
            packing_seq = result.get('PACKINGSEQUENCE')
            placement = result.get('PLACEMENTINBOX')
            box_no = result.get('BOXNUMBER')
            element_seq = result.get('ELEMENTSEQ')
            part_desc = result.get('PARTDESC')
            total_pcs = result.get('TOTALPCS')
            
            results.append({
                'PALLETNUMBER': str(pallet).strip() if pallet is not None else '',
                'BOXSEQUENCE': str(box_seq).strip() if box_seq is not None else '',
                'ELEMENTDESC': str(element_desc).strip() if element_desc is not None else '',
                'PACKINGSEQUENCE': str(packing_seq).strip() if packing_seq is not None else 'PT1',
                'PLACEMENTINBOX': str(placement).strip() if placement is not None else '',
                'BOXNUMBER': str(box_no).strip() if box_no is not None else '1',
                'ELEMENTSEQ': str(element_seq).strip() if element_seq is not None else '1',
                'PARTDESC': str(part_desc).strip() if part_desc is not None else '',
                'TOTALPCS': str(total_pcs).strip() if total_pcs is not None else '0'
            })
            result = ibm_db.fetch_assoc(stmt)
        
        print(f"[KIT QUERY] ✅ Found {len(results)} kit elements")
        return results
        
    except Exception as e:
        print(f"[KIT QUERY] ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if conn:
            try:
                ibm_db.close(conn)
            except:
                pass
        print("=" * 80)


# ====================================================================
# 2. BUILD FOLDER PATH (UI BASED)
# ====================================================================

def build_folder_path_from_ui(production_order_code, production_demand_code, pallet_number, box_number):
    """
    Build folder path using UI provided values
    """
    try:
        # Step 1: Get customer data
        customer_data = fetch_customer_data_from_ui(production_order_code, production_demand_code)
        
        if customer_data:
            customer_name = customer_data.get('CustomerName', 'UNKNOWN')
            customer_po = customer_data.get('CustomerPO', 'NONE')
            subcode03 = customer_data.get('Subcode03', '')
            logger.info(f"✅ Customer: {customer_name}, PO: {customer_po}, Subcode03: {subcode03}")
        else:
            customer_name = 'UNKNOWN'
            customer_po = 'NONE'
            subcode03 = ''
            logger.warning("⚠️ No customer data found")
        
        # Step 2: Get product details for subcode03 if not found
        if not subcode03:
            product_data = fetch_product_details_from_ui(production_order_code, production_demand_code)
            if product_data:
                subcode03 = product_data.get('Subcode03', '')
                logger.info(f"✅ Subcode03 from product details: {subcode03}")
        
        # Step 3: Get kit elements for packing sequence
        kit_elements = fetch_kit_elements_from_ui(production_order_code, production_demand_code, pallet_number, box_number)
        
        packing_sequence = 'PT1'  # Default
        if kit_elements and len(kit_elements) > 0:
            packing_sequence = kit_elements[0].get('PACKINGSEQUENCE', 'PT1')
            if not packing_sequence or packing_sequence == 'None' or packing_sequence == 'null':
                packing_sequence = 'PT1'
            logger.info(f"✅ PackingSequence: {packing_sequence}")
        else:
            logger.warning("⚠️ No kit elements found, using default packing sequence")
        
        # Clean values for folder names
        customer_slug = re.sub(r'[^\w\s-]', '', customer_name).strip().upper()
        customer_slug = customer_slug.replace(' ', '-').replace('--', '-') if customer_slug else 'UNKNOWN'
        
        po_clean = customer_po.upper() if customer_po and customer_po != '-' else 'NONE'
        order_clean = production_order_code.strip().upper()
        demand_clean = production_demand_code.strip().upper()
        pallet_clean = str(pallet_number).strip().upper()
        box_clean = str(box_number).strip().upper()
        
        # Build folder path
        if subcode03 and subcode03 != 'N/A':
            demand_folder = f"{demand_clean}_{subcode03}"
            pallet_folder = f"PALLET_{pallet_clean}_{subcode03}"
        else:
            demand_folder = demand_clean
            pallet_folder = f"PALLET_{pallet_clean}"
        
        # Clean packing sequence for box folder
        box_folder_value = re.sub(r'[^\w\-]', '', packing_sequence).strip()
        if not box_folder_value or box_folder_value == 'None':
            box_folder_value = 'PT1'
        
        folder_path = f"{customer_slug}--{po_clean}/{order_clean}/{demand_folder}/{pallet_folder}/BOX_{box_clean}_{box_folder_value}"
        
        logger.info(f"✅ Generated folder path: {folder_path}")
        return folder_path
        
    except Exception as e:
        logger.error(f"❌ Error building folder path: {e}")
        import traceback
        traceback.print_exc()
        return None


# ====================================================================
# 3. FETCH DATA VIEW
# ====================================================================

def fetch_data(request):
    if request.method == 'POST':
        production_order_code = request.POST.get('production_order_code', '').strip()
        production_demand_code = request.POST.get('production_demand_code', '').strip()
        pallet_number = request.POST.get('pallet_number', '1').strip()
        box_number = request.POST.get('box_number', '1').strip()  # This is BOXSEQUENCE
        
        logger.info("=" * 60)
        logger.info(f"[DEBUG] Order Code: '{production_order_code}'")
        logger.info(f"[DEBUG] Demand Code: '{production_demand_code}'")
        logger.info(f"[DEBUG] Pallet Number: '{pallet_number}'")
        logger.info(f"[DEBUG] Box Number (BOXSEQUENCE): '{box_number}'")
        logger.info("=" * 60)
        
        if not production_order_code or not production_demand_code:
            context = {
                'error': 'Please enter Order Code and Demand Code',
                'production_order_code': production_order_code,
                'production_demand_code': production_demand_code,
                'pallet_number': pallet_number,
                'box_number': box_number,
            }
            return render(request, 'fetch_data.html', context)
        
        try:
            # Fetch data using UI parameters
            customer_data = fetch_customer_data_from_ui(production_order_code, production_demand_code)
            product_details = fetch_product_details_from_ui(production_order_code, production_demand_code)
            kit_elements = fetch_kit_elements_from_ui(production_order_code, production_demand_code, pallet_number, box_number)
            
            logger.info(f"[DEBUG] Customer Data: {customer_data is not None}")
            logger.info(f"[DEBUG] Product Details: {product_details is not None}")
            logger.info(f"[DEBUG] Kit Elements Found: {len(kit_elements) if kit_elements else 0}")
            
            # Check if data exists
            if not customer_data and not product_details and not kit_elements:
                context = {
                    'error': f'No data found for Order: {production_order_code}, Demand: {production_demand_code}, Pallet: {pallet_number}, Box: {box_number}.',
                    'production_order_code': production_order_code,
                    'production_demand_code': production_demand_code,
                    'pallet_number': pallet_number,
                    'box_number': box_number,
                }
                return render(request, 'fetch_data.html', context)
            
            # Process kit elements
            packing_sequence = 'PT1'
            if kit_elements and len(kit_elements) > 0:
                packing_sequence = kit_elements[0].get('PACKINGSEQUENCE', 'PT1')
                if not packing_sequence or packing_sequence == 'None':
                    packing_sequence = 'PT1'
            
            # Build folder path for each element and check TXT file
            for element in kit_elements:
                folder_structure = build_folder_path_from_ui(
                    production_order_code,
                    production_demand_code,
                    pallet_number,
                    box_number
                )
                
                if folder_structure:
                    element['folder_structure'] = folder_structure
                    element_desc = element.get('ELEMENTDESC', '').strip()
                    
                    # Check TXT file exists in destination
                    dest_base = Path(DESTINATION_BASE)
                    dest_folder = dest_base / folder_structure
                    txt_file_path = dest_folder / f"{element_desc}.txt"
                    element['txt_file_exists'] = txt_file_path.exists()
                    logger.info(f"[TXT] {element_desc}: {txt_file_path} -> {element['txt_file_exists']}")
                    
                    # Check image exists
                    main_path = os.path.join(settings.MEDIA_ROOT, folder_structure)
                    image_url = None
                    if os.path.exists(main_path):
                        files = os.listdir(main_path)
                        for file in files:
                            file_name = os.path.splitext(file)[0]
                            if file_name == element_desc:
                                image_url = f"{settings.MEDIA_URL}{folder_structure}/{file}".replace('\\', '/')
                                break
                    
                    element['image_url'] = image_url
                    element['has_image'] = image_url is not None
            
            # Prepare display data
            display_customer = {
                'CustomerName': customer_data.get('CustomerName', 'Not Available') if customer_data else 'Not Available',
                'CustomerPO': customer_data.get('CustomerPO', 'Not Available') if customer_data else 'Not Available',
                'CustomerCode': customer_data.get('CustomerCode', 'Not Available') if customer_data else 'Not Available'
            }
            
            display_product = {
                'ItemType': product_details.get('ItemType', 'Not Available') if product_details else 'Not Available',
                'Subcode01': product_details.get('Subcode01', 'N/A') if product_details else 'N/A',
                'Subcode02': product_details.get('Subcode02', 'N/A') if product_details else 'N/A',
                'Subcode03': product_details.get('Subcode03', 'N/A') if product_details else 'N/A',
                'Subcode04': product_details.get('Subcode04', 'N/A') if product_details else 'N/A',
                'Subcode05': product_details.get('Subcode05', 'N/A') if product_details else 'N/A',
                'PressurBal': product_details.get('Subcode03', '1') if product_details else '1',
                'PL1': '1',
                'PackingSequence': packing_sequence
            }
            
            context = {
                'customer_data': display_customer,
                'product_details': display_product,
                'kit_elements': kit_elements or [],
                'production_order_code': production_order_code,
                'production_demand_code': production_demand_code,
                'pallet_number': pallet_number,
                'box_number': box_number,
                'packing_sequence': packing_sequence,
                'MEDIA_URL': settings.MEDIA_URL,
                'DESTINATION_BASE': DESTINATION_BASE,
            }
            
            return render(request, 'view_data.html', context)
            
        except Exception as e:
            logger.error(f"[DEBUG] ❌ Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            
            context = {
                'error': f'Error: {str(e)}',
                'production_order_code': production_order_code,
                'production_demand_code': production_demand_code,
                'pallet_number': pallet_number,
                'box_number': box_number,
            }
            return render(request, 'fetch_data.html', context)

    return render(request, 'fetch_data.html')


# ====================================================================
# 4. VIEW DATA (GET Request Support)
# ====================================================================

def view_data(request):
    if request.method == 'POST':
        production_order_code = request.POST.get('production_order_code', '').strip()
        production_demand_code = request.POST.get('production_demand_code', '').strip()
        pallet_number = request.POST.get('pallet_number', '1').strip()
        box_number = request.POST.get('box_number', '1').strip()

        customer_data = fetch_customer_data_from_ui(production_order_code, production_demand_code)
        product_details = fetch_product_details_from_ui(production_order_code, production_demand_code)
        kit_elements = fetch_kit_elements_from_ui(production_order_code, production_demand_code, pallet_number, box_number)
        
        packing_sequence = 'PT1'
        if kit_elements and len(kit_elements) > 0:
            packing_sequence = kit_elements[0].get('PACKINGSEQUENCE', 'PT1')
            if not packing_sequence or packing_sequence == 'None':
                packing_sequence = 'PT1'
        
        for element in kit_elements:
            folder_structure = build_folder_path_from_ui(
                production_order_code,
                production_demand_code,
                pallet_number,
                box_number
            )
            
            element['folder_structure'] = folder_structure
            element_desc = element.get('ELEMENTDESC', '').strip()
            
            dest_base = Path(DESTINATION_BASE)
            dest_folder = dest_base / folder_structure if folder_structure else dest_base
            txt_file_path = dest_folder / f"{element_desc}.txt"
            element['txt_file_exists'] = txt_file_path.exists()
            
            image_path = os.path.join(settings.MEDIA_ROOT, folder_structure) if folder_structure else ''
            image_url = None
            if image_path and os.path.exists(image_path):
                files = os.listdir(image_path)
                for file in files:
                    file_name = os.path.splitext(file)[0]
                    if file_name == element_desc:
                        image_url = f"{settings.MEDIA_URL}{folder_structure}/{file}".replace('\\', '/')
                        break
            
            element['image_url'] = image_url
            element['has_image'] = image_url is not None

        display_customer = {
            'CustomerName': customer_data.get('CustomerName', 'Not Available') if customer_data else 'Not Available',
            'CustomerPO': customer_data.get('CustomerPO', 'Not Available') if customer_data else 'Not Available',
            'CustomerCode': customer_data.get('CustomerCode', 'Not Available') if customer_data else 'Not Available'
        }
        
        display_product = {
            'ItemType': product_details.get('ItemType', 'Not Available') if product_details else 'Not Available',
            'Subcode01': product_details.get('Subcode01', 'N/A') if product_details else 'N/A',
            'Subcode02': product_details.get('Subcode02', 'N/A') if product_details else 'N/A',
            'Subcode03': product_details.get('Subcode03', 'N/A') if product_details else 'N/A',
            'Subcode04': product_details.get('Subcode04', 'N/A') if product_details else 'N/A',
            'Subcode05': product_details.get('Subcode05', 'N/A') if product_details else 'N/A',
            'PressurBal': product_details.get('Subcode03', '1') if product_details else '1',
            'PL1': '1',
            'PackingSequence': packing_sequence
        }

        context = {
            'customer_data': display_customer,
            'product_details': display_product,
            'kit_elements': kit_elements or [],
            'production_order_code': production_order_code,
            'production_demand_code': production_demand_code,
            'pallet_number': pallet_number,
            'box_number': box_number,
            'packing_sequence': packing_sequence,
            'MEDIA_URL': settings.MEDIA_URL,
            'DESTINATION_BASE': DESTINATION_BASE,
        }

        return render(request, 'view_data.html', context)

    # GET request handling
    production_order_code = request.GET.get('production_order_code', '').strip()
    production_demand_code = request.GET.get('production_demand_code', '').strip()
    pallet_number = request.GET.get('pallet_number', '1').strip()
    box_number = request.GET.get('box_number', '1').strip()

    if production_order_code and production_demand_code:
        customer_data = fetch_customer_data_from_ui(production_order_code, production_demand_code)
        product_details = fetch_product_details_from_ui(production_order_code, production_demand_code)
        kit_elements = fetch_kit_elements_from_ui(production_order_code, production_demand_code, pallet_number, box_number)
        
        packing_sequence = 'PT1'
        if kit_elements and len(kit_elements) > 0:
            packing_sequence = kit_elements[0].get('PACKINGSEQUENCE', 'PT1')
            if not packing_sequence or packing_sequence == 'None':
                packing_sequence = 'PT1'
        
        for element in kit_elements:
            folder_structure = build_folder_path_from_ui(
                production_order_code,
                production_demand_code,
                pallet_number,
                box_number
            )
            
            element['folder_structure'] = folder_structure
            element_desc = element.get('ELEMENTDESC', '').strip()
            
            dest_base = Path(DESTINATION_BASE)
            dest_folder = dest_base / folder_structure if folder_structure else dest_base
            txt_file_path = dest_folder / f"{element_desc}.txt"
            element['txt_file_exists'] = txt_file_path.exists()
            
            image_path = os.path.join(settings.MEDIA_ROOT, folder_structure) if folder_structure else ''
            image_url = None
            if image_path and os.path.exists(image_path):
                files = os.listdir(image_path)
                for file in files:
                    file_name = os.path.splitext(file)[0]
                    if file_name == element_desc:
                        image_url = f"{settings.MEDIA_URL}{folder_structure}/{file}".replace('\\', '/')
                        break
            
            element['image_url'] = image_url
            element['has_image'] = image_url is not None

        display_customer = {
            'CustomerName': customer_data.get('CustomerName', 'Not Available') if customer_data else 'Not Available',
            'CustomerPO': customer_data.get('CustomerPO', 'Not Available') if customer_data else 'Not Available',
            'CustomerCode': customer_data.get('CustomerCode', 'Not Available') if customer_data else 'Not Available'
        }
        
        display_product = {
            'ItemType': product_details.get('ItemType', 'Not Available') if product_details else 'Not Available',
            'Subcode01': product_details.get('Subcode01', 'N/A') if product_details else 'N/A',
            'Subcode02': product_details.get('Subcode02', 'N/A') if product_details else 'N/A',
            'Subcode03': product_details.get('Subcode03', 'N/A') if product_details else 'N/A',
            'Subcode04': product_details.get('Subcode04', 'N/A') if product_details else 'N/A',
            'Subcode05': product_details.get('Subcode05', 'N/A') if product_details else 'N/A',
            'PressurBal': product_details.get('Subcode03', '1') if product_details else '1',
            'PL1': '1',
            'PackingSequence': packing_sequence
        }

        context = {
            'customer_data': display_customer,
            'product_details': display_product,
            'kit_elements': kit_elements or [],
            'production_order_code': production_order_code,
            'production_demand_code': production_demand_code,
            'pallet_number': pallet_number,
            'box_number': box_number,
            'packing_sequence': packing_sequence,
            'MEDIA_URL': settings.MEDIA_URL,
            'DESTINATION_BASE': DESTINATION_BASE,
        }

        return render(request, 'view_data.html', context)

    return render(request, 'fetch_data.html')


# ====================================================================
# 5. MOVE TXT FILES (UI Based - Scheduler Compatible)
# ====================================================================

def move_txt_files(production_order_code=None, production_demand_code=None, pallet_number=None, box_number=None):
    """
    Main function to move text files from source to destination
    Uses UI parameters if provided, otherwise uses values from database
    """
    source_path = Path(SOURCE_DIR)
    dest_base = Path(DESTINATION_BASE)
    
    if not source_path.exists():
        logger.error(f"Source directory not found: {SOURCE_DIR}")
        return False
    
    if not dest_base.exists():
        logger.error(f"Destination base directory not found: {DESTINATION_BASE}")
        try:
            dest_base.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created destination directory: {DESTINATION_BASE}")
        except Exception as e:
            logger.error(f"Could not create destination directory: {e}")
            return False
    
    txt_files = list(source_path.glob('*.txt'))
    
    if not txt_files:
        logger.info("No .txt files found in source directory")
        return True
    
    logger.info(f"Found {len(txt_files)} .txt files to process")
    
    use_ui_params = production_order_code and production_demand_code
    
    if use_ui_params:
        logger.info(f"✅ Using order: {production_order_code}, demand: {production_demand_code} from UI")
        logger.info(f"✅ Using pallet: {pallet_number}, box: {box_number} from UI")
    else:
        logger.warning("⚠️ No UI parameters provided! Using database values.")
    
    moved_count = 0
    failed_count = 0
    skipped_count = 0
    
    for file_path in txt_files:
        file_name = file_path.stem
        logger.info(f"Processing: {file_name}")
        
        try:
            if not use_ui_params:
                element_data = get_element_data_from_db(file_name)
                if not element_data:
                    logger.info(f"Element '{file_name}' not found in database. Skipping.")
                    skipped_count += 1
                    continue
                
                prod_order = element_data.get('PRODUCTIONORDERCODE', '').strip()
                prod_demand = element_data.get('PRODUCTIONDEMANDCODE', '').strip()
                pallet = element_data.get('PALLETNUMBER', '1')
                box = element_data.get('BOXSEQUENCE', '1')  # Use BOXSEQUENCE
                
                if not prod_order or not prod_demand:
                    logger.info(f"No order/demand found for '{file_name}'. Skipping.")
                    skipped_count += 1
                    continue
                
                folder_path = build_folder_path_from_ui(prod_order, prod_demand, pallet, box)
            else:
                folder_path = build_folder_path_from_ui(
                    production_order_code,
                    production_demand_code,
                    pallet_number or '1',
                    box_number or '1'
                )
            
            if not folder_path:
                logger.warning(f"Could not build folder path for {file_name}")
                failed_count += 1
                continue
            
            dest_folder = dest_base / folder_path
            dest_file_path = dest_folder / file_path.name
            
            try:
                dest_folder.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created/Verified folder: {dest_folder}")
            except Exception as e:
                logger.error(f"Could not create destination folder: {e}")
                failed_count += 1
                continue
            
            if dest_file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = f"{file_path.stem}_{timestamp}.txt"
                dest_file_path = dest_folder / new_name
                logger.info(f"File exists, renaming to: {new_name}")
            
            try:
                shutil.move(str(file_path), str(dest_file_path))
                moved_count += 1
                logger.info(f"✓ Moved: {file_path.name} -> {dest_folder.relative_to(dest_base)}")
            except Exception as e:
                logger.error(f"Error moving file: {e}")
                failed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}")
            import traceback
            traceback.print_exc()
            failed_count += 1
    
    logger.info("=" * 60)
    logger.info(f"✅ Successfully moved: {moved_count} files")
    logger.info(f"⏭️ Skipped (not in DB): {skipped_count} files")
    logger.info(f"❌ Failed: {failed_count} files")
    logger.info("=" * 60)
    
    return moved_count > 0


def get_element_data_from_db(element_desc):
    """Get element data from SKP_KITUPLOAD table"""
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        
        query = """
        SELECT 
            KE.PALLETNUMBER,
            KE.BOXSEQUENCE,
            KE.PACKINGSEQUENCE,
            KE.ELEMENTDESC,
            KE.ITEMTYPECODE,
            KE.DECOSUBCODE01,
            KE.DECOSUBCODE02,
            KE.DECOSUBCODE03,
            PDS.PRODUCTIONORDERCODE,
            PDS.PRODUCTIONDEMANDCODE
        FROM SKP_KITUPLOAD KE
        LEFT JOIN PRODUCTIONDEMANDSTEP PDS 
            ON KE.COMPANYCODE = PDS.PRODUCTIONDEMANDCOMPANYCODE
            AND KE.ITEMTYPECODE = PDS.ITEMTYPEAFICODE
        WHERE UPPER(KE.ELEMENTDESC) = UPPER(?)
        FETCH FIRST 1 ROW ONLY
        """
        
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, element_desc)
        ibm_db.execute(stmt)
        
        result = ibm_db.fetch_assoc(stmt)
        
        if result:
            return {
                'PALLETNUMBER': result.get('PALLETNUMBER', '1').strip(),
                'BOXSEQUENCE': result.get('BOXSEQUENCE', '1').strip(),
                'PACKINGSEQUENCE': result.get('PACKINGSEQUENCE', 'PT1').strip(),
                'ELEMENTDESC': result.get('ELEMENTDESC', '').strip(),
                'ITEMTYPECODE': result.get('ITEMTYPECODE', '').strip(),
                'DECOSUBCODE01': result.get('DECOSUBCODE01', '').strip(),
                'DECOSUBCODE02': result.get('DECOSUBCODE02', '').strip(),
                'DECOSUBCODE03': result.get('DECOSUBCODE03', '').strip(),
                'PRODUCTIONORDERCODE': result.get('PRODUCTIONORDERCODE', '').strip(),
                'PRODUCTIONDEMANDCODE': result.get('PRODUCTIONDEMANDCODE', '').strip()
            }
        return None
    except Exception as e:
        logger.error(f"Error getting element data: {e}")
        return None
    finally:
        if 'conn' in locals():
            try:
                ibm_db.close(conn)
            except:
                pass


# ====================================================================
# 6. ENDPOINT TO MOVE TXT FILES FROM UI
# ====================================================================

@csrf_exempt
@require_POST
def move_txt_files_endpoint(request):
    try:
        production_order_code = request.POST.get('production_order_code', '').strip()
        production_demand_code = request.POST.get('production_demand_code', '').strip()
        pallet_number = request.POST.get('pallet_number', '1').strip()
        box_number = request.POST.get('box_number', '1').strip()
        specific_file = request.POST.get('file_name', '').strip()
        
        logger.info(f"[MOVE ENDPOINT] Order: {production_order_code}, Demand: {production_demand_code}")
        logger.info(f"[MOVE ENDPOINT] Pallet: {pallet_number}, Box: {box_number}")
        
        if not production_order_code or not production_demand_code:
            return JsonResponse({
                'status': 'error',
                'message': 'Order code and Demand code are required'
            }, status=400)
        
        if specific_file:
            source_path = Path(SOURCE_DIR) / f"{specific_file}.txt"
            if not source_path.exists():
                return JsonResponse({
                    'status': 'error',
                    'message': f'File not found: {specific_file}.txt'
                }, status=404)
            
            folder_path = build_folder_path_from_ui(
                production_order_code,
                production_demand_code,
                pallet_number,
                box_number
            )
            
            if not folder_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Could not build folder path'
                }, status=400)
            
            dest_base = Path(DESTINATION_BASE)
            dest_folder = dest_base / folder_path
            dest_file_path = dest_folder / f"{specific_file}.txt"
            
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            if dest_file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = f"{specific_file}_{timestamp}.txt"
                dest_file_path = dest_folder / new_name
            
            shutil.move(str(source_path), str(dest_file_path))
            
            return JsonResponse({
                'status': 'success',
                'message': f'File moved successfully',
                'source': str(source_path),
                'destination': str(dest_file_path),
                'folder': str(folder_path)
            })
        else:
            success = move_txt_files(
                production_order_code,
                production_demand_code,
                pallet_number,
                box_number
            )
            return JsonResponse({
                'status': 'success' if success else 'error',
                'message': 'File move operation completed'
            })
            
    except Exception as e:
        logger.error(f"Error in move_txt_files_endpoint: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f"Server error: {str(e)}"
        }, status=500)


# ====================================================================
# 7. SCHEDULER JOB FUNCTION
# ====================================================================

def check_and_process_txt_files():
    try:
        logger.info("[FILE_MONITOR] 🔍 Checking for txt files...")
        success = move_txt_files()
        if success:
            logger.info("[FILE_MONITOR] ✅ File processing completed successfully")
        else:
            logger.warning("[FILE_MONITOR] ⚠️ File processing completed with issues")
        return success
    except Exception as e:
        logger.error(f"[FILE_MONITOR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ====================================================================
# 8. SCHEDULER MANAGEMENT ENDPOINTS
# ====================================================================

@csrf_exempt
@require_GET
def scheduler_status(request):
    try:
        from .scheduler import get_scheduler_status
        status = get_scheduler_status()
        return JsonResponse({
            'status': 'success',
            'scheduler': status
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
def trigger_file_check_now(request):
    try:
        from .scheduler import check_and_process_txt_files
        check_and_process_txt_files()
        return JsonResponse({
            'status': 'success',
            'message': 'File check triggered successfully'
        })
    except Exception as e:
        logger.error(f"[MANUAL CHECK ERROR] {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
def update_check_interval(request):
    try:
        from .scheduler import _scheduler
        
        interval = request.POST.get('interval', '5').strip()
        
        try:
            interval = int(interval)
            if interval < 1:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Interval must be at least 1 minute'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Interval must be a valid integer'
            }, status=400)
        
        if not _scheduler or not _scheduler.running:
            return JsonResponse({
                'status': 'error',
                'message': 'Scheduler is not running'
            }, status=500)
        
        _scheduler.reschedule_job('txt_file_monitor', trigger='interval', minutes=interval)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Check interval updated to {interval} minute(s)',
            'new_interval': interval
        })
        
    except Exception as e:
        logger.error(f"[INTERVAL UPDATE ERROR] {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# ====================================================================
# 9. UPLOAD ELEMENT IMAGE
# ====================================================================

@csrf_exempt
def upload_element_image(request):
    if request.method == 'POST':
        try:
            element_desc = request.POST.get('element_desc', '').strip()
            is_human_image = request.POST.get('is_human_image') == 'true'
            
            production_order_code = request.POST.get('production_order_code', '').strip()
            production_demand_code = request.POST.get('production_demand_code', '').strip()
            pallet_number = request.POST.get('pallet_number', '').strip()
            box_number = request.POST.get('box_number', '').strip()
            
            if is_human_image:
                filename = f"fc_{element_desc}.jpeg"
            else:
                filename = f"{element_desc}.jpeg"

            image_data = request.POST.get('element_image')
            
            if not image_data:
                return JsonResponse({'status': 'error', 'message': 'No image data'}, status=400)

            folder_structure = build_folder_path_from_ui(
                production_order_code,
                production_demand_code,
                pallet_number,
                box_number
            )
            
            if not folder_structure:
                return JsonResponse({'status': 'error', 'message': 'Could not build folder path'}, status=400)

            image_bytes = base64.b64decode(image_data)

            if is_human_image:
                network_base = r"\\192.168.4.32\Corekit"
                folder_structure_clean = folder_structure.strip('/\\')
                network_folder = os.path.join(network_base, folder_structure_clean)
                filepath = os.path.join(network_folder, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
            else:
                main_path = os.path.join(settings.MEDIA_ROOT, folder_structure)
                os.makedirs(main_path, exist_ok=True)
                filepath = os.path.join(main_path, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
            
            return JsonResponse({
                'status': 'success',
                'filename': filename,
                'path': str(filepath),
                'message': 'Image saved successfully'
            })

        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


# ====================================================================
# 10. DELETE ELEMENT IMAGE
# ====================================================================

@csrf_exempt
def delete_element_image(request):
    if request.method == 'POST':
        try:
            element_desc = request.POST.get('element_desc', '').strip()
            production_order_code = request.POST.get('production_order_code', '').strip()
            production_demand_code = request.POST.get('production_demand_code', '').strip()
            pallet_number = request.POST.get('pallet_number', '').strip()
            box_number = request.POST.get('box_number', '').strip()
            
            if not element_desc:
                return JsonResponse({'status': 'error', 'message': 'Element description is required'}, status=400)
            
            folder_structure = build_folder_path_from_ui(
                production_order_code,
                production_demand_code,
                pallet_number,
                box_number
            )
            
            if not folder_structure:
                return JsonResponse({'status': 'error', 'message': 'Could not build folder path'}, status=400)
            
            deleted_files = []
            failed_files = []
            
            element_filename = f"{element_desc}.jpeg"
            main_folder = os.path.join(settings.MEDIA_ROOT, folder_structure)
            element_file_path = os.path.join(main_folder, element_filename)
            
            if os.path.exists(element_file_path):
                try:
                    os.remove(element_file_path)
                    deleted_files.append(f"Element image: {element_filename}")
                except Exception as e:
                    failed_files.append(f"Element image: {str(e)}")
            
            human_filename = f"fc_{element_desc}.jpeg"
            try:
                network_base = r"\\192.168.4.32\Corekit"
                folder_structure_clean = folder_structure.strip('/\\')
                network_folder = os.path.join(network_base, folder_structure_clean)
                network_file_path = os.path.join(network_folder, human_filename)
                
                if os.path.exists(network_file_path):
                    os.remove(network_file_path)
                    deleted_files.append(f"Human image (network): {human_filename}")
            except Exception as e:
                logger.error(f"Error deleting network human image: {e}")
                failed_files.append(f"Human image (network): {str(e)}")
            
            if deleted_files:
                message = f"Successfully deleted: {', '.join(deleted_files)}"
                if failed_files:
                    message += f" | Failed: {', '.join(failed_files)}"
                return JsonResponse({
                    'status': 'success', 
                    'message': message,
                    'deleted_files': deleted_files,
                    'failed_files': failed_files
                })
            else:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'No images found to delete'
                }, status=404)
                
        except Exception as e:
            logger.error(f"Delete image error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error', 
                'message': f'Server error: {str(e)}'
            }, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


# ====================================================================
# 11. UPLOAD BOX CAPTURE
# ====================================================================

@csrf_exempt
@require_POST
def upload_box_capture(request):
    try:
        image_data = request.POST.get("box_image")
        
        if not image_data:
            return JsonResponse({
                "status": "error",
                "message": "No image received."
            })
        
        production_order_code = request.POST.get("production_order_code", "UNKNOWN_ORDER")
        production_demand_code = request.POST.get("production_demand_code", "UNKNOWN_DEMAND")
        pallet_number = request.POST.get("pallet_number", "UNKNOWN_PALLET")
        box_number = request.POST.get("box_number", "UNKNOWN_BOX")
        
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        
        image_bytes = base64.b64decode(image_data)
        
        filename = f"{production_order_code}_{production_demand_code}_Pallet_{pallet_number}_Box_{box_number}.jpg"
        
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        
        with open(file_path, "wb") as image_file:
            image_file.write(image_bytes)
        
        logger.info(f"✅ Box image saved: {file_path}")
        
        return JsonResponse({
            "status": "success",
            "message": "Box image uploaded successfully.",
            "filepath": file_path,
            "filename": filename
        })
        
    except Exception as e:
        logger.error(f"❌ Box image upload error: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)