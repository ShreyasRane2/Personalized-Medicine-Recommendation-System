import pandas as pd
import ast
import numpy as np

def parse_medication_list(med_string):
    """Parse medication string into a list with comprehensive error handling"""
    try:
        if pd.isna(med_string) or str(med_string).lower() in ['nan', 'none', '', 'false']:
            return []
        
        med_string_clean = str(med_string).strip()
        
        # Handle boolean False
        if med_string_clean.lower() == 'false':
            return []
        
        # Handle list format
        if med_string_clean.startswith('[') and med_string_clean.endswith(']'):
            med_list = ast.literal_eval(med_string_clean)
        else:
            # Handle comma-separated or single item
            if ',' in med_string_clean:
                med_list = [item.strip().strip("'\"") for item in med_string_clean.split(',')]
            else:
                med_list = [med_string_clean]
        
        if not isinstance(med_list, list):
            med_list = [str(med_string)]
        
        # Remove empty items and clean up
        med_list = [item.strip() for item in med_list if item and str(item).strip() and str(item).strip().lower() != 'false']
        return med_list
    except Exception as e:
        print(f"[MEDICATION DEBUG] Parsing error for '{med_string}': {e}")
        return [str(med_string)] if str(med_string).strip() else []

def get_filtered_medications(disease, medical_history=None, age=None):
    """
    Enhanced medication filtering based on medical history and age
    
    Args:
        disease (str): The diagnosed disease
        medical_history (str): Comma-separated medical conditions
        age (int): Patient age
    
    Returns:
        list: Filtered and personalized medication recommendations
    """
    try:
        # Load medications dataset
        medications = pd.read_csv("datasets/medications.csv")
        
        print(f"[MEDICATION FILTER] Processing disease: {disease}")
        print(f"[MEDICATION FILTER] Age: {age}, Medical History: {medical_history}")
        
        # Find disease row
        med_rows = medications[medications['Disease'].str.lower() == disease.lower()]
        
        if med_rows.empty:
            # Try partial match
            med_rows = medications[medications['Disease'].str.contains(disease, case=False, na=False)]
        
        if med_rows.empty:
            print(f"[MEDICATION FILTER] No medication data found for: {disease}")
            return [f"No specific medications found for {disease}. Please consult a healthcare provider."]
        
        med_row = med_rows.iloc[0]
        print(f"[MEDICATION FILTER] Found medication data for: {med_row['Disease']}")
        
        # Step 1: Determine base medications based on age
        if age is not None and int(age) < 18:
            # Use pediatric medications
            base_meds = parse_medication_list(med_row.get('Pediatric_Medication', ''))
            age_category = "pediatric"
            print(f"[MEDICATION FILTER] Using pediatric medications: {base_meds}")
        else:
            # Use adult medications
            base_meds = parse_medication_list(med_row.get('Adult_Medication', ''))
            age_category = "adult"
            print(f"[MEDICATION FILTER] Using adult medications: {base_meds}")
        
        if not base_meds:
            return [f"No {age_category} medications available for {disease}"]
        
        # Step 2: Apply medical history filtering if present
        if medical_history and medical_history.lower() != 'none':
            history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
            print(f"[MEDICATION FILTER] Processing medical conditions: {history_conditions}")
            
            safe_meds = []
            alternatives_added = []
            filtered_base_meds = base_meds.copy()
            warnings = []
            
            # Process each medical condition
            for condition in history_conditions:
                condition_key = None
                condition_display = condition.title()
                
                # Map condition to database column prefix
                if 'diabetes' in condition:
                    condition_key = 'Diabetes'
                    condition_display = 'Diabetes'
                elif 'hypertension' in condition or 'blood pressure' in condition or 'high blood pressure' in condition:
                    condition_key = 'Hypertension'
                    condition_display = 'Hypertension'
                elif 'heart' in condition or 'cardiac' in condition:
                    condition_key = 'Heart'
                    condition_display = 'Heart Disease'
                elif 'kidney' in condition or 'renal' in condition:
                    condition_key = 'Kidney'
                    condition_display = 'Kidney Disease'
                elif 'liver' in condition or 'hepatic' in condition:
                    condition_key = 'Liver'
                    condition_display = 'Liver Disease'
                
                if condition_key:
                    contraindicated_col = f"{condition_key}_Contraindicated"
                    alternative_col = f"{condition_key}_Alternative"
                    
                    print(f"[MEDICATION FILTER] Processing {condition_display}...")
                    
                    # Get contraindicated medications
                    if contraindicated_col in med_row.index:
                        contraindicated = parse_medication_list(med_row[contraindicated_col])
                        print(f"[MEDICATION FILTER] {condition_display} contraindicated: {contraindicated}")
                        
                        if contraindicated:
                            # Remove contraindicated medications
                            original_count = len(filtered_base_meds)
                            removed_meds = []
                            
                            new_filtered_meds = []
                            for med in filtered_base_meds:
                                is_contraindicated = False
                                for contra_med in contraindicated:
                                    if contra_med and contra_med.lower() in med.lower():
                                        is_contraindicated = True
                                        removed_meds.append(med)
                                        warnings.append(f"⚠️ REMOVED: {med} (contraindicated for {condition_display})")
                                        break
                                
                                if not is_contraindicated:
                                    new_filtered_meds.append(med)
                            
                            filtered_base_meds = new_filtered_meds
                            print(f"[MEDICATION FILTER] Removed {len(removed_meds)} medications for {condition_display}")
                    
                    # Get alternative medications
                    if alternative_col in med_row.index:
                        alternatives = parse_medication_list(med_row[alternative_col])
                        print(f"[MEDICATION FILTER] {condition_display} alternatives: {alternatives}")
                        
                        if alternatives:
                            for alt in alternatives:
                                if alt and alt not in alternatives_added:
                                    safe_meds.append(f"✅ {alt} (Safe for {condition_display})")
                                    alternatives_added.append(alt)
                                    print(f"[MEDICATION FILTER] Added alternative: {alt}")
            
            # Add remaining safe medications from filtered base list
            for med in filtered_base_meds:
                safe_meds.append(f"✅ {med}")
            
            # Add warnings to the medication list
            if warnings:
                safe_meds.extend(warnings)
            
            # If no safe medications remain, provide guidance
            if not any(med.startswith('✅') for med in safe_meds):
                safe_meds = [
                    "⚠️ MEDICAL ALERT: Standard medications for this condition may not be suitable due to your medical history.",
                    "🏥 RECOMMENDATION: Please consult your healthcare provider immediately for personalized treatment options.",
                    "👨‍⚕️ Your doctor will prescribe medications that are safe for your specific medical conditions.",
                    f"📋 CONDITIONS TO DISCUSS: {', '.join([c.title() for c in history_conditions])}"
                ]
            else:
                # Add summary information
                safe_meds.append(f"📋 FILTERED FOR: {', '.join([c.title() for c in history_conditions])}")
                if age is not None:
                    safe_meds.append(f"👤 AGE-APPROPRIATE: Dosing adjusted for {age_category} patient (age {age})")
            
            final_meds = safe_meds
            print(f"[MEDICATION FILTER] Final filtered medications: {final_meds}")
        
        else:
            # No medical history - use base medications with age info
            final_meds = [f"✅ {med}" for med in base_meds]
            if age is not None:
                final_meds.append(f"👤 AGE-APPROPRIATE: {age_category.title()} dosing (age {age})")
            print(f"[MEDICATION FILTER] No medical history, using base medications: {final_meds}")
        
        return final_meds
        
    except Exception as e:
        print(f"[MEDICATION FILTER] Error: {e}")
        import traceback
        traceback.print_exc()
        return [f"Error retrieving medications for {disease}. Please consult a healthcare provider."]

