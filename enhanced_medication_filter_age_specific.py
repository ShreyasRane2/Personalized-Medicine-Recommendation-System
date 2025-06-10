# --- Age-Specific Medical History Filtering Functions ---

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

def get_age_specific_contraindicated_from_dataset(disease, medical_history, age, medications_df):
    """Get age-specific contraindicated medications from dataset based on medical history"""
    contraindicated_meds = []
    
    if medical_history and medical_history.lower() != 'none':
        # Find the disease row in medications dataset
        disease_rows = medications_df[medications_df['Disease'].str.lower() == disease.lower()]
        
        if not disease_rows.empty:
            disease_row = disease_rows.iloc[0]
            history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
            
            # Determine age group
            is_pediatric = age is not None and int(age) < 18
            age_suffix = "_Pediatric" if is_pediatric else "_Adult"
            
            print(f"[DATASET DEBUG] Processing medical history: {history_conditions}")
            print(f"[DATASET DEBUG] Age group: {'Pediatric' if is_pediatric else 'Adult'} (Age: {age})")
            
            # Check each medical condition with age-specific contraindications
            for condition in history_conditions:
                if 'diabetes' in condition:
                    column_name = f'Diabetes_Contraindicated{age_suffix}'
                    if column_name in medications_df.columns:
                        diabetes_contra = parse_medication_list(disease_row[column_name])
                        contraindicated_meds.extend(diabetes_contra)
                        print(f"[DATASET DEBUG] Diabetes contraindicated ({age_suffix}): {diabetes_contra}")
                
                elif 'hypertension' in condition or 'blood pressure' in condition:
                    column_name = f'Hypertension_Contraindicated{age_suffix}'
                    if column_name in medications_df.columns:
                        hypertension_contra = parse_medication_list(disease_row[column_name])
                        contraindicated_meds.extend(hypertension_contra)
                        print(f"[DATASET DEBUG] Hypertension contraindicated ({age_suffix}): {hypertension_contra}")
                
                elif 'heart' in condition or 'cardiac' in condition:
                    column_name = f'Heart_Contraindicated{age_suffix}'
                    if column_name in medications_df.columns:
                        heart_contra = parse_medication_list(disease_row[column_name])
                        contraindicated_meds.extend(heart_contra)
                        print(f"[DATASET DEBUG] Heart contraindicated ({age_suffix}): {heart_contra}")
                
                elif 'kidney' in condition or 'renal' in condition:
                    column_name = f'Kidney_Contraindicated{age_suffix}'
                    if column_name in medications_df.columns:
                        kidney_contra = parse_medication_list(disease_row[column_name])
                        contraindicated_meds.extend(kidney_contra)
                        print(f"[DATASET DEBUG] Kidney contraindicated ({age_suffix}): {kidney_contra}")
                
                elif 'liver' in condition or 'hepatic' in condition:
                    column_name = f'Liver_Contraindicated{age_suffix}'
                    if column_name in medications_df.columns:
                        liver_contra = parse_medication_list(disease_row[column_name])
                        contraindicated_meds.extend(liver_contra)
                        print(f"[DATASET DEBUG] Liver contraindicated ({age_suffix}): {liver_contra}")
    
    # Remove duplicates
    contraindicated_meds = list(set(contraindicated_meds))
    print(f"[DATASET DEBUG] Final age-specific contraindicated medications: {contraindicated_meds}")
    return contraindicated_meds

