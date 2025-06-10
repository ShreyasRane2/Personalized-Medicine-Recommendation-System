# --- Dataset-Based Medication Filtering Functions ---

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

def get_contraindicated_from_dataset(disease, medical_history, medications_df):
    """Get contraindicated medications from dataset based on medical history"""
    contraindicated_meds = []
    
    if medical_history and medical_history.lower() != 'none':
        # Find the disease row in medications dataset
        disease_rows = medications_df[medications_df['Disease'].str.lower() == disease.lower()]
        
        if not disease_rows.empty:
            disease_row = disease_rows.iloc[0]
            history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
            
            print(f"[DATASET DEBUG] Processing medical history: {history_conditions}")
            
            # Check each medical condition
            for condition in history_conditions:
                if 'diabetes' in condition:
                    if 'Diabetes_Contraindicated' in medications_df.columns:
                        diabetes_contra = parse_medication_list(disease_row['Diabetes_Contraindicated'])
                        contraindicated_meds.extend(diabetes_contra)
                        print(f"[DATASET DEBUG] Diabetes contraindicated: {diabetes_contra}")
                
                elif 'hypertension' in condition or 'blood pressure' in condition:
                    if 'Hypertension_Contraindicated' in medications_df.columns:
                        hypertension_contra = parse_medication_list(disease_row['Hypertension_Contraindicated'])
                        contraindicated_meds.extend(hypertension_contra)
                        print(f"[DATASET DEBUG] Hypertension contraindicated: {hypertension_contra}")
                
                elif 'heart' in condition or 'cardiac' in condition:
                    if 'Heart_Contraindicated' in medications_df.columns:
                        heart_contra = parse_medication_list(disease_row['Heart_Contraindicated'])
                        contraindicated_meds.extend(heart_contra)
                        print(f"[DATASET DEBUG] Heart contraindicated: {heart_contra}")
                
                elif 'kidney' in condition or 'renal' in condition:
                    if 'Kidney_Contraindicated' in medications_df.columns:
                        kidney_contra = parse_medication_list(disease_row['Kidney_Contraindicated'])
                        contraindicated_meds.extend(kidney_contra)
                        print(f"[DATASET DEBUG] Kidney contraindicated: {kidney_contra}")
                
                elif 'liver' in condition or 'hepatic' in condition:
                    if 'Liver_Contraindicated' in medications_df.columns:
                        liver_contra = parse_medication_list(disease_row['Liver_Contraindicated'])
                        contraindicated_meds.extend(liver_contra)
                        print(f"[DATASET DEBUG] Liver contraindicated: {liver_contra}")
    
    # Remove duplicates
    contraindicated_meds = list(set(contraindicated_meds))
    print(f"[DATASET DEBUG] Final contraindicated medications: {contraindicated_meds}")
    return contraindicated_meds

def get_alternatives_from_dataset(disease, medical_history, medications_df):
    """Get safe alternatives from dataset based on medical history"""
    safe_alternatives = []
    
    if medical_history and medical_history.lower() != 'none':
        # Find the disease row in medications dataset
        disease_rows = medications_df[medications_df['Disease'].str.lower() == disease.lower()]
        
        if not disease_rows.empty:
            disease_row = disease_rows.iloc[0]
            history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
            
            print(f"[DATASET DEBUG] Getting alternatives for medical history: {history_conditions}")
            
            # Check each medical condition for alternatives
            for condition in history_conditions:
                if 'diabetes' in condition:
                    if 'Diabetes_Alternative' in medications_df.columns:
                        diabetes_alt = parse_medication_list(disease_row['Diabetes_Alternative'])
                        safe_alternatives.extend(diabetes_alt)
                        print(f"[DATASET DEBUG] Diabetes alternatives: {diabetes_alt}")
                
                elif 'hypertension' in condition or 'blood pressure' in condition:
                    if 'Hypertension_Alternative' in medications_df.columns:
                        hypertension_alt = parse_medication_list(disease_row['Hypertension_Alternative'])
                        safe_alternatives.extend(hypertension_alt)
                        print(f"[DATASET DEBUG] Hypertension alternatives: {hypertension_alt}")
                
                elif 'heart' in condition or 'cardiac' in condition:
                    if 'Heart_Alternative' in medications_df.columns:
                        heart_alt = parse_medication_list(disease_row['Heart_Alternative'])
                        safe_alternatives.extend(heart_alt)
                        print(f"[DATASET DEBUG] Heart alternatives: {heart_alt}")
                
                elif 'kidney' in condition or 'renal' in condition:
                    if 'Kidney_Alternative' in medications_df.columns:
                        kidney_alt = parse_medication_list(disease_row['Kidney_Alternative'])
                        safe_alternatives.extend(kidney_alt)
                        print(f"[DATASET DEBUG] Kidney alternatives: {kidney_alt}")
                
                elif 'liver' in condition or 'hepatic' in condition:
                    if 'Liver_Alternative' in medications_df.columns:
                        liver_alt = parse_medication_list(disease_row['Liver_Alternative'])
                        safe_alternatives.extend(liver_alt)
                        print(f"[DATASET DEBUG] Liver alternatives: {liver_alt}")
    
    # Remove duplicates
    safe_alternatives = list(set(safe_alternatives))
    print(f"[DATASET DEBUG] Final safe alternatives: {safe_alternatives}")
    return safe_alternatives

