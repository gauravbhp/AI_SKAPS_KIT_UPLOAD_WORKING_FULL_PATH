import ibm_db
import re
from django.conf import settings

def get_db_connection():
    conn_str = f"DATABASE={settings.DATABASES['default']['NAME']};"
    conn_str += f"HOSTNAME={settings.DATABASES['default']['HOST']};"
    conn_str += f"PORT={settings.DATABASES['default']['PORT']};"
    conn_str += f"PROTOCOL=TCPIP;"
    conn_str += f"UID={settings.DATABASES['default']['USER']};"
    conn_str += f"PWD={settings.DATABASES['default']['PASSWORD']};"
    
    return ibm_db.connect(conn_str, '', '')


def fetch_customer_data(production_order_code, production_demand_code):
    query = """
    SELECT PDS.PRODUCTIONDEMANDCOMPANYCODE as CompanyCode,
           SOLN.EXTERNALREFERENCE as CustomerPO,
           OP.CUSTOMERSUPPLIERCODE as CustomerCode,
           BP.LEGALNAME1 as CustomerName,
           PDS.PRODUCTIONDEMANDCOUNTERCODE as CounterCode,
           PDS.PRODUCTIONDEMANDCODE as DemandCode,
           PDS.PRODUCTIONORDERCODE as ProductionOrderCode,
           SO.CODE as SalesOrderCode,
           PD.SUBCODE01,
           PD.SUBCODE02,
           PD.SUBCODE03,
           PD.SUBCODE04,
           PD.SUBCODE05
    FROM PRODUCTIONDEMANDSTEP PDS 
    LEFT OUTER JOIN PRODUCTIONDEMAND PD 
           ON PDS.PRODUCTIONDEMANDCOMPANYCODE = PD.COMPANYCODE
          AND PDS.PRODUCTIONDEMANDCOUNTERCODE = PD.COUNTERCODE 
          AND PDS.PRODUCTIONDEMANDCODE = PD.CODE 
    LEFT OUTER JOIN SALESORDERLINE SOLN 
           ON PD.ORIGDLVSALORDLINESALORDCNTCOD = SOLN.SALESORDERCOUNTERCODE 
          AND PD.ORIGDLVSALORDLINESALORDERCODE = SOLN.SALESORDERCODE
          AND PD.COMPANYCODE = SOLN.SALESORDERCOMPANYCODE
          AND PD.ORIGDLVSALORDERLINEORDERLINE = SOLN.ORDERLINE 
          AND PD.ORIGDLVSALORDLINEORDERSUBLINE = SOLN.ORDERSUBLINE 
          AND PD.ORIGDLVSALORDLINECMPORDERLINE = SOLN.COMPONENTORDERLINE 
    LEFT OUTER JOIN SALESORDER SO 
           ON SOLN.SALESORDERCOMPANYCODE = SO.COMPANYCODE
          AND SOLN.SALESORDERCOUNTERCODE = SO.COUNTERCODE 
          AND SOLN.SALESORDERCODE = SO.CODE
    LEFT OUTER JOIN ORDERPARTNER OP 
           ON SO.COMPANYCODE = OP.CUSTOMERSUPPLIERCOMPANYCODE 
          AND SO.ORDERTYPE = OP.CUSTOMERSUPPLIERTYPE
          AND SO.ORDPRNCUSTOMERSUPPLIERCODE = OP.CUSTOMERSUPPLIERCODE 
    LEFT OUTER JOIN BUSINESSPARTNER BP 
           ON OP.ORDERBUSINESSPARTNERNUMBERID = BP.NUMBERID
    WHERE PDS.PRODUCTIONORDERCODE = ?
      AND PDS.PRODUCTIONDEMANDCODE = ?
    """
    
    try:
        conn = get_db_connection()
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, production_order_code)
        ibm_db.bind_param(stmt, 2, production_demand_code)
        ibm_db.execute(stmt)
        
        result = ibm_db.fetch_assoc(stmt)
        
        if not result:
            return None
            
        # Normalize the dictionary keys to match what your template expects
        normalized_result = {
            'CompanyCode': result.get('COMPANYCODE'),
            'CustomerPO': result.get('CUSTOMERPO'),
            'CustomerCode': result.get('CUSTOMERCODE'),
            'CustomerName': result.get('CUSTOMERNAME'),
            'CounterCode': result.get('COUNTERCODE'),
            'DemandCode': result.get('DEMANDCODE'),
            'ProductionOrderCode': result.get('PRODUCTIONORDERCODE'),
            'SalesOrderCode': result.get('SALESORDERCODE'),
            'Subcode01': result.get('SUBCODE01'),
            'Subcode02': result.get('SUBCODE02'),
            'Subcode03': result.get('SUBCODE03'),
            'Subcode04': result.get('SUBCODE04'),
            'Subcode05': result.get('SUBCODE05'),
            'ItemType': result.get('ITEMTYPEAFICODE', '')
        }
        
        print("Normalized Result:", normalized_result)
        return normalized_result
        
    except Exception as e:
        print("Database error:", e)
        return None
    finally:
        if 'conn' in locals():
            ibm_db.close(conn)


