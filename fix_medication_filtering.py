# Create a fixed version of the helper function with better debugging

def helper_with_history_fixed(dis, medical_history=None, age=None):
    """Fixed version of helper function with better medication filtering"""
    import pandas as pd
    import ast
    
    print(f"[HELPER DEBUG] Processing disease: {dis}")
    print(f"[HELPER DEBUG] Age: {age}, Medical History: {medical_history}")
    
    try:
        # Load datasets
        medications = pd.read_csv("datasets/medications.csv")
        description = pd.read_csv("datasets/description.csv")
        precautions = pd.read_csv("datasets/precautions_df.csv")
        diets = pd.read_csv("datasets/diets.csv")
        workout = pd.read_csv("datasets/workout_df.csv")
        
        def parse_medication_list(med_string):
            """Parse medication string into a list with better error handling"""
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
        
        # Get description
        desc_rows = description[description['Disease'].str.lower() == dis.lower()]
        if not desc_rows.empty:
            desc = desc_rows['Description'].iloc[0]
        else:
            desc = "No description available for this disease."
        
        # Get precautions
        pre_rows = precautions[precautions['Disease'].str.lower() == dis.lower()]
        if not pre_rows.empty:
            pre = [col for col in pre_rows[['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']].values]
        else:
            pre = [["No precautions available"]]
        
        # Get medications with improved filtering
        print(f"[MEDICATION DEBUG] Looking for disease: {dis}")
        
        # Try exact match first
        med_rows = medications[medications['Disease'].str.lower() == dis.lower()]
        
        if med_rows.empty:
            # Try partial match
            med_rows = medications[medications['Disease'].str.contains(dis, case=False, na=False)]
        
        if not med_rows.empty:
            print(f"[MEDICATION DEBUG] Found medication row for: {dis}")
            med_row = med_rows.iloc[0]
            
            # Determine base medication list based on age
            if age is not None and int(age) < 18:
                # Use pediatric medications if available
                if 'Pediatric_Medication' in medications.columns:
                    base_meds = parse_medication_list(med_row['Pediatric_Medication'])
                    print(f"[MEDICATION DEBUG] Using Pediatric_Medication: {base_meds}")
                else:
                    base_meds = parse_medication_list(med_row['Adult_Medication'])
                    print(f"[MEDICATION DEBUG] Using Adult_Medication for pediatric: {base_meds}")
            else:
                # Use adult medications
                base_meds = parse_medication_list(med_row['Adult_Medication'])
                print(f"[MEDICATION DEBUG] Using Adult_Medication: {base_meds}")
            
            # Apply medical history filtering
            if medical_history and medical_history.lower() != 'none':
                history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
                print(f"[MEDICATION DEBUG] Medical history conditions: {history_conditions}")
                
                safe_meds = []
                alternatives_added = []
                filtered_base_meds = base_meds.copy()
                
                # Apply filtering for each condition
                for condition in history_conditions:
                    print(f"[MEDICATION DEBUG] Processing condition: {condition}")
                    
                    if 'diabetes' in condition:
                        # Remove diabetes contraindicated medications
                        contraindicated = parse_medication_list(med_row.get('Diabetes_Contraindicated', ''))
                        print(f"[MEDICATION DEBUG] Diabetes contraindicated: {contraindicated}")
                        
                        if contraindicated:
                            original_count = len(filtered_base_meds)
                            filtered_base_meds = [med for med in filtered_base_meds 
                                                if not any(contra.lower() in med.lower() for contra in contraindicated)]
                            print(f"[MEDICATION DEBUG] Removed {original_count - len(filtered_base_meds)} diabetes contraindicated meds")
                        
                        # Add diabetes alternatives
                        alternatives = parse_medication_list(med_row.get('Diabetes_Alternative', ''))
                        print(f"[MEDICATION DEBUG] Diabetes alternatives: {alternatives}")
                        
                        for alt in alternatives:
                            if alt and alt not in alternatives_added:
                                safe_meds.append(f"{alt} (Diabetes-safe)")
                                alternatives_added.append(alt)
                    
                    elif 'hypertension' in condition or 'blood pressure' in condition:
                        # Remove hypertension contraindicated medications
                        contraindicated = parse_medication_list(med_row.get('Hypertension_Contraindicated', ''))
                        print(f"[MEDICATION DEBUG] Hypertension contraindicated: {contraindicated}")
                        
                        if contraindicated:
                            original_count = len(filtered_base_meds)
                            filtered_base_meds = [med for med in filtered_base_meds 
                                                if not any(contra.lower() in med.lower() for contra in contraindicated)]
                            print(f"[MEDICATION DEBUG] Removed {original_count - len(filtered_base_meds)} hypertension contraindicated meds")
                        
                        # Add hypertension alternatives
                        alternatives = parse_medication_list(med_row.get('Hypertension_Alternative', ''))
                        print(f"[MEDICATION DEBUG] Hypertension alternatives: {alternatives}")
                        
                        for alt in alternatives:
                            if alt and alt not in alternatives_added:
                                safe_meds.append(f"{alt} (Blood pressure-safe)")
                                alternatives_added.append(alt)
                    
                    elif 'heart' in condition or 'cardiac' in condition:
                        # Remove heart contraindicated medications
                        contraindicated = parse_medication_list(med_row.get('Heart_Contraindicated', ''))
                        print(f"[MEDICATION DEBUG] Heart contraindicated: {contraindicated}")
                        
                        if contraindicated:
                            original_count = len(filtered_base_meds)
                            filtered_base_meds = [med for med in filtered_base_meds 
                                                if not any(contra.lower() in med.lower() for contra in contraindicated)]
                            print(f"[MEDICATION DEBUG] Removed {original_count - len(filtered_base_meds)} heart contraindicated meds")
                        
                        # Add heart alternatives
                        alternatives = parse_medication_list(med_row.get('Heart_Alternative', ''))
                        print(f"[MEDICATION DEBUG] Heart alternatives: {alternatives}")
                        
                        for alt in alternatives:
                            if alt and alt not in alternatives_added:
                                safe_meds.append(f"{alt} (Heart-safe)")
                                alternatives_added.append(alt)
                    
                    elif 'kidney' in condition or 'renal' in condition:
                        # Remove kidney contraindicated medications
                        contraindicated = parse_medication_list(med_row.get('Kidney_Contraindicated', ''))
                        print(f"[MEDICATION DEBUG] Kidney contraindicated: {contraindicated}")
                        
                        if contraindicated:
                            original_count = len(filtered_base_meds)
                            filtered_base_meds = [med for med in filtered_base_meds 
                                                if not any(contra.lower() in med.lower() for contra in contraindicated)]
                            print(f"[MEDICATION DEBUG] Removed {original_count - len(filtered_base_meds)} kidney contraindicated meds")
                        
                        # Add kidney alternatives
                        alternatives = parse_medication_list(med_row.get('Kidney_Alternative', ''))
                        print(f"[MEDICATION DEBUG] Kidney alternatives: {alternatives}")
                        
                        for alt in alternatives:
                            if alt and alt not in alternatives_added:
                                safe_meds.append(f"{alt} (Kidney-safe)")
                                alternatives_added.append(alt)
                    
                    elif 'liver' in condition or 'hepatic' in condition:
                        # Remove liver contraindicated medications
                        contraindicated = parse_medication_list(med_row.get('Liver_Contraindicated', ''))
                        print(f"[MEDICATION DEBUG] Liver contraindicated: {contraindicated}")
                        
                        if contraindicated:
                            original_count = len(filtered_base_meds)
                            filtered_base_meds = [med for med in filtered_base_meds 
                                                if not any(contra.lower() in med.lower() for contra in contraindicated)]
                            print(f"[MEDICATION DEBUG] Removed {original_count - len(filtered_base_meds)} liver contraindicated meds")
                        
                        # Add liver alternatives
                        alternatives = parse_medication_list(med_row.get('Liver_Alternative', ''))
                        print(f"[MEDICATION DEBUG] Liver alternatives: {alternatives}")
                        
                        for alt in alternatives:
                            if alt and alt not in alternatives_added:
                                safe_meds.append(f"{alt} (Liver-safe)")
                                alternatives_added.append(alt)
                
                # Add remaining safe medications from filtered base list
                safe_meds.extend(filtered_base_meds)
                
                # If no safe medications remain, provide guidance
                if not safe_meds:
                    safe_meds = [
                        "⚠️ Standard medications for this condition require medical review due to your medical history.",
                        "Please consult your healthcare provider for personalized treatment options.",
                        "Your doctor will prescribe medications that are safe for your specific conditions."
                    ]
                else:
                    # Add informational note about filtering
                    safe_meds.append("✅ All medications above are safe for your medical conditions")
                
                med = safe_meds
                print(f"[MEDICATION DEBUG] Final filtered medications: {med}")
            else:
                # No medical history - use all base medications
                med = base_meds
                print(f"[MEDICATION DEBUG] No medical history, using base medications: {med}")
        else:
            print(f"[MEDICATION DEBUG] No medication found for disease: {dis}")
            med = [f"No specific medications found for {dis}. Please consult a healthcare provider."]
        
        # Get diet recommendations
        die_rows = diets[diets['Disease'].str.lower() == dis.lower()]
        if not die_rows.empty:
            die_string = die_rows['Diet'].iloc[0]
            try:
                if pd.isna(die_string):
                    die = ["No specific diet recommendations available"]
                else:
                    die = ast.literal_eval(str(die_string))
                    if not isinstance(die, list):
                        die = [str(die_string)]
            except (ValueError, SyntaxError):
                die = [str(die_string)]
        else:
            die = ["No diet recommendations available"]
        
        # Get workout recommendations
        wrkout_rows = workout[workout['disease'].str.lower() == dis.lower()]
        if not wrkout_rows.empty:
            wrkout = [str(wrkout_rows['workout'].iloc[0])]
        else:
            wrkout = ["No workout recommendations available"]
        
        # Add personalized notes
        personalized_notes = []
        if medical_history and medical_history.lower() != 'none':
            history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
            
            if any('diabetes' in condition for condition in history_conditions):
                personalized_notes.append("⚠️ DIABETES ALERT: Monitor blood sugar levels closely. Consult your endocrinologist before starting new medications.")
            
            if any('hypertension' in condition or 'blood pressure' in condition for condition in history_conditions):
                personalized_notes.append("⚠️ HYPERTENSION ALERT: Monitor blood pressure regularly. Limit sodium intake.")
            
            if any('heart' in condition or 'cardiac' in condition for condition in history_conditions):
                personalized_notes.append("❤️ HEART CONDITION: Avoid strenuous exercise without medical supervision.")
            
            if any('kidney' in condition or 'renal' in condition for condition in history_conditions):
                personalized_notes.append("🫘 KIDNEY ALERT: Monitor protein intake and stay hydrated. Some medications may need dose adjustment.")
            
            if any('liver' in condition or 'hepatic' in condition for condition in history_conditions):
                personalized_notes.append("🫀 LIVER CAUTION: Avoid alcohol and medications that may stress the liver.")
        
        # Add age-specific alerts
        if age is not None:
            age_int = int(age)
            if age_int < 18:
                personalized_notes.append(f"👶 PEDIATRIC PATIENT: Age {age} - All medications are adjusted for pediatric dosing. Adult supervision required.")
            elif age_int > 65:
                personalized_notes.append(f"👴 SENIOR PATIENT: Age {age} - Consider reduced dosages and increased monitoring due to age-related changes.")
        
        return desc, pre, med, die, wrkout, personalized_notes
        
    except Exception as e:
        print(f"Error in helper_with_history_fixed function: {e}")
        import traceback
        traceback.print_exc()
        return ("Error retrieving information", 
                [["No precautions available"]], 
                ["Error retrieving medications"], 
                ["No diet recommendations available"], 
                ["No workout recommendations available"],
                [])

# Test the fixed function
print("🧪 TESTING FIXED HELPER FUNCTION")
print("="*50)

# Test case 1: Diabetes patient
print("\n👤 Test Case 1: Diabetes Patient")
desc, pre, med, die, wrkout, notes = helper_with_history_fixed("Diabetes", "diabetes", 45)
print(f"✅ Medications returned: {med}")
print(f"✅ Personalized notes: {notes}")

print("\n" + "="*50)

# Test case 2: Hypertension patient  
print("\n👤 Test Case 2: Hypertension Patient")
desc, pre, med, die, wrkout, notes = helper_with_history_fixed("Hypertension", "hypertension", 55)
print(f"✅ Medications returned: {med}")
print(f"✅ Personalized notes: {notes}")

print("\n" + "="*50)

# Test case 3: Multiple conditions
print("\n👤 Test Case 3: Multiple Conditions (Diabetes + Heart Disease)")
desc, pre, med, die, wrkout, notes = helper_with_history_fixed("Diabetes", "diabetes, heart disease", 65)
print(f"✅ Medications returned: {med}")
print(f"✅ Personalized notes: {notes}")

print("\n✅ FIXED HELPER FUNCTION TESTING COMPLETE")
