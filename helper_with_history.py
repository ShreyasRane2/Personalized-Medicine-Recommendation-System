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
        med_rows = medications[medications['Disease'] == dis]['Medication']
        if not med_rows.empty:
            med_string = med_rows.iloc[0]
            try:
                # Parse the string representation of list into actual list
                med = ast.literal_eval(med_string)
                if not isinstance(med, list):
                    med = [med_string]
                
                # Apply age-specific modifications to medications
                if age is not None:
                    age_int = int(age)
                    if age_int < 18:
                        # Pediatric modifications
                        modified_meds = []
                        for medication in med:
                            if "aspirin" in medication.lower():
                                modified_meds.append("Acetaminophen (Child-safe alternative)")
                            elif "ibuprofen" in medication.lower():
                                modified_meds.append(f"{medication} (Children's Formula)")
                            elif "antibiotic" in medication.lower():
                                modified_meds.append(f"{medication} (Pediatric Dosage)")
                            else:
                                modified_meds.append(f"{medication} (Child-appropriate dosage)")
                        med = modified_meds
                    elif age_int > 65:
                        # Senior modifications
                        modified_meds = []
                        for medication in med:
                            modified_meds.append(f"{medication} (Senior-appropriate dosage)")
                        med = modified_meds
            except (ValueError, SyntaxError):
                med = [med_string]
        else:
            med = ["No medications available"]

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