def fetch_product_details(production_order_code, production_demand_code):
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
    
    print("\n[PRODUCT QUERY] Executing product details query")
    print(f"[PRODUCT QUERY] Order: {production_order_code}, Demand: {production_demand_code}")

    try:
        conn = get_db_connection()
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, production_order_code)
        ibm_db.bind_param(stmt, 2, production_demand_code)
        ibm_db.execute(stmt)
        
        result = ibm_db.fetch_assoc(stmt)
        print(f"[PRODUCT RESULT] Raw DB result: {result}")
        
        if not result:
            print("[PRODUCT RESULT] No results returned from query")
            return None
            
        normalized_result = {
            'ItemType': result.get('ITEMTYPEAFICODE', 'Not Available'),
            'Subcode01': result.get('SUBCODE01', 'N/A'),
            'Subcode02': result.get('SUBCODE02', 'N/A'),
            'Subcode03': result.get('SUBCODE03', 'N/A'),
            'Subcode04': result.get('SUBCODE04', 'N/A'),
            'Subcode05': result.get('SUBCODE05', 'N/A'),
            'Subcode06': result.get('SUBCODE06', 'N/A'),
            'Subcode07': result.get('SUBCODE07', 'N/A'),
            'Subcode08': result.get('SUBCODE08', 'N/A'),
            'Subcode09': result.get('SUBCODE09', 'N/A'),
            'Subcode10': result.get('SUBCODE10', 'N/A')
        }
        
        print(f"[PRODUCT RESULT] Normalized result: {normalized_result}")
        return normalized_result
        
    except Exception as e:
        print(f"[PRODUCT ERROR] Database error: {str(e)}")
        return None
    finally:
        if 'conn' in locals():
            ibm_db.close(conn)


def try_alternative_query(production_order_code, production_demand_code):
    """Alternative query if primary one fails"""
    simple_query = """
    SELECT 
        PD.SUBCODE01, PD.SUBCODE02, PD.SUBCODE03, PD.SUBCODE04, PD.SUBCODE05,
        PD.ITEMTYPEAFICODE as ItemType
    FROM PRODUCTIONDEMANDSTEP PDS
    JOIN PRODUCTIONDEMAND PD ON PDS.PRODUCTIONDEMANDCOMPANYCODE = PD.COMPANYCODE
        AND PDS.PRODUCTIONDEMANDCOUNTERCODE = PD.COUNTERCODE 
        AND PDS.PRODUCTIONDEMANDCODE = PD.CODE
    WHERE PDS.PRODUCTIONORDERCODE = ?
      AND PDS.PRODUCTIONDEMANDCODE = ?
    """
    
    try:
        conn = get_db_connection()
        stmt = ibm_db.prepare(conn, simple_query)
        ibm_db.bind_param(stmt, 1, production_order_code)
        ibm_db.bind_param(stmt, 2, production_demand_code)
        ibm_db.execute(stmt)
        
        result = ibm_db.fetch_assoc(stmt)
        print("DEBUG - Simple Query Result:", result)
        
        if result:
            result.update({
                'CustomerName': 'Not Available',
                'CustomerPO': 'Not Available',
                'CustomerCode': 'Not Available'
            })
        
        return result
        
    except Exception as e:
        print("Alternative query error:", e)
        return None
    finally:
        if 'conn' in locals():
            ibm_db.close(conn)