def get_age_specific_alternatives_from_dataset(disease, medical_history, age, medications_df):
    """Get age-specific safe alternatives from dataset based on medical history"""
    safe_alternatives = []
    
    if medical_history and medical_history.lower() != 'none':
        # Find the disease row in medications dataset
        disease_rows = medications_df[medications_df['Disease'].str.lower() == disease.lower()]
        
        if not disease_rows.empty:
            disease_row = disease_rows.iloc[0]
            history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
            
            # Determine age group
            is_pediatric = age is not None and int(age) < 18
            age_suffix = "_Pediatric" if is_pediatric else "_Adult"
            
            print(f"[DATASET DEBUG] Getting alternatives for medical history: {history_conditions}")
            print(f"[DATASET DEBUG] Age group for alternatives: {'Pediatric' if is_pediatric else 'Adult'}")
            
            # Check each medical condition for age-specific alternatives
            for condition in history_conditions:
                if 'diabetes' in condition:
                    column_name = f'Diabetes_Alternative{age_suffix}'
                    if column_name in medications_df.columns:
                        diabetes_alt = parse_medication_list(disease_row[column_name])
                        safe_alternatives.extend(diabetes_alt)
                        print(f"[DATASET DEBUG] Diabetes alternatives ({age_suffix}): {diabetes_alt}")
                
                elif 'hypertension' in condition or 'blood pressure' in condition:
                    column_name = f'Hypertension_Alternative{age_suffix}'
                    if column_name in medications_df.columns:
                        hypertension_alt = parse_medication_list(disease_row[column_name])
                        safe_alternatives.extend(hypertension_alt)
                        print(f"[DATASET DEBUG] Hypertension alternatives ({age_suffix}): {hypertension_alt}")
                
                elif 'heart' in condition or 'cardiac' in condition:
                    column_name = f'Heart_Alternative{age_suffix}'
                    if column_name in medications_df.columns:
                        heart_alt = parse_medication_list(disease_row[column_name])
                        safe_alternatives.extend(heart_alt)
                        print(f"[DATASET DEBUG] Heart alternatives ({age_suffix}): {heart_alt}")
                
                elif 'kidney' in condition or 'renal' in condition:
                    column_name = f'Kidney_Alternative{age_suffix}'
                    if column_name in medications_df.columns:
                        kidney_alt = parse_medication_list(disease_row[column_name])
                        safe_alternatives.extend(kidney_alt)
                        print(f"[DATASET DEBUG] Kidney alternatives ({age_suffix}): {kidney_alt}")
                
                elif 'liver' in condition or 'hepatic' in condition:
                    column_name = f'Liver_Alternative{age_suffix}'
                    if column_name in medications_df.columns:
                        liver_alt = parse_medication_list(disease_row[column_name])
                        safe_alternatives.extend(liver_alt)
                        print(f"[DATASET DEBUG] Liver alternatives ({age_suffix}): {liver_alt}")
    
    # Remove duplicates
    safe_alternatives = list(set(safe_alternatives))
    print(f"[DATASET DEBUG] Final age-specific safe alternatives: {safe_alternatives}")
    return safe_alternatives