def test_medication_filtering():
    """Test the medication filtering with various scenarios"""
    print("🧪 TESTING ENHANCED MEDICATION FILTERING")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Adult with no medical history",
            "disease": "Migraine",
            "medical_history": None,
            "age": 35
        },
        {
            "name": "Child with no medical history", 
            "disease": "Common Cold",
            "medical_history": None,
            "age": 8
        },
        {
            "name": "Adult with diabetes",
            "disease": "Migraine", 
            "medical_history": "diabetes",
            "age": 45
        },
        {
            "name": "Adult with hypertension",
            "disease": "Arthritis",
            "medical_history": "hypertension", 
            "age": 55
        },
        {
            "name": "Senior with multiple conditions",
            "disease": "Arthritis",
            "medical_history": "diabetes, hypertension, heart disease",
            "age": 70
        },
        {
            "name": "Adult with kidney disease",
            "disease": "Arthritis",
            "medical_history": "kidney disease",
            "age": 50
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🔬 Test Case {i}: {case['name']}")
        print(f"   Disease: {case['disease']}")
        print(f"   Medical History: {case['medical_history']}")
        print(f"   Age: {case['age']}")
        print("   " + "-" * 40)
        
        medications = get_filtered_medications(
            case['disease'], 
            case['medical_history'], 
            case['age']
        )
        
        print("   📋 RECOMMENDED MEDICATIONS:")
        for j, med in enumerate(medications, 1):
            print(f"      {j}. {med}")
        
        print("   " + "=" * 40)

if __name__ == "__main__":
    test_medication_filtering()