def filter_medications_by_dataset(base_medications, disease, medical_history, age, medications_df):
    """Filter medications using dataset-based contraindications and alternatives"""
    print(f"[DATASET FILTER DEBUG] Input medications: {base_medications}")
    print(f"[DATASET FILTER DEBUG] Disease: {disease}")
    print(f"[DATASET FILTER DEBUG] Medical history: {medical_history}")
    print(f"[DATASET FILTER DEBUG] Age: {age}")
    
    if not base_medications:
        return ["No medications available for this condition"]
    
    # Get contraindicated medications from dataset
    contraindicated_meds = get_contraindicated_from_dataset(disease, medical_history, medications_df)
    
    # Filter out contraindicated medications
    safe_medications = []
    removed_medications = []
    
    for med in base_medications:
        if not med or str(med).strip().lower() in ['nan', 'none', '']:
            continue
            
        med_lower = str(med).lower().strip()
        is_contraindicated = False
        
        # Check if medication is contraindicated based on dataset
        for contra_med in contraindicated_meds:
            if contra_med.lower() in med_lower or med_lower in contra_med.lower():
                is_contraindicated = True
                removed_medications.append(f"❌ {med} (removed - contraindicated per dataset)")
                break
        
        if not is_contraindicated:
            safe_medications.append(f"✅ {med}")
    
    print(f"[DATASET FILTER DEBUG] Safe medications after filtering: {safe_medications}")
    print(f"[DATASET FILTER DEBUG] Removed medications: {removed_medications}")
    
    # Get safe alternatives from dataset
    safe_alternatives = get_alternatives_from_dataset(disease, medical_history, medications_df)
    
    # Add alternatives with labels
    for alt in safe_alternatives[:3]:  # Limit to top 3 alternatives
        if alt and alt not in [med.lower() for med in safe_medications]:
            safe_medications.append(f"🔄 {alt} (Dataset alternative)")
    
    # Age-specific adjustments (still rule-based as this is universal)
    if age is not None:
        age_int = int(age)
        if age_int < 18:
            # Pediatric adjustments - remove known unsafe medications for children
            pediatric_unsafe = ['aspirin', 'tetracycline', 'doxycycline', 'ciprofloxacin']
            original_count = len(safe_medications)
            safe_medications = [med for med in safe_medications 
                              if not any(unsafe.lower() in str(med).lower() for unsafe in pediatric_unsafe)]
            if len(safe_medications) < original_count:
                safe_medications.append("⚠️ Some medications removed - not safe for children")
            safe_medications.append("👶 All medications require pediatric dosing")
        elif age_int > 65:
            # Geriatric considerations
            safe_medications.append("👴 Consider dose reduction for elderly patients")
    
    # Add medical history warnings based on dataset filtering
    if medical_history and medical_history.lower() != 'none':
        history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
        
        warning_messages = []
        if any('diabetes' in condition for condition in history_conditions):
            warning_messages.append("🩺 DIABETES: Medications filtered per dataset contraindications")
        if any('hypertension' in condition or 'blood pressure' in condition for condition in history_conditions):
            warning_messages.append("🩺 HYPERTENSION: Medications filtered per dataset contraindications")
        if any('heart' in condition or 'cardiac' in condition for condition in history_conditions):
            warning_messages.append("🩺 HEART: Medications filtered per dataset contraindications")
        if any('kidney' in condition or 'renal' in condition for condition in history_conditions):
            warning_messages.append("🩺 KIDNEY: Medications filtered per dataset contraindications")
        if any('liver' in condition or 'hepatic' in condition for condition in history_conditions):
            warning_messages.append("🩺 LIVER: Medications filtered per dataset contraindications")
        
        safe_medications.extend(warning_messages)
    
    # Show what was removed for transparency
    if removed_medications:
        safe_medications.append("📋 REMOVED MEDICATIONS (per dataset):")
        safe_medications.extend(removed_medications)
    
    # If no safe medications remain, provide guidance
    safe_med_count = len([med for med in safe_medications if med.startswith('✅')])
    if safe_med_count == 0:
        return [
            "⚠️ All standard medications contraindicated per dataset for your medical history.",
            "🏥 URGENT: Consult your healthcare provider for personalized treatment options.",
            "👨‍⚕️ Your doctor will prescribe medications that are safe for your specific conditions.",
            "📊 DATASET: All contraindications based on medical database."
        ]
    
    print(f"[DATASET FILTER DEBUG] Final filtered medications: {safe_medications}")
    return safe_medications