def filter_medications_by_age_specific_dataset(base_medications, disease, medical_history, age, medications_df):
    """Filter medications using age-specific dataset-based contraindications and alternatives"""
    print(f"[AGE-SPECIFIC FILTER DEBUG] Input medications: {base_medications}")
    print(f"[AGE-SPECIFIC FILTER DEBUG] Disease: {disease}")
    print(f"[AGE-SPECIFIC FILTER DEBUG] Medical history: {medical_history}")
    print(f"[AGE-SPECIFIC FILTER DEBUG] Age: {age}")
    
    if not base_medications:
        return ["No medications available for this condition"]
    
    # Determine age group
    is_pediatric = age is not None and int(age) < 18
    age_group = "Pediatric" if is_pediatric else "Adult"
    
    # Get age-specific contraindicated medications from dataset
    contraindicated_meds = get_age_specific_contraindicated_from_dataset(disease, medical_history, age, medications_df)
    
    # Filter out contraindicated medications
    safe_medications = []
    removed_medications = []
    
    for med in base_medications:
        if not med or str(med).strip().lower() in ['nan', 'none', '']:
            continue
            
        med_lower = str(med).lower().strip()
        is_contraindicated = False
        
        # Check if medication is contraindicated based on age-specific dataset
        for contra_med in contraindicated_meds:
            if contra_med.lower() in med_lower or med_lower in contra_med.lower():
                is_contraindicated = True
                removed_medications.append(f"❌ {med} (removed - {age_group} contraindicated per dataset)")
                break
        
        if not is_contraindicated:
            safe_medications.append(f"✅ {med}")
    
    print(f"[AGE-SPECIFIC FILTER DEBUG] Safe medications after filtering: {safe_medications}")
    print(f"[AGE-SPECIFIC FILTER DEBUG] Removed medications: {removed_medications}")
    
    # Get age-specific safe alternatives from dataset
    safe_alternatives = get_age_specific_alternatives_from_dataset(disease, medical_history, age, medications_df)
    
    # Add alternatives with age-specific labels
    for alt in safe_alternatives[:3]:  # Limit to top 3 alternatives
        if alt and alt not in [med.lower() for med in safe_medications]:
            safe_medications.append(f"🔄 {alt} ({age_group} dataset alternative)")
    
    # Add age-specific warnings and guidance
    if age is not None:
        age_int = int(age)
        if age_int < 18:
            safe_medications.append(f"👶 PEDIATRIC (Age {age}): All medications filtered using pediatric-specific contraindications")
            safe_medications.append("👨‍⚕️ SUPERVISION: Adult supervision required for all medications")
            safe_medications.append("⚖️ DOSING: Pediatric dosing required - consult healthcare provider")
        elif age_int > 65:
            safe_medications.append(f"👴 GERIATRIC (Age {age}): Enhanced monitoring recommended")
            safe_medications.append("⚖️ DOSING: Consider dose reduction for elderly patients")
        else:
            safe_medications.append(f"👨‍⚕️ ADULT (Age {age}): Standard adult contraindications applied")
    
    # Add medical history warnings based on age-specific dataset filtering
    if medical_history and medical_history.lower() != 'none':
        history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
        
        warning_messages = []
        if any('diabetes' in condition for condition in history_conditions):
            warning_messages.append(f"🩺 DIABETES ({age_group}): Medications filtered per age-specific dataset contraindications")
        if any('hypertension' in condition or 'blood pressure' in condition for condition in history_conditions):
            warning_messages.append(f"🩺 HYPERTENSION ({age_group}): Medications filtered per age-specific dataset contraindications")
        if any('heart' in condition or 'cardiac' in condition for condition in history_conditions):
            warning_messages.append(f"🩺 HEART ({age_group}): Medications filtered per age-specific dataset contraindications")
        if any('kidney' in condition or 'renal' in condition for condition in history_conditions):
            warning_messages.append(f"🩺 KIDNEY ({age_group}): Medications filtered per age-specific dataset contraindications")
        if any('liver' in condition or 'hepatic' in condition for condition in history_conditions):
            warning_messages.append(f"🩺 LIVER ({age_group}): Medications filtered per age-specific dataset contraindications")
        
        safe_medications.extend(warning_messages)
    
    # Show what was removed for transparency
    if removed_medications:
        safe_medications.append(f"📋 REMOVED MEDICATIONS ({age_group} dataset):")
        safe_medications.extend(removed_medications)
    
    # If no safe medications remain, provide age-specific guidance
    safe_med_count = len([med for med in safe_medications if med.startswith('✅')])
    if safe_med_count == 0:
        return [
            f"⚠️ All standard medications contraindicated per {age_group.lower()} dataset for your medical history.",
            f"🏥 URGENT: Consult your healthcare provider for personalized {age_group.lower()} treatment options.",
            f"👨‍⚕️ Your doctor will prescribe medications that are safe for your specific conditions and age group.",
            f"📊 DATASET: All contraindications based on {age_group.lower()}-specific medical database."
        ]
    
    print(f"[AGE-SPECIFIC FILTER DEBUG] Final filtered medications: {safe_medications}")
    return safe_medications
