# --- Enhanced Helper Function with Medical History and Age ---
def helper_with_history(dis, medical_history=None, age=None):
    try:
        # Get description
        desc_rows = description[description['Disease'] == dis]['Description']
        if not desc_rows.empty:
            desc = " ".join([w for w in desc_rows])
        else:
            desc = "No description available for this disease."

        # Get precautions
        pre_rows = precautions[precautions['Disease'] == dis][['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']]
        if not pre_rows.empty:
            pre = [col for col in pre_rows.values]
        else:
            pre = [["No precautions available"]]

        # Get medications - FIXED with age consideration
        if not medications.empty:
            print(f"[DEBUG] Looking for disease: {dis}")
            
            # Try exact match first
            med_rows = medications[medications['Disease'].str.lower() == dis.lower()]
            
            if med_rows.empty:
                # Try partial match
                med_rows = medications[medications['Disease'].str.contains(dis, case=False, na=False)]
            
            if not med_rows.empty:
                print(f"[DEBUG] Found medication row for: {dis}")
                
                # Check which medication column exists
                if 'Adult_Medication' in medications.columns:
                    med_string = med_rows['Adult_Medication'].iloc[0]
                    print(f"[DEBUG] Using Adult_Medication: {med_string}")
                elif 'Medication' in medications.columns:
                    med_string = med_rows['Medication'].iloc[0]
                    print(f"[DEBUG] Using Medication: {med_string}")
                else:
                    med_string = "No medication column found"
                
                # Parse medication string
                try:
                    if pd.isna(med_string) or str(med_string).lower() in ['nan', 'none', '']:
                        med = ["No specific medications available for this condition"]
                    else:
                        # Try to parse as list
                        med = ast.literal_eval(str(med_string))
                        if not isinstance(med, list):
                            med = [str(med_string)]
                        print(f"[DEBUG] Parsed medications: {med}")
                except (ValueError, SyntaxError) as e:
                    print(f"[DEBUG] Parsing error: {e}, using raw string")
                    med = [str(med_string)]
                
                # Apply age-specific modifications to medications
                if age is not None:
                    age_int = int(age)
                    print(f"[DEBUG] Applying age modifications for age: {age_int}")
                    
                    if age_int < 18:
                        # Pediatric modifications
                        modified_meds = []
                        for medication in med:
                            med_lower = medication.lower()
                            if "aspirin" in med_lower:
                                modified_meds.append("⚠️ PEDIATRIC ALERT: Acetaminophen (Child-safe alternative to aspirin)")
                            elif "ibuprofen" in med_lower:
                                modified_meds.append(f"👶 CHILD DOSAGE: {medication} (Children's Formula - consult pediatrician for proper dosing)")
                            elif "antibiotic" in med_lower:
                                modified_meds.append(f"👶 PEDIATRIC: {medication} (Pediatric Dosage - weight-based dosing required)")
                            elif any(adult_term in med_lower for adult_term in ['adult', 'mg', 'tablet']):
                                modified_meds.append(f"👶 CHILD VERSION: {medication} (Child-appropriate dosage - consult pediatrician)")
                            else:
                                modified_meds.append(f"👶 PEDIATRIC: {medication} (Child-appropriate dosage required)")
                        med = modified_meds
                        print(f"[DEBUG] Pediatric medications: {med}")
                        
                    elif age_int >= 18:
                        # Adult medications (18+)
                        modified_meds = []
                        for medication in med:
                            if age_int > 65:
                                # Senior modifications
                                modified_meds.append(f"👴 SENIOR DOSAGE: {medication} (Senior-appropriate dosage - may require adjustment)")
                            else:
                                # Regular adult dosage
                                modified_meds.append(f"👨 ADULT: {medication}")
                        med = modified_meds
                        print(f"[DEBUG] Adult medications: {med}")
            else:
                print(f"[DEBUG] No medication found for disease: {dis}")
                if age is not None and int(age) < 18:
                    med = [f"👶 PEDIATRIC ALERT: No specific medications found for {dis}. Please consult a pediatrician for age-appropriate treatment."]
                else:
                    med = [f"No specific medications found for {dis}. Please consult a healthcare provider."]
        else:
            med = ["Medication database not available"]

        # Get diet recommendations - FIXED
        die_rows = diets[diets['Disease'] == dis]['Diet']
        if not die_rows.empty:
            die_string = die_rows.iloc[0]
            try:
                die = ast.literal_eval(die_string)
                if not isinstance(die, list):
                    die = [die_string]
            except (ValueError, SyntaxError):
                die = [die_string]
        else:
            die = ["No diet recommendations available"]

        # Get workout recommendations
        wrkout_rows = workout[workout['disease'] == dis]['workout']
        if not wrkout_rows.empty:
            wrkout = [w for w in wrkout_rows.values]
        else:
            wrkout = ["No workout recommendations available"]

        # Add personalized recommendations based on medical history
        personalized_notes = []
        if medical_history and medical_history.lower() != 'none':
            history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
            
            # Add specific warnings and recommendations
            if any('diabetes' in condition for condition in history_conditions):
                personalized_notes.append("⚠️ DIABETES ALERT: Monitor blood sugar levels closely. Consult your endocrinologist before starting new medications.")
                if any('sugar' in d.lower() or 'sweet' in d.lower() for d in die):
                    personalized_notes.append("🍎 DIET MODIFICATION: Avoid high-sugar foods due to your diabetes history.")
            
            if any('hypertension' in condition for condition in history_conditions):
                personalized_notes.append("⚠️ HYPERTENSION ALERT: Monitor blood pressure regularly. Limit sodium intake.")
                personalized_notes.append("💊 MEDICATION CAUTION: Some medications may affect blood pressure. Consult your cardiologist.")
            
            if any('heart' in condition for condition in history_conditions):
                personalized_notes.append("❤️ HEART CONDITION: Avoid strenuous exercise without medical supervision.")
                personalized_notes.append("🚫 ACTIVITY RESTRICTION: Modify workout recommendations based on your cardiac capacity.")
            
            if any('kidney' in condition for condition in history_conditions):
                personalized_notes.append("🫘 KIDNEY ALERT: Monitor protein intake and stay hydrated. Some medications may need dose adjustment.")
            
            if any('liver' in condition for condition in history_conditions):
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
        print(f"Error in helper function: {e}")
        return ("Error retrieving information", 
                [["No precautions available"]], 
                ["No medications available"], 
                ["No diet recommendations available"], 
                ["No workout recommendations available"],
                [])
