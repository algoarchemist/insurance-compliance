"""ICD-10 code lookup table — common procedures for Indian healthcare."""

ICD_CODES = {
    # Surgical
    "K35.2": "Acute appendicitis with generalized peritonitis",
    "K35.3": "Acute appendicitis with localized peritonitis",
    "K35.80": "Unspecified acute appendicitis",
    "K80.00": "Calculus of gallbladder with acute cholecystitis",
    "K40.90": "Unilateral inguinal hernia, without obstruction or gangrene",
    "K40.30": "Unilateral inguinal hernia, with obstruction",
    "N20.0": "Calculus of kidney",
    "N20.1": "Calculus of ureter",
    "N13.2": "Hydronephrosis with renal and ureteral calculous obstruction",
    "Z41.0": "Hair transplant / cosmetic surgery",
    
    # Cardiac
    "I21.0": "Acute transmural MI of anterior wall",
    "I21.1": "Acute transmural MI of inferior wall",
    "I25.10": "Atherosclerotic heart disease",
    "I48.0": "Paroxysmal atrial fibrillation",
    "I50.9": "Heart failure, unspecified",
    
    # Orthopedic
    "M17.11": "Primary osteoarthritis, right knee",
    "M17.12": "Primary osteoarthritis, left knee",
    "M16.11": "Primary osteoarthritis, right hip",
    "S72.001": "Fracture of unspecified part of neck of right femur",
    "S82.001": "Unspecified fracture of right patella",
    
    # Obstetric
    "O80": "Encounter for full-term uncomplicated delivery",
    "O82": "Encounter for cesarean delivery without indication",
    "O60.10": "Preterm labor with preterm delivery",
    
    # Medical
    "J18.9": "Pneumonia, unspecified organism",
    "J44.1": "COPD with acute exacerbation",
    "E11.9": "Type 2 diabetes mellitus without complications",
    "E11.65": "Type 2 diabetes mellitus with hyperglycemia",
    "N18.6": "End stage renal disease",
    "A09": "Infectious gastroenteritis and colitis, unspecified",
    "A15.0": "Tuberculosis of lung",
    "B20": "HIV disease",
    
    # Cancer
    "C50.911": "Malignant neoplasm of unspecified site of right female breast",
    "C34.90": "Malignant neoplasm of unspecified part of bronchus or lung",
    "C61": "Malignant neoplasm of prostate",
    
    # Eye
    "H25.9": "Unspecified age-related cataract",
    "H40.10": "Unspecified open-angle glaucoma",
    
    # ENT
    "J35.01": "Chronic tonsillitis",
    "J34.2": "Deviated nasal septum",
}


def lookup_icd_code(code: str) -> str:
    """Look up ICD-10 code description."""
    return ICD_CODES.get(code, f"Unknown code: {code}")


def search_icd_codes(query: str) -> list:
    """Search ICD-10 codes by description."""
    query_lower = query.lower()
    results = []
    for code, desc in ICD_CODES.items():
        if query_lower in desc.lower() or query_lower in code.lower():
            results.append({"code": code, "description": desc})
    return results