def fetch_kit_elements(production_order_code, production_demand_code, pallet_number='1', box_sequence='1'):
    """
    Fetch kit elements including PACKINGSEQUENCE which contains PL1 value
    """
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
    LEFT OUTER JOIN PRODUCTIONDEMAND PD 
        ON PDS.PRODUCTIONDEMANDCOMPANYCODE = PD.COMPANYCODE 
       AND PDS.PRODUCTIONDEMANDCOUNTERCODE = PD.COUNTERCODE 
       AND PDS.PRODUCTIONDEMANDCODE = PD.CODE
    LEFT OUTER JOIN SKP_KITUPLOAD KE 
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
    
    print(f"\n[KIT QUERY] Fetching kit elements")
    print(f"[KIT QUERY] Order: {production_order_code}, Demand: {production_demand_code}")
    print(f"[KIT QUERY] Pallet: {pallet_number}, Box: {box_sequence}")
    
    try:
        conn = get_db_connection()
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, production_demand_code)
        ibm_db.bind_param(stmt, 2, production_order_code)
        ibm_db.bind_param(stmt, 3, pallet_number)
        ibm_db.bind_param(stmt, 4, box_sequence)
        ibm_db.execute(stmt)
        
        results = []
        result = ibm_db.fetch_assoc(stmt)
        while result:
            results.append(result)
            result = ibm_db.fetch_assoc(stmt)
        
        print(f"[KIT RESULT] Found {len(results)} kit elements")
        if results:
            print(f"[KIT RESULT] First record PACKINGSEQUENCE: {results[0].get('PACKINGSEQUENCE', 'N/A')}")
        
        return results
        
    except Exception as e:
        print(f"[KIT ERROR] Database error: {str(e)}")
        return []
    finally:
        if 'conn' in locals():
            ibm_db.close(conn)


def extract_pressur_bal_and_pl1(product_details, kit_elements=None):
    """
    Extract PressurBal and PL1 values from subcodes or kit elements
    
    Args:
        product_details: Dictionary with Subcode01-10 values
        kit_elements: List of kit element dictionaries from fetch_kit_elements()
    
    Returns:
        tuple: (pressur_bal, pl1)
    """
    pressur_bal = None
    pl1 = None
    
    # ========== EXTRACT PL1 FROM KIT ELEMENTS (PACKINGSEQUENCE) ==========
    if kit_elements and len(kit_elements) > 0:
        for kit in kit_elements:
            packing_sequence = kit.get('PACKINGSEQUENCE', '').strip()
            if packing_sequence and packing_sequence != 'N/A':
                print(f"[PL1 EXTRACT] Checking PACKINGSEQUENCE: '{packing_sequence}'")
                
                # Check for PL1, PL2, PL3, etc.
                match = re.search(r'PL(\d+)', packing_sequence.upper())
                if match:
                    pl1 = match.group(1)
                    print(f"[PL1 EXTRACT] Found PL1 from PACKINGSEQUENCE: {pl1}")
                    break
                elif 'PL' in packing_sequence.upper():
                    # If PL is present but no number, default to 1
                    pl1 = '1'
                    print(f"[PL1 EXTRACT] Found PL (no number) from PACKINGSEQUENCE, defaulting to: {pl1}")
                    break
    
    # ========== EXTRACT PL1 FROM PRODUCT DETAILS (Fallback) ==========
    if pl1 is None and product_details:
        print("[PL1 EXTRACT] PL1 not found in kit elements, checking product details...")
        
        # Check all Subcode fields
        for i in range(1, 11):
            subcode_key = f'Subcode{str(i).zfill(2)}'
            subcode_value = product_details.get(subcode_key, '').strip()
            
            if subcode_value and subcode_value != 'N/A':
                print(f"[PL1 EXTRACT] Checking {subcode_key}: '{subcode_value}'")
                
                # Check for PL pattern
                if 'PL1' in subcode_value.upper():
                    match = re.search(r'PL1\s*(\d+)?', subcode_value.upper())
                    if match and match.group(1):
                        pl1 = match.group(1)
                    else:
                        pl1 = '1'
                    print(f"[PL1 EXTRACT] Found PL1 in {subcode_key}: {pl1}")
                    break
                elif 'PL' in subcode_value.upper():
                    match = re.search(r'PL\s*(\d+)', subcode_value.upper())
                    if match:
                        pl1 = match.group(1)
                        print(f"[PL1 EXTRACT] Found PL in {subcode_key}: {pl1}")
                        break
                # Check for plain digits <= 3 (legacy support)
                elif subcode_value.isdigit() and len(subcode_value) <= 3:
                    if pl1 is None:
                        pl1 = subcode_value
                        print(f"[PL1 EXTRACT] Using numeric value from {subcode_key}: {pl1}")
    
    # ========== EXTRACT PRESSURBAL FROM PRODUCT DETAILS ==========
    if product_details:
        # Check Subcode03 first (most common location)
        subcode03 = product_details.get('Subcode03', '').strip()
        print(f"[PRESSURBAL EXTRACT] Checking Subcode03: '{subcode03}'")
        
        if subcode03 and subcode03 != 'N/A':
            if 'PRESSURBAL' in subcode03.upper():
                match = re.search(r'PRESSURBAL\s*(\d+)', subcode03.upper())
                if match:
                    pressur_bal = match.group(1)
                    print(f"[PRESSURBAL EXTRACT] Found PRESSURBAL in Subcode03: {pressur_bal}")
                else:
                    pressur_bal = subcode03
                    print(f"[PRESSURBAL EXTRACT] Using Subcode03 value: {pressur_bal}")
            else:
                pressur_bal = subcode03
                print(f"[PRESSURBAL EXTRACT] Using Subcode03 as pressur_bal: {pressur_bal}")
        
        # If not found in Subcode03, check other subcodes
        if pressur_bal is None:
            for i in range(1, 11):
                subcode_key = f'Subcode{str(i).zfill(2)}'
                if subcode_key != 'Subcode03':  # Skip already checked
                    subcode_value = product_details.get(subcode_key, '').strip()
                    if subcode_value and subcode_value != 'N/A':
                        if 'PRESSURBAL' in subcode_value.upper():
                            match = re.search(r'PRESSURBAL\s*(\d+)', subcode_value.upper())
                            if match:
                                pressur_bal = match.group(1)
                                print(f"[PRESSURBAL EXTRACT] Found PRESSURBAL in {subcode_key}: {pressur_bal}")
                                break
    
    # ========== EXTRACT PRESSURBAL FROM KIT ELEMENTS (Fallback) ==========
    if pressur_bal is None and kit_elements:
        print("[PRESSURBAL EXTRACT] Checking kit elements for pressure info...")
        for kit in kit_elements:
            element_desc = kit.get('ELEMENTDESC', '').strip()
            if element_desc and 'PRESSURE' in element_desc.upper():
                match = re.search(r'(\d+)', element_desc)
                if match:
                    pressur_bal = match.group(1)
                    print(f"[PRESSURBAL EXTRACT] Found pressure in ELEMENTDESC: {pressur_bal}")
                    break
    
    # ========== APPLY DEFAULTS IF NEEDED ==========
    if pressur_bal is None:
        pressur_bal = '1'
        print("[PRESSURBAL EXTRACT] Using default value: 1")
    
    if pl1 is None:
        pl1 = '1'
        print("[PL1 EXTRACT] Using default value: 1")
    
    print(f"\n[FINAL EXTRACTED VALUES] PressurBal: {pressur_bal}, PL1: {pl1}")
    return pressur_bal, pl1


