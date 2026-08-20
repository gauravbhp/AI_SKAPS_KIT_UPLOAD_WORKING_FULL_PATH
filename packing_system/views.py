import os
import shutil
import re
import logging
from pathlib import Path
from django.conf import settings
from .utils.db_queries import get_db_connection
import ibm_db
import json
import base64
from django.shortcuts import render
from .auto_context import save_monitor_context, load_monitor_context
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from datetime import datetime
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _safe_str(value, default=''):
    """Convert DB/UI values safely to stripped strings."""
    if value is None:
        return default
    return str(value).strip()


def _clean_path_part(value, default='UNKNOWN'):
    """Create a safe single path component."""
    value = _safe_str(value, default)
    value = re.sub(r'[<>:"/\\|?*]+', '-', value)
    value = re.sub(r'\s+', '-', value).strip(' .-_')
    return value or default


def _decode_base64_image(value):
    """Decode a data-URL or plain base64 image safely."""
    if not value:
        raise ValueError("No image data received.")

    if "," in value:
        value = value.split(",", 1)[1]

    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValueError("Invalid base64 image data.") from exc


def _find_image_url(folder_path, element_desc):
    """Find an element image case-insensitively by filename stem."""
    folder = Path(folder_path)
    if not folder.is_dir():
        return None

    wanted = _safe_str(element_desc).casefold()

    for file_path in folder.iterdir():
        if file_path.is_file() and file_path.stem.casefold() == wanted:
            try:
                relative_folder = os.path.relpath(folder, settings.MEDIA_ROOT)
            except ValueError:
                relative_folder = folder.name

            if relative_folder == ".":
                relative_url = ""
            else:
                relative_url = relative_folder.replace(os.sep, "/").strip("/")

            base_url = str(settings.MEDIA_URL).rstrip("/")
            return (
                f"{base_url}/{relative_url}/{file_path.name}"
                if relative_url
                else f"{base_url}/{file_path.name}"
            )

    return None


# Paths
SOURCE_DIR = r"E:\Onedrive_it_intern\OneDrive - SKAPS INDUSTRIES INDIA PVT.LTD\Jay Vyas's files - Images from Server\Results From Bot"
DESTINATION_BASE = r"\\192.168.4.32\testKit"

# ====================================================================
# 1. CHECK TXT FILE EXISTS
# ====================================================================

def check_txt_file_exists(element_desc, folder_structure):
    """
    Check if txt file exists in the SPECIFIC folder structure
    (order/demand/pallet/box ke hisaab se)
    """
    dest_base = Path(DESTINATION_BASE)
    dest_folder = dest_base / folder_structure
    txt_file_path = dest_folder / f"{element_desc}.txt"
    
    # Sirf is specific folder mein check karo
    if txt_file_path.exists():
        logger.info(f"[TXT CHECK] ✅ Found: {txt_file_path}")
        return True
    
    logger.info(f"[TXT CHECK] ❌ Not found: {txt_file_path}")
    return False


