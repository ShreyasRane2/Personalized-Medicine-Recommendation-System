import pandas as pd
import ast

# Load the medications CSV to debug the filtering
print("=== DEBUGGING MEDICATION FILTERING ===")

try:
    medications = pd.read_csv("datasets/medications.csv")
    print(f"✅ Medications CSV loaded successfully")
    print(f"📊 Shape: {medications.shape}")
    print(f"📋 Columns: {list(medications.columns)}")
    print()
    
    # Show first few rows
    print("🔍 First 3 rows of medications data:")
    print(medications.head(3).to_string())
    print()
    
    # Test specific disease lookup
    test_disease = "Diabetes"
    print(f"🧪 Testing disease lookup for: {test_disease}")
    
    # Try exact match
    exact_match = medications[medications['Disease'].str.lower() == test_disease.lower()]
    print(f"📍 Exact match found: {len(exact_match)} rows")
    
    if not exact_match.empty:
        row = exact_match.iloc[0]
        print(f"✅ Found row for {test_disease}")
        
        # Test parsing each medication column
        print("\n🧬 Testing medication column parsing:")
        
        # Adult medications
        if 'Adult_Medication' in medications.columns:
            adult_meds = row['Adult_Medication']
            print(f"📝 Raw Adult_Medication: {adult_meds}")
            print(f"📝 Type: {type(adult_meds)}")
            
            try:
                if pd.isna(adult_meds):
                    parsed_adult = []
                else:
                    parsed_adult = ast.literal_eval(str(adult_meds))
                print(f"✅ Parsed Adult_Medication: {parsed_adult}")
            except Exception as e:
                print(f"❌ Error parsing Adult_Medication: {e}")
        
        # Test contraindication columns
        contraindication_columns = [
            'Diabetes_Contraindicated', 'Diabetes_Alternative',
            'Hypertension_Contraindicated', 'Hypertension_Alternative',
            'Heart_Contraindicated', 'Heart_Alternative',
            'Kidney_Contraindicated', 'Kidney_Alternative',
            'Liver_Contraindicated', 'Liver_Alternative'
        ]
        
        print("\n🚫 Testing contraindication columns:")
        for col in contraindication_columns:
            if col in medications.columns:
                value = row[col]
                print(f"📋 {col}: {value} (Type: {type(value)})")
                
                try:
                    if pd.isna(value) or str(value).strip() == '':
                        parsed = []
                    else:
                        parsed = ast.literal_eval(str(value))
                        if not isinstance(parsed, list):
                            parsed = [str(value)]
                    print(f"   ✅ Parsed: {parsed}")
                except Exception as e:
                    print(f"   ❌ Parse error: {e}")
            else:
                print(f"❌ Column {col} not found")
        
    else:
        print(f"❌ No exact match found for {test_disease}")
        
        # Try partial match
        partial_match = medications[medications['Disease'].str.contains(test_disease, case=False, na=False)]
        print(f"📍 Partial match found: {len(partial_match)} rows")
        
        if not partial_match.empty:
            print("🔍 Partial matches:")
            for idx, row in partial_match.iterrows():
                print(f"   - {row['Disease']}")
    
    print("\n" + "="*50)
    
    # Test the actual filtering function
    print("🧪 TESTING ACTUAL FILTERING FUNCTION")
    
    def parse_medication_list(med_string):
        """Parse medication string into a list"""
        try:
            if pd.isna(med_string) or str(med_string).lower() in ['nan', 'none', '']:
                return []
            
            med_string_clean = str(med_string).strip()
            if med_string_clean.startswith('[') and med_string_clean.endswith(']'):
                med_list = ast.literal_eval(med_string_clean)
            else:
                # Split by comma if it's a comma-separated string
                med_list = [item.strip().strip("'\"") for item in med_string_clean.split(',')]
            
            if not isinstance(med_list, list):
                med_list = [str(med_string)]
            
            # Remove empty items
            med_list = [item for item in med_list if item and str(item).strip()]
            return med_list
        except (ValueError, SyntaxError) as e:
            print(f"[MEDICATION DEBUG] Parsing error: {e}, using raw string")
            return [str(med_string)]
    
    # Test with diabetes patient
    print("\n👤 Testing with Diabetes patient:")
    test_disease = "Diabetes"
    medical_history = "diabetes"
    
    med_rows = medications[medications['Disease'].str.lower() == test_disease.lower()]
    if not med_rows.empty:
        med_row = med_rows.iloc[0]
        
        # Get base medications
        base_meds = parse_medication_list(med_row['Adult_Medication'])
        print(f"🏥 Base medications: {base_meds}")
        
        # Apply diabetes filtering
        safe_meds = []
        alternatives_added = []
        filtered_base_meds = base_meds.copy()
        
        # Remove diabetes contraindicated medications
        if 'Diabetes_Contraindicated' in medications.columns:
            contraindicated = parse_medication_list(med_row['Diabetes_Contraindicated'])
            print(f"🚫 Diabetes contraindicated: {contraindicated}")
            
            if contraindicated:
                # Remove contraindicated medications from base list
                original_count = len(filtered_base_meds)
                filtered_base_meds = [med for med in filtered_base_meds 
                                    if not any(contra.lower() in med.lower() for contra in contraindicated)]
                print(f"🔄 Filtered medications: {filtered_base_meds}")
                print(f"📊 Removed {original_count - len(filtered_base_meds)} contraindicated medications")
        
        # Add diabetes alternatives if available
        if 'Diabetes_Alternative' in medications.columns:
            alternatives = parse_medication_list(med_row['Diabetes_Alternative'])
            print(f"✅ Diabetes alternatives: {alternatives}")
            
            if alternatives:
                for alt in alternatives:
                    if alt not in alternatives_added:
                        safe_meds.append(f"{alt} (Diabetes-safe)")
                        alternatives_added.append(alt)
        
        # Add remaining safe medications from filtered base list
        safe_meds.extend(filtered_base_meds)
        
        print(f"🎯 Final safe medications: {safe_meds}")
    
    print("\n" + "="*50)
    print("✅ MEDICATION FILTERING DEBUG COMPLETE")
    
except Exception as e:
    print(f"❌ Error loading medications CSV: {e}")
    import traceback
    traceback.print_exc()
