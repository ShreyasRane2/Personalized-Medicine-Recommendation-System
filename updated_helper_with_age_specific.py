# --- Updated Helper Function with Age-Specific Dataset Filtering ---

def helper_with_history_age_specific(dis, medical_history=None, age=None):
    """Enhanced helper function with age-specific dataset-based medication filtering"""
    try:
        print(f"[HELPER DEBUG] Processing disease: {dis}")
        print(f"[HELPER DEBUG] Age: {age}, Medical History: {medical_history}")
        
        # Get description
        if not description.empty:
            desc_rows = description[description['Disease'].str.lower() == dis.lower()]
            if not desc_rows.empty:
                desc = desc_rows['Description'].iloc[0]
            else:
                desc = "No description available for this disease."
        else:
            desc = "No description available for this disease."

        # Get precautions
        if not precautions.empty:
            pre_rows = precautions[precautions['Disease'].str.lower() == dis.lower()]
            if not pre_rows.empty:
                pre = [col for col in pre_rows[['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']].values]
            else:
                pre = [["No precautions available"]]
        else:
            pre = [["No precautions available"]]

        # Get age-appropriate base medications from dataset
        base_medications = []
        if not medications.empty:
            print(f"[MEDICATION DEBUG] Looking for disease: {dis}")
            
            # Try exact match first
            med_rows = medications[medications['Disease'].str.lower() == dis.lower()]
            
            if med_rows.empty:
                # Try partial match
                med_rows = medications[medications['Disease'].str.contains(dis, case=False, na=False)]
            
            if not med_rows.empty:
                print(f"[MEDICATION DEBUG] Found medication row for: {dis}")
                med_row = med_rows.iloc[0]
                
                # Check available columns and use age-appropriate medication list
                available_columns = medications.columns.tolist()
                print(f"[MEDICATION DEBUG] Available columns: {available_columns}")
                
                # Determine base medication list based on age
                if age is not None and int(age) < 18:
                    # Use pediatric medications if available
                    if 'Pediatric_Medication' in available_columns:
                        base_medications = parse_medication_list(med_row['Pediatric_Medication'])
                        print(f"[MEDICATION DEBUG] Using Pediatric_Medication: {base_medications}")
                    elif 'Adult_Medication' in available_columns:
                        base_medications = parse_medication_list(med_row['Adult_Medication'])
                        print(f"[MEDICATION DEBUG] Using Adult_Medication for pediatric (will be filtered): {base_medications}")
                    elif 'Medication' in available_columns:
                        base_medications = parse_medication_list(med_row['Medication'])
                        print(f"[MEDICATION DEBUG] Using general Medication for pediatric (will be filtered): {base_medications}")
                else:
                    # Use adult medications or general medications
                    if 'Adult_Medication' in available_columns:
                        base_medications = parse_medication_list(med_row['Adult_Medication'])
                        print(f"[MEDICATION DEBUG] Using Adult_Medication: {base_medications}")
                    elif 'Medication' in available_columns:
                        base_medications = parse_medication_list(med_row['Medication'])
                        print(f"[MEDICATION DEBUG] Using general Medication: {base_medications}")
            else:
                print(f"[MEDICATION DEBUG] No medication found for disease: {dis}")
                base_medications = [f"Standard treatment for {dis} - consult healthcare provider"]
        else:
            base_medications = ["Medication database not available"]

        # Apply age-specific dataset-based medical history filtering
        filtered_medications = filter_medications_by_age_specific_dataset(
            base_medications, dis, medical_history, age, medications
        )

        # Get diet recommendations
        if not diets.empty:
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
        else:
            die = ["No diet recommendations available"]

        # Get workout recommendations
        if not workout.empty:
            wrkout_rows = workout[workout['disease'].str.lower() == dis.lower()]
            if not wrkout_rows.empty:
                wrkout = [str(wrkout_rows['workout'].iloc[0])]
            else:
                wrkout = ["No workout recommendations available"]
        else:
            wrkout = ["No workout recommendations available"]

        # Generate age-specific personalized notes based on dataset filtering
        personalized_notes = []
        
        # Age-specific notes
        if age is not None:
            age_int = int(age)
            if age_int < 18:
                personalized_notes.extend([
                    f"👶 PEDIATRIC PATIENT (Age {age}): All recommendations use pediatric-specific dataset",
                    "🔍 FILTERING: Medications filtered using pediatric contraindication database",
                    "👨‍⚕️ SUPERVISION: Adult supervision required for all treatments"
                ])
            elif age_int > 65:
                personalized_notes.extend([
                    f"👴 GERIATRIC PATIENT (Age {age}): Enhanced monitoring recommended",
                    "🔍 FILTERING: Medications filtered using adult contraindication database",
                    "⚖️ DOSING: Consider dose adjustments for elderly patients"
                ])
            else:
                personalized_notes.extend([
                    f"👨‍⚕️ ADULT PATIENT (Age {age}): Standard adult treatment protocols",
                    "🔍 FILTERING: Medications filtered using adult contraindication database"
                ])
        
        # Medical history specific notes
        if medical_history and medical_history.lower() != 'none':
            history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
            age_group = "Pediatric" if (age is not None and int(age) < 18) else "Adult"
            
            # Add notes based on what was filtered from age-specific dataset
            if any('diabetes' in condition for condition in history_conditions):
                personalized_notes.extend([
                    f"⚠️ DIABETES ({age_group}): Medications filtered using {age_group.lower()}-specific diabetes contraindications",
                    "🍎 DIET: Follow age-appropriate diabetes-friendly diet recommendations",
                    f"📊 DATASET: {age_group} diabetes contraindications applied"
                ])
            
            if any('hypertension' in condition or 'blood pressure' in condition for condition in history_conditions):
                personalized_notes.extend([
                    f"⚠️ HYPERTENSION ({age_group}): Medications filtered using {age_group.lower()}-specific hypertension contraindications",
                    "🧂 DIET: Age-appropriate low sodium diet recommendations",
                    f"📊 DATASET: {age_group} hypertension contraindications applied"
                ])
            
            if any('heart' in condition or 'cardiac' in condition for condition in history_conditions):
                personalized_notes.extend([
                    f"❤️ HEART ({age_group}): Medications filtered using {age_group.lower()}-specific cardiac contraindications",
                    "🏃 EXERCISE: Age-appropriate cardiac exercise guidelines",
                    f"📊 DATASET: {age_group} cardiac contraindications applied"
                ])
            
            if any('kidney' in condition or 'renal' in condition for condition in history_conditions):
                personalized_notes.extend([
                    f"🫘 KIDNEY ({age_group}): Medications filtered using {age_group.lower()}-specific renal contraindications",
                    "💧 HYDRATION: Age-appropriate kidney-safe hydration guidelines",
                    f"📊 DATASET: {age_group} renal contraindications applied"
                ])
            
            if any('liver' in condition or 'hepatic' in condition for condition in history_conditions):
                personalized_notes.extend([
                    f"🫀 LIVER ({age_group}): Medications filtered using {age_group.lower()}-specific hepatic contraindications",
                    "🚫 SUBSTANCES: Age-appropriate liver protection guidelines",
                    f"📊 DATASET: {age_group} hepatic contraindications applied"
                ])

        print(f"[HELPER DEBUG] Final age-specific dataset-filtered medications: {filtered_medications}")
        print(f"[HELPER DEBUG] Final age-specific personalized notes: {personalized_notes}")
        
        return desc, pre, filtered_medications, die, wrkout, personalized_notes
    
    except Exception as e:
        print(f"Error in helper_with_history_age_specific function: {e}")
        import traceback
        traceback.print_exc()
        return ("Error retrieving information", 
                [["No precautions available"]], 
                ["Error retrieving medications - consult healthcare provider"], 
                ["No diet recommendations available"], 
                ["No workout recommendations available"],
                ["⚠️ Error in processing age-specific dataset - consult healthcare provider"])