# ====================================================================
# 2. DATABASE QUERY FUNCTIONS (UI BASED)
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
                'CustomerName': _safe_str(result.get('CUSTOMERNAME'), 'UNKNOWN'),
                'CustomerPO': _safe_str(result.get('CUSTOMERPO'), 'NONE'),
                'CustomerCode': _safe_str(result.get('CUSTOMERCODE'), ''),
                'ProductionOrderCode': _safe_str(result.get('PRODUCTIONORDERCODE'), ''),
                'DemandCode': _safe_str(result.get('DEMANDCODE'), ''),
                'Subcode01': _safe_str(result.get('SUBCODE01'), ''),
                'Subcode02': _safe_str(result.get('SUBCODE02'), ''),
                'Subcode03': _safe_str(result.get('SUBCODE03'), ''),
                'Subcode04': _safe_str(result.get('SUBCODE04'), ''),
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
                'ItemType': _safe_str(result.get('ITEMTYPE'), 'Not Available'),
                'Subcode01': result.get('SUBCODE01', 'N/A').strip(),
                'Subcode02': result.get('SUBCODE02', 'N/A').strip(),
                'Subcode03': result.get('SUBCODE03', 'N/A').strip(),
                'Subcode04': result.get('SUBCODE04', 'N/A').strip(),
                'Subcode05': result.get('SUBCODE05', 'N/A').strip(),
                'Subcode06': _safe_str(result.get('SUBCODE06'), 'N/A'),
                'Subcode07': _safe_str(result.get('SUBCODE07'), 'N/A'),
                'Subcode08': _safe_str(result.get('SUBCODE08'), 'N/A'),
                'Subcode09': _safe_str(result.get('SUBCODE09'), 'N/A'),
                'Subcode10': _safe_str(result.get('SUBCODE10'), 'N/A')
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
    JOIN SKP_KITUPLOAD KE
        ON PD.COMPANYCODE = KE.COMPANYCODE
        AND PD.ITEMTYPEAFICODE = KE.ITEMTYPECODE
        AND PD.SUBCODE01 = KE.DECOSUBCODE01
        AND PD.SUBCODE02 = KE.DECOSUBCODE02
        AND PD.SUBCODE03 = KE.DECOSUBCODE03
        AND PD.SUBCODE04 = KE.DECOSUBCODE04
        AND PD.SUBCODE05 = KE.DECOSUBCODE05
    WHERE PDS.PRODUCTIONDEMANDCODE = ?
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
        
        # get_element_data_from_db(element_desc,production_demand_code,production_order_code,pallet_number,box_sequence)
        
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
                'PALLETNUMBER': _safe_str(pallet),
                'BOXSEQUENCE': _safe_str(box_seq),
                'ELEMENTDESC': _safe_str(element_desc),
                'PACKINGSEQUENCE': _safe_str(packing_seq, 'PT1'),
                'PLACEMENTINBOX': _safe_str(placement),
                'BOXNUMBER': _safe_str(box_no, '1'),
                'ELEMENTSEQ': _safe_str(element_seq, '1'),
                'PARTDESC': _safe_str(part_desc),
                'TOTALPCS': _safe_str(total_pcs, '0')
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
# 3. BUILD FOLDER PATH (UI BASED)
# ====================================================================