# ========== MAIN FUNCTION TO GET ALL DATA ==========
def get_complete_product_data(production_order_code, production_demand_code, pallet_number='1', box_sequence='1'):
    """
    Fetch all product data including customer, product details, kit elements,
    and extracted PressurBal/PL1 values
    """
    print("\n" + "="*60)
    print(f"FETCHING DATA FOR Order: {production_order_code}, Demand: {production_demand_code}")
    print("="*60)
    
    # Fetch all required data
    customer_data = fetch_customer_data(production_order_code, production_demand_code)
    product_details = fetch_product_details(production_order_code, production_demand_code)
    kit_elements = fetch_kit_elements(production_order_code, production_demand_code, pallet_number, box_sequence)
    
    # If product_details is None but customer_data exists, use customer_data for subcodes
    if product_details is None and customer_data:
        product_details = {
            'ItemType': customer_data.get('ItemType', 'Not Available'),
            'Subcode01': customer_data.get('Subcode01', 'N/A'),
            'Subcode02': customer_data.get('Subcode02', 'N/A'),
            'Subcode03': customer_data.get('Subcode03', 'N/A'),
            'Subcode04': customer_data.get('Subcode04', 'N/A'),
            'Subcode05': customer_data.get('Subcode05', 'N/A'),
            'Subcode06': 'N/A',
            'Subcode07': 'N/A',
            'Subcode08': 'N/A',
            'Subcode09': 'N/A',
            'Subcode10': 'N/A'
        }
    
    # Extract PressurBal and PL1
    pressur_bal, pl1 = extract_pressur_bal_and_pl1(product_details, kit_elements)
    
    # Combine all data
    complete_data = {
        'customer': customer_data,
        'product': product_details,
        'kit_elements': kit_elements,
        'pressur_bal': pressur_bal,
        'pl1': pl1
    }
    
    return complete_data