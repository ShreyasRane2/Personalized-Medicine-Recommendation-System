# --- Updated Helper Function Using Dataset-Based Filtering ---

def helper_with_history(dis, medical_history=None, age=None):
    """Enhanced helper function with dataset-based medication filtering"""
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

        # Get base medications from dataset
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
                
                # Check available columns and use appropriate medication list
                available_columns = medications.columns.tolist()
                print(f"[MEDICATION DEBUG] Available columns: {available_columns}")
                
                # Determine base medication list based on age and available columns
                if age is not None and int(age) < 18:
                    # Use pediatric medications if available
                    if 'Pediatric_Medication' in available_columns:
                        base_medications = parse_medication_list(med_row['Pediatric_Medication'])
                        print(f"[MEDICATION DEBUG] Using Pediatric_Medication: {base_medications}")
                    elif 'Adult_Medication' in available_columns:
                        base_medications = parse_medication_list(med_row['Adult_Medication'])
                        print(f"[MEDICATION DEBUG] Using Adult_Medication for pediatric: {base_medications}")
                    elif 'Medication' in available_columns:
                        base_medications = parse_medication_list(med_row['Medication'])
                        print(f"[MEDICATION DEBUG] Using general Medication for pediatric: {base_medications}")
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

        # Apply dataset-based medical history filtering
        filtered_medications = filter_medications_by_dataset(
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

        # Generate personalized notes based on dataset filtering
        personalized_notes = []
        if medical_history and medical_history.lower() != 'none':
            history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
            
            # Add notes based on what was filtered from dataset
            if any('diabetes' in condition for condition in history_conditions):
                personalized_notes.extend([
                    "⚠️ DIABETES: Medications filtered based on dataset contraindications",
                    "🍎 DIET: Follow diabetes-friendly diet recommendations",
                    "📊 DATASET: All filtering based on medical database"
                ])
            
            if any('hypertension' in condition or 'blood pressure' in condition for condition in history_conditions):
                personalized_notes.extend([
                    "⚠️ HYPERTENSION: Medications filtered based on dataset contraindications",
                    "🧂 DIET: Low sodium diet as per medical guidelines",
                    "📊 DATASET: All filtering based on medical database"
                ])
            
            if any('heart' in condition or 'cardiac' in condition for condition in history_conditions):
                personalized_notes.extend([
                    "❤️ HEART: Medications filtered based on dataset contraindications",
                    "🏃 EXERCISE: Modified exercise as per cardiac guidelines",
                    "📊 DATASET: All filtering based on medical database"
                ])
            
            if any('kidney' in condition or 'renal' in condition for condition in history_conditions):
                personalized_notes.extend([
                    "🫘 KIDNEY: Medications filtered based on dataset contraindications",
                    "💧 HYDRATION: Follow kidney-safe hydration guidelines",
                    "📊 DATASET: All filtering based on medical database"
                ])
            
            if any('liver' in condition or 'hepatic' in condition for condition in history_conditions):
                personalized_notes.extend([
                    "🫀 LIVER: Medications filtered based on dataset contraindications",
                    "🚫 ALCOHOL: Avoid alcohol as per liver guidelines",
                    "📊 DATASET: All filtering based on medical database"
                ])

        # Add age-specific alerts
        if age is not None:
            age_int = int(age)
            if age_int < 18:
                personalized_notes.extend([
                    f"👶 PEDIATRIC: Age {age} - Dataset-based pediatric medication selection",
                    "👨‍⚕️ SUPERVISION: Adult supervision required for all medications"
                ])
            elif age_int > 65:
                personalized_notes.extend([
                    f"👴 GERIATRIC: Age {age} - Dataset-based geriatric considerations",
                    "🩺 MONITORING: Enhanced monitoring per age guidelines"
                ])

        print(f"[HELPER DEBUG] Final dataset-filtered medications: {filtered_medications}")
        print(f"[HELPER DEBUG] Final personalized notes: {personalized_notes}")
        
        return desc, pre, filtered_medications, die, wrkout, personalized_notes
    
    except Exception as e:
        print(f"Error in helper_with_history function: {e}")
        import traceback
        traceback.print_exc()
        return ("Error retrieving information", 
                [["No precautions available"]], 
                ["Error retrieving medications - consult healthcare provider"], 
                ["No diet recommendations available"], 
                ["No workout recommendations available"],
                ["⚠️ Error in processing dataset - consult healthcare provider"])