def build_folder_path_from_ui(production_order_code, production_demand_code, pallet_number, box_number):
    """
    Build folder path using UI provided values
    """
    try:
        print("=" * 60)
        print("[BUILD FOLDER] Building folder path...")
        print(f"[BUILD FOLDER] Order: {production_order_code}")
        print(f"[BUILD FOLDER] Demand: {production_demand_code}")
        print(f"[BUILD FOLDER] Pallet: {pallet_number}")
        print(f"[BUILD FOLDER] Box: {box_number}")
        
        # Step 1: Get customer data
        customer_data = fetch_customer_data_from_ui(production_order_code, production_demand_code)
        
        if customer_data:
            customer_name = customer_data.get('CustomerName', 'UNKNOWN')
            customer_po = customer_data.get('CustomerPO', 'NONE')
            subcode03 = customer_data.get('Subcode03', '')
            print(f"[BUILD FOLDER] Customer Name: '{customer_name}'")
            print(f"[BUILD FOLDER] Customer PO: '{customer_po}'")
            print(f"[BUILD FOLDER] Subcode03: '{subcode03}'")
        else:
            customer_name = 'UNKNOWN'
            customer_po = 'NONE'
            subcode03 = ''
            print("[BUILD FOLDER] ⚠️ No customer data found!")
        
        # Step 2: Get product details for subcode03 if not found
        if not subcode03:
            product_data = fetch_product_details_from_ui(production_order_code, production_demand_code)
            if product_data:
                subcode03 = product_data.get('Subcode03', '')
                print(f"[BUILD FOLDER] Subcode03 from product: '{subcode03}'")
        
        # Step 3: Get kit elements for packing sequence
        kit_elements = fetch_kit_elements_from_ui(production_order_code, production_demand_code, pallet_number, box_number)
        
        packing_sequence = 'PT1'
        if kit_elements and len(kit_elements) > 0:
            packing_sequence = kit_elements[0].get('PACKINGSEQUENCE', 'PT1')
            if not packing_sequence or packing_sequence == 'None' or packing_sequence == 'null':
                packing_sequence = 'PT1'
            print(f"[BUILD FOLDER] PackingSequence: '{packing_sequence}'")
        else:
            print("[BUILD FOLDER] ⚠️ No kit elements found!")
        
        # Clean values
        customer_slug = _clean_path_part(customer_name, 'UNKNOWN').upper()
        print(f"[BUILD FOLDER] Customer Slug: '{customer_slug}'")
        
        po_clean = _clean_path_part(customer_po, 'NONE').upper()
        if po_clean == '-':
            po_clean = 'NONE'
        print(f"[BUILD FOLDER] PO Clean: '{po_clean}'")
        
        order_clean = production_order_code.strip().upper()
        demand_clean = production_demand_code.strip().upper()
        pallet_clean = str(pallet_number).strip().upper()
        box_clean = str(box_number).strip().upper()
        
        print(f"[BUILD FOLDER] Order Clean: '{order_clean}'")
        print(f"[BUILD FOLDER] Demand Clean: '{demand_clean}'")
        print(f"[BUILD FOLDER] Pallet Clean: '{pallet_clean}'")
        print(f"[BUILD FOLDER] Box Clean: '{box_clean}'")
        
        # Build folder path
        if subcode03 and subcode03 != 'N/A':
            demand_folder = f"{demand_clean}_{subcode03}"
            pallet_folder = f"PALLET_{pallet_clean}_{subcode03}"
        else:
            demand_folder = demand_clean
            pallet_folder = f"PALLET_{pallet_clean}"
        
        box_folder_value = _clean_path_part(packing_sequence, 'PT1')
        if not box_folder_value or box_folder_value == 'None':
            box_folder_value = 'PT1'
        
        folder_path = f"{customer_slug}--{po_clean}/{order_clean}/{demand_folder}/{pallet_folder}/BOX_{box_clean}_{box_folder_value}"
        
        print(f"[BUILD FOLDER] ✅ Final Folder Path: {folder_path}")
        print("=" * 60)
        
        return folder_path
        
    except Exception as e:
        print(f"[BUILD FOLDER] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


# ====================================================================
# 4. FETCH DATA VIEW
# ====================================================================

def fetch_data(request):
    if request.method == 'POST':
        production_order_code = request.POST.get('production_order_code', '').strip()
        production_demand_code = request.POST.get('production_demand_code', '').strip()
        pallet_number = request.POST.get('pallet_number', '1').strip()
        box_number = request.POST.get('box_number', '1').strip()  # This is BOXSEQUENCE

        print("=" * 60)
        print(f"[DEBUG] Order Code: '{production_order_code}'")
        print(f"[DEBUG] Demand Code: '{production_demand_code}'")
        print(f"[DEBUG] Pallet Number: '{pallet_number}'")
        print(f"[DEBUG] Box Number (BOXSEQUENCE): '{box_number}'")
        print("=" * 60)

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

            print(f"[DEBUG] Customer Data: {customer_data is not None}")
            print(f"[DEBUG] Product Details: {product_details is not None}")
            print(f"[DEBUG] Kit Elements Found: {len(kit_elements) if kit_elements else 0}")

            # Update automatic monitor context with latest UI values.
            try:
                from .scheduler import set_monitor_context

                set_monitor_context(
                    production_order_code,
                    production_demand_code,
                    pallet_number,
                    box_number,
                )
            except Exception as sched_ctx_err:
                logger.error(
                    "[SCHEDULER] Could not update monitor context: %s",
                    sched_ctx_err
                )

            # Keep the existing job-id compatibility block.
            try:
                from .scheduler import _scheduler
                if _scheduler and _scheduler.running:
                    logger.info(
                        "[SCHEDULER] Monitor is already running; "
                        "it will use the updated context on the next scan."
                    )
            except Exception as sched_err:
                logger.error(f"[SCHEDULER] Could not update job args: {sched_err}")

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
                element_desc = element.get('ELEMENTDESC', '').strip()
                folder_structure = build_folder_path_from_ui(
                    production_order_code,
                    production_demand_code,
                    pallet_number,
                    box_number
                )
                if folder_structure:
                    element['folder_structure'] = folder_structure
                    element['txt_file_exists'] = check_txt_file_exists(element_desc, folder_structure)

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

            # Persist the exact active scope and exact already-built path.
            # Background worker will use this context; it will NOT search other orders.
            active_folder_structure = build_folder_path_from_ui(
                production_order_code,
                production_demand_code,
                pallet_number,
                box_number,
            )

            if active_folder_structure:
                save_monitor_context(
                    production_order_code,
                    production_demand_code,
                    pallet_number,
                    box_number,
                    active_folder_structure,
                )

            # ------------------------------------------------------------
            # SAVE THE EXACT ACTIVE SCOPE FOR THE BACKGROUND WORKER
            # ------------------------------------------------------------
            # Worker will search ONLY this:
            #   Order + Demand + Pallet + Box
            # and will move files ONLY into this already-built folder.
            active_folder_structure = build_folder_path_from_ui(
                production_order_code,
                production_demand_code,
                pallet_number,
                box_number,
            )

            if active_folder_structure:
                save_monitor_context(
                    production_order_code,
                    production_demand_code,
                    pallet_number,
                    box_number,
                    active_folder_structure,
                )
                logger.info(
                    "[AUTO CONTEXT] ✅ Active monitor scope saved: "
                    "Order=%s Demand=%s Pallet=%s Box=%s Path=%s",
                    production_order_code,
                    production_demand_code,
                    pallet_number,
                    box_number,
                    active_folder_structure,
                )
            else:
                logger.error(
                    "[AUTO CONTEXT] ❌ Could not build active folder path."
                )

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
            print(f"[DEBUG] ❌ Exception: {str(e)}")
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
# 5. VIEW DATA (GET Request Support)
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
        
        
        monitor_and_move_files(
            production_order_code,
            production_demand_code,
            pallet_number,
            box_number
        )
       
        packing_sequence = 'PT1'
        if kit_elements and len(kit_elements) > 0:
            packing_sequence = kit_elements[0].get('PACKINGSEQUENCE', 'PT1')
            if not packing_sequence or packing_sequence == 'None':
                packing_sequence = 'PT1'
        
        for element in kit_elements:
            element_desc = element.get('ELEMENTDESC', '').strip()
            
            folder_structure = build_folder_path_from_ui(
                production_order_code,
                production_demand_code,
                pallet_number,
                box_number
            )
            
            if folder_structure:
                # Persist the exact active scope/path for the background worker.
                try:
                    save_monitor_context(
                        production_order_code,
                        production_demand_code,
                        pallet_number,
                        box_number,
                        folder_structure,
                    )

                    destination_folder = Path(DESTINATION_BASE) / folder_structure
                    destination_folder.mkdir(parents=True, exist_ok=True)

                    logger.info(
                        "[AUTO CONTEXT] ✅ Destination folder ready: %s",
                        destination_folder,
                    )
                    logger.info(
                        "[AUTO CONTEXT] ✅ Saved active scope: "
                        "Order=%s Demand=%s Pallet=%s Box=%s Path=%s",
                        production_order_code,
                        production_demand_code,
                        pallet_number,
                        box_number,
                        folder_structure,
                    )
                except Exception as context_exc:
                    logger.exception(
                        "[AUTO CONTEXT] ❌ Failed to save active scope: %s",
                        context_exc,
                    )
                    raise

                element['folder_structure'] = folder_structure
                
                # ========== CHECK TXT FILE EXISTS ==========
                element['txt_file_exists'] = check_txt_file_exists(element_desc, folder_structure)
                
                # Check image exists
                image_path = os.path.join(settings.MEDIA_ROOT, folder_structure)
                image_url = _find_image_url(image_path, element_desc)
                
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
            element_desc = element.get('ELEMENTDESC', '').strip()
            
            folder_structure = build_folder_path_from_ui(
                production_order_code,
                production_demand_code,
                pallet_number,
                box_number
            )
            
            if folder_structure:
                # Persist the exact active scope/path for the background worker.
                try:
                    save_monitor_context(
                        production_order_code,
                        production_demand_code,
                        pallet_number,
                        box_number,
                        folder_structure,
                    )

                    destination_folder = Path(DESTINATION_BASE) / folder_structure
                    destination_folder.mkdir(parents=True, exist_ok=True)

                    logger.info(
                        "[AUTO CONTEXT] ✅ Destination folder ready: %s",
                        destination_folder,
                    )
                    logger.info(
                        "[AUTO CONTEXT] ✅ Saved active scope: "
                        "Order=%s Demand=%s Pallet=%s Box=%s Path=%s",
                        production_order_code,
                        production_demand_code,
                        pallet_number,
                        box_number,
                        folder_structure,
                    )
                except Exception as context_exc:
                    logger.exception(
                        "[AUTO CONTEXT] ❌ Failed to save active scope: %s",
                        context_exc,
                    )
                    raise

                element['folder_structure'] = folder_structure
                element['txt_file_exists'] = check_txt_file_exists(element_desc, folder_structure)
                
                image_path = os.path.join(settings.MEDIA_ROOT, folder_structure)
                image_url = _find_image_url(image_path, element_desc)
                
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
# 6. MOVE TXT FILES (UI Based - Scheduler Compatible)
# ====================================================================

def move_txt_files(production_order_code, production_demand_code, pallet_number, box_number):
    """
    Main function to move text files from source to destination
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

    moved_count = 0
    failed_count = 0
    skipped_count = 0

    for file_path in txt_files:
        file_name = file_path.stem
        logger.info(f"Processing: {file_name}")

        try:
            # Always fetch element data with all parameters
            element_data = get_element_data_from_db(
                file_name,
                production_order_code,
                production_demand_code,
                pallet_number or '1',
                box_number or '1'
            )

            if not element_data:
                logger.warning(f"Element '{file_name}' not found in database. Skipping.")
                skipped_count += 1
                continue

            prod_order = element_data.get('PRODUCTIONORDERCODE', '').strip()
            prod_demand = element_data.get('PRODUCTIONDEMANDCODE', '').strip()
            pallet = element_data.get('PALLETNUMBER', '1')
            box = element_data.get('BOXSEQUENCE', '1')

            if not prod_order or not prod_demand:
                logger.warning(f"No order/demand found for '{file_name}'. Skipping.")
                skipped_count += 1
                continue

            folder_path = build_folder_path_from_ui(prod_order, prod_demand, pallet, box)

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



def find_element_context_from_db(
    element_desc,
    production_order_code,
    production_demand_code,
    pallet_number,
    box_number,
):
    """
    Find one TXT element ONLY inside the exact active production context.

    DB is filtered by:
        ELEMENTDESC
        PRODUCTIONORDERCODE
        PRODUCTIONDEMANDCODE
        PALLETNUMBER
        BOXSEQUENCE

    This deliberately does NOT search all production orders.
    """
    conn = None

    try:
        element_desc = _safe_str(element_desc)
        production_order_code = _safe_str(production_order_code)
        production_demand_code = _safe_str(production_demand_code)
        pallet_number = _safe_str(pallet_number, "1")
        box_number = _safe_str(box_number, "1")

        if not element_desc:
            logger.error("[AUTO DB] Empty ELEMENTDESC.")
            return None

        if not production_order_code or not production_demand_code:
            logger.error(
                "[AUTO DB] Missing Order/Demand context. "
                "Element=%s",
                element_desc,
            )
            return None

        conn = get_db_connection()

        if conn is None:
            logger.error("[AUTO DB] Database connection failed.")
            return None

        query = """
        SELECT
            KE.ELEMENTDESC,
            KE.PALLETNUMBER,
            KE.BOXSEQUENCE,
            KE.PACKINGSEQUENCE,
            PDS.PRODUCTIONORDERCODE,
            PDS.PRODUCTIONDEMANDCODE
        FROM SKP_KITUPLOAD KE
        JOIN PRODUCTIONDEMAND PD
            ON PD.COMPANYCODE = KE.COMPANYCODE
            AND PD.ITEMTYPEAFICODE = KE.ITEMTYPECODE
            AND PD.SUBCODE01 = KE.DECOSUBCODE01
            AND PD.SUBCODE02 = KE.DECOSUBCODE02
            AND PD.SUBCODE03 = KE.DECOSUBCODE03
            AND PD.SUBCODE04 = KE.DECOSUBCODE04
            AND PD.SUBCODE05 = KE.DECOSUBCODE05
        JOIN PRODUCTIONDEMANDSTEP PDS
            ON PDS.PRODUCTIONDEMANDCOMPANYCODE = PD.COMPANYCODE
            AND PDS.PRODUCTIONDEMANDCOUNTERCODE = PD.COUNTERCODE
            AND PDS.PRODUCTIONDEMANDCODE = PD.CODE
        WHERE UPPER(TRIM(KE.ELEMENTDESC)) = UPPER(TRIM(?))
          AND PDS.PRODUCTIONORDERCODE = ?
          AND PDS.PRODUCTIONDEMANDCODE = ?
          AND KE.PALLETNUMBER = ?
          AND KE.BOXSEQUENCE = ?
        FETCH FIRST 1 ROW ONLY
        """

        params = [
            element_desc,
            production_order_code,
            production_demand_code,
            pallet_number,
            box_number,
        ]

        logger.info(
            "[AUTO DB] Scoped lookup -> Element=%s | Order=%s | "
            "Demand=%s | Pallet=%s | Box=%s",
            element_desc,
            production_order_code,
            production_demand_code,
            pallet_number,
            box_number,
        )

        stmt = ibm_db.prepare(conn, query)

        for index, value in enumerate(params, start=1):
            ibm_db.bind_param(stmt, index, value)

        ibm_db.execute(stmt)
        result = ibm_db.fetch_assoc(stmt)

        if not result:
            logger.warning(
                "[AUTO DB] ❌ No match in selected context for '%s.txt'",
                element_desc,
            )
            return None

        data = {
            "ELEMENTDESC": _safe_str(result.get("ELEMENTDESC")),
            "PRODUCTIONORDERCODE": _safe_str(
                result.get("PRODUCTIONORDERCODE")
            ),
            "PRODUCTIONDEMANDCODE": _safe_str(
                result.get("PRODUCTIONDEMANDCODE")
            ),
            "PALLETNUMBER": _safe_str(
                result.get("PALLETNUMBER"), "1"
            ),
            "BOXSEQUENCE": _safe_str(
                result.get("BOXSEQUENCE"), "1"
            ),
            "PACKINGSEQUENCE": _safe_str(
                result.get("PACKINGSEQUENCE"), "PT1"
            ),
        }

        logger.info(
            "[AUTO DB] ✅ MATCH -> Order=%s Demand=%s Pallet=%s Box=%s "
            "Packing=%s",
            data["PRODUCTIONORDERCODE"],
            data["PRODUCTIONDEMANDCODE"],
            data["PALLETNUMBER"],
            data["BOXSEQUENCE"],
            data["PACKINGSEQUENCE"],
        )

        return data

    except Exception as exc:
        logger.exception(
            "[AUTO DB] ❌ Scoped DB lookup failed for '%s': %s",
            element_desc,
            exc,
        )
        return None

    finally:
        if conn is not None:
            try:
                ibm_db.close(conn)
            except Exception:
                logger.debug(
                    "[AUTO DB] DB connection close failed.",
                    exc_info=True,
                )



def get_element_data_from_db(
    element_desc,
    production_order_code=None,
    production_demand_code=None,
    pallet_number=None,
    box_number=None,
):
    """
    Backward-compatible wrapper.

    The automatic flow uses element_desc only.
    Optional old parameters are accepted so existing manual code does not break.
    """
    data = find_element_context_from_db(element_desc)

    if not data:
        return None

    # If old UI parameters are supplied, validate them rather than silently
    # using a mismatched record.
    if production_order_code and (
        _safe_str(production_order_code).upper()
        != data["PRODUCTIONORDERCODE"].upper()
    ):
        logger.warning(
            "[GET ELEMENT DATA] Order mismatch for '%s': UI=%s DB=%s",
            element_desc,
            production_order_code,
            data["PRODUCTIONORDERCODE"],
        )
        return None

    if production_demand_code and (
        _safe_str(production_demand_code).upper()
        != data["PRODUCTIONDEMANDCODE"].upper()
    ):
        logger.warning(
            "[GET ELEMENT DATA] Demand mismatch for '%s': UI=%s DB=%s",
            element_desc,
            production_demand_code,
            data["PRODUCTIONDEMANDCODE"],
        )
        return None

    if pallet_number and (
        _safe_str(pallet_number).upper()
        != data["PALLETNUMBER"].upper()
    ):
        logger.warning(
            "[GET ELEMENT DATA] Pallet mismatch for '%s': UI=%s DB=%s",
            element_desc,
            pallet_number,
            data["PALLETNUMBER"],
        )
        return None

    if box_number and (
        _safe_str(box_number).upper()
        != data["BOXSEQUENCE"].upper()
    ):
        logger.warning(
            "[GET ELEMENT DATA] Box mismatch for '%s': UI=%s DB=%s",
            element_desc,
            box_number,
            data["BOXSEQUENCE"],
        )
        return None

    return data


def move_txt_files_automatically():
    """
    Automatic production mover.

    Uses the last scope selected by the UI:
      Order + Demand + Pallet + Box + exact folder_structure.

    Then, for each source TXT:
      filename stem -> ELEMENTDESC
      ELEMENTDESC + 4 scope values -> DB lookup
      successful match -> move to the exact saved folder.
    """
    source_path = Path(SOURCE_DIR)
    destination_base = Path(DESTINATION_BASE)

    logger.info("[AUTO MOVE] SOURCE: %s", source_path)
    logger.info("[AUTO MOVE] DESTINATION BASE: %s", destination_base)

    if not source_path.is_dir():
        logger.error("[AUTO MOVE] ❌ SOURCE_DIR does not exist.")
        return {
            "status": "error",
            "found": 0,
            "moved": 0,
            "skipped": 0,
            "failed": 0,
        }

    context = load_monitor_context()

    if not context:
        logger.error(
            "[AUTO MOVE] ❌ NO ACTIVE CONTEXT. "
            "Open the UI and execute the request that builds the folder "
            "path first."
        )
        return {
            "status": "waiting_context",
            "found": 0,
            "moved": 0,
            "skipped": 0,
            "failed": 0,
        }

    order = context["production_order_code"]
    demand = context["production_demand_code"]
    pallet = context["pallet_number"]
    box = context["box_number"]
    folder_structure = context["folder_structure"]

    logger.info(
        "[AUTO MOVE] ACTIVE SCOPE -> Order=%s | Demand=%s | Pallet=%s | Box=%s",
        order,
        demand,
        pallet,
        box,
    )
    logger.info(
        "[AUTO MOVE] EXACT DESTINATION -> %s",
        destination_base / folder_structure,
    )

    # Exact folder path from UI.
    destination_folder = destination_base / folder_structure

    try:
        destination_folder.mkdir(parents=True, exist_ok=True)
    except Exception:
        logger.exception(
            "[AUTO MOVE] ❌ Cannot create destination folder: %s",
            destination_folder,
        )
        return {
            "status": "error",
            "found": 0,
            "moved": 0,
            "skipped": 0,
            "failed": 1,
        }

    txt_files = [
        file_path
        for file_path in source_path.iterdir()
        if file_path.is_file() and file_path.suffix.lower() == ".txt"
    ]

    logger.info(
        "[AUTO MOVE] Found %d TXT file(s).",
        len(txt_files),
    )

    moved_count = 0
    skipped_count = 0
    failed_count = 0

    for source_file in txt_files:
        element_desc = source_file.stem.strip()

        logger.info("-" * 80)
        logger.info("[AUTO MOVE] 📄 Processing %s", source_file.name)
        logger.info("[AUTO MOVE] ELEMENTDESC = %s", element_desc)

        try:
            db_data = find_element_context_from_db(
                element_desc=element_desc,
                production_order_code=order,
                production_demand_code=demand,
                pallet_number=pallet,
                box_number=box,
            )

            if not db_data:
                skipped_count += 1
                logger.warning(
                    "[AUTO MOVE] ⏭️ DB match not found in exact scope. "
                    "File stays in source: %s",
                    source_file.name,
                )
                continue

            # Defensive scope check.
            if (
                db_data["PRODUCTIONORDERCODE"].upper() != order.upper()
                or db_data["PRODUCTIONDEMANDCODE"].upper() != demand.upper()
                or db_data["PALLETNUMBER"].upper() != pallet.upper()
                or db_data["BOXSEQUENCE"].upper() != box.upper()
            ):
                failed_count += 1
                logger.error(
                    "[AUTO MOVE] ❌ DB scope mismatch. File stays in source."
                )
                continue

            destination_file = destination_folder / source_file.name

            if destination_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                destination_file = (
                    destination_folder
                    / f"{source_file.stem}_{timestamp}{source_file.suffix}"
                )

            shutil.move(
                str(source_file),
                str(destination_file),
            )

            moved_count += 1

            logger.info(
                "[AUTO MOVE] ✅ MOVED: %s",
                destination_file,
            )

        except PermissionError:
            failed_count += 1
            logger.exception(
                "[AUTO MOVE] ❌ Permission error: %s",
                source_file.name,
            )

        except OSError:
            failed_count += 1
            logger.exception(
                "[AUTO MOVE] ❌ File system error: %s",
                source_file.name,
            )

        except Exception:
            failed_count += 1
            logger.exception(
                "[AUTO MOVE] ❌ Unexpected error: %s",
                source_file.name,
            )

    logger.info("=" * 80)
    logger.info(
        "[AUTO MOVE] FINAL -> Found=%s Moved=%s Skipped=%s Failed=%s",
        len(txt_files),
        moved_count,
        skipped_count,
        failed_count,
    )
    logger.info("=" * 80)

    return {
        "status": "success" if failed_count == 0 else "partial",
        "found": len(txt_files),
        "moved": moved_count,
        "skipped": skipped_count,
        "failed": failed_count,
    }



def monitor_and_move_files(
    production_order_code=None,
    production_demand_code=None,
    pallet_number=None,
    box_number=None,
):
    """
    Automatic monitor entry point.

    The arguments are retained for backward compatibility with the UI.
    Automatic processing ignores them and derives the complete context
    from each TXT filename -> DB lookup.
    """
    return move_txt_files_automatically()



@require_GET
def automatic_file_monitor_status(request):
    """Simple debug endpoint showing source/destination configuration."""
    source = Path(SOURCE_DIR)
    destination = Path(DESTINATION_BASE)

    txt_files = []
    if source.is_dir():
        txt_files = [p.name for p in source.iterdir()
                     if p.is_file() and p.suffix.lower() == ".txt"]

    return JsonResponse({
        "status": "ok",
        "source_dir": str(source),
        "source_exists": source.is_dir(),
        "destination_base": str(destination),
        "destination_exists": destination.is_dir(),
        "pending_txt_files": txt_files,
    })


# ====================================================================
# 10. UPLOAD ELEMENT IMAGE
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

            image_bytes = _decode_base64_image(image_data)

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
# 11. DELETE ELEMENT IMAGE
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
# 12. UPLOAD BOX CAPTURE
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