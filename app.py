from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import pymysql
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import ast
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import io
from flask import make_response

# --- Database Connection Helper ---
def get_db_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='shreyasrane',
            database='medicinesystem'
        )
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

pymysql.install_as_MySQLdb()

app = Flask(__name__, template_folder="templates")
app.secret_key = 'shreyasr2559'

# --- Database Schema Setup ---
def setup_database():
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Create users table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    age INT DEFAULT 30,
                    medical_history TEXT DEFAULT 'None'
                )
            """)
            connection.commit()
            
            # Create search_history table as specified
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100),
                    symptoms TEXT,
                    predicted_disease VARCHAR(100),
                    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.commit()
            
            # Keep the predictions table for algorithm comparison data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    symptoms TEXT NOT NULL,
                    predicted_disease VARCHAR(255) NOT NULL,
                    winning_algorithm VARCHAR(50) NOT NULL,
                    confidence FLOAT DEFAULT 0,
                    rf_prediction VARCHAR(255),
                    svc_prediction VARCHAR(255),
                    rf_confidence FLOAT DEFAULT 0,
                    svc_confidence FLOAT DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.commit()
            
            cursor.close()
            connection.close()
            print("Database schema setup completed successfully")
            print("Tables created: users, search_history, predictions")
    except Exception as e:
        print(f"Error setting up database schema: {e}")

# Setup database on startup
setup_database()

# --- Load Data ---
try:
    sym_des = pd.read_csv("datasets/symtoms_df.csv")
    precautions = pd.read_csv("datasets/precautions_df.csv")
    workout = pd.read_csv("datasets/workout_df.csv")
    description = pd.read_csv("datasets/description.csv")
    medications = pd.read_csv("datasets/medications_condition_specific_with_dosage.csv")
    diets = pd.read_csv("datasets/diets.csv")
    
    print("All datasets loaded successfully")
    print("Medications CSV columns:", medications.columns.tolist())
    # print("Sample medications data:")
    # print(medications.head())
    print("Medications shape:", medications.shape)
    print("Unique diseases in condition-specific medications:", medications['Disease'].nunique())
except Exception as e:
    print(f"Error loading datasets: {e}")
    # Create empty dataframes as fallback
    sym_des = pd.DataFrame()
    precautions = pd.DataFrame()
    workout = pd.DataFrame()
    description = pd.DataFrame()
    medications = pd.DataFrame()
    diets = pd.DataFrame()

# Clean symptoms data
if not sym_des.empty:
    if 'Unnamed: 0' in sym_des.columns:
        sym_des.drop(columns=['Unnamed: 0'], inplace=True)
    
    # Ensure we have the right column names
    if len(sym_des.columns) >= 5:
        sym_des.columns = ['Disease', 'Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']
        for col in ['Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']:
            sym_des[col] = sym_des[col].str.strip().str.lower()

# --- Encode Symptoms ---
if not sym_des.empty:
    all_symptoms = pd.unique(sym_des[['Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']].values.ravel())
    all_symptoms = [symptom for symptom in all_symptoms if pd.notna(symptom)]
    symptoms_dict = {symptom: idx for idx, symptom in enumerate(all_symptoms)}

    def encode_symptoms(row):
        vector = np.zeros(len(symptoms_dict))
        for symptom in row:
            if pd.notna(symptom):
                symptom = symptom.strip().lower()
                if symptom in symptoms_dict:
                    vector[symptoms_dict[symptom]] = 1
        return vector

    X = np.array([encode_symptoms(row) for row in sym_des[['Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']].values])
    le = LabelEncoder()
    y = le.fit_transform(sym_des['Disease'])

    # Train both models
    print("Training RandomForest model...")
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X, y)
    
    print("Training SVC model...")
    svc_model = SVC(kernel='rbf', probability=True, random_state=42, gamma='scale')
    svc_model.fit(X, y)
    
    # Evaluate both models (backend only)
    print("Evaluating models...")
    rf_scores = cross_val_score(rf_model, X, y, cv=5)
    svc_scores = cross_val_score(svc_model, X, y, cv=5)
    
    print(f"[BACKEND] RandomForest CV Accuracy: {rf_scores.mean():.3f} (+/- {rf_scores.std() * 2:.3f})")
    print(f"[BACKEND] SVC CV Accuracy: {svc_scores.mean():.3f} (+/- {svc_scores.std() * 2:.3f})")
    
    # Store which algorithm performs better overall
    rf_overall_accuracy = rf_scores.mean()
    svc_overall_accuracy = svc_scores.mean()
    
else:
    symptoms_dict = {}
    rf_model = None
    svc_model = None
    le = None
    rf_overall_accuracy = 0
    svc_overall_accuracy = 0

# --- Smart Algorithm Selection Function ---
def predict_disease_smart_selection(input_symptoms):
    """
    Compare both algorithms and automatically select the one with higher confidence.
    User only sees the best result, not the comparison.
    """
    if rf_model is None or svc_model is None or not symptoms_dict:
        return None
        
    input_data = np.zeros(len(symptoms_dict))
    found_symptom = False

    for symptom in input_symptoms:
        cleaned = symptom.strip().lower()
        if cleaned in symptoms_dict:
            input_data[symptoms_dict[cleaned]] = 1
            found_symptom = True

    if not found_symptom:
        return None

    # Get predictions from both models
    rf_predictions = rf_model.predict_proba([input_data])[0]
    svc_predictions = svc_model.predict_proba([input_data])[0]
    
    # Get top prediction from each model
    rf_top_idx = np.argmax(rf_predictions)
    svc_top_idx = np.argmax(svc_predictions)
    
    rf_disease = le.inverse_transform([rf_top_idx])[0]
    svc_disease = le.inverse_transform([svc_top_idx])[0]
    
    rf_confidence = rf_predictions[rf_top_idx]
    svc_confidence = svc_predictions[svc_top_idx]
    
    # Backend comparison logic
    print(f"[BACKEND COMPARISON]")
    print(f"RandomForest: {rf_disease} (confidence: {rf_confidence:.3f})")
    print(f"SVC: {svc_disease} (confidence: {svc_confidence:.3f})")
    
    # Smart selection logic
    if rf_confidence > svc_confidence:
        # RandomForest has higher confidence
        winning_algorithm = "RandomForest"
        final_disease = rf_disease
        final_confidence = rf_confidence
        print(f"[WINNER] RandomForest selected (higher confidence: {rf_confidence:.3f} vs {svc_confidence:.3f})")
    elif svc_confidence > rf_confidence:
        # SVC has higher confidence
        winning_algorithm = "SVC"
        final_disease = svc_disease
        final_confidence = svc_confidence
        print(f"[WINNER] SVC selected (higher confidence: {svc_confidence:.3f} vs {rf_confidence:.3f})")
    else:
        # Tie - use overall model performance
        if rf_overall_accuracy >= svc_overall_accuracy:
            winning_algorithm = "RandomForest"
            final_disease = rf_disease
            final_confidence = rf_confidence
            print(f"[WINNER] RandomForest selected (tie-breaker: better overall accuracy)")
        else:
            winning_algorithm = "SVC"
            final_disease = svc_disease
            final_confidence = svc_confidence
            print(f"[WINNER] SVC selected (tie-breaker: better overall accuracy)")
    
    # Return winning result + backend data for logging
    return {
        'final_disease': final_disease,
        'final_confidence': final_confidence,
        'winning_algorithm': winning_algorithm,
        'rf_disease': rf_disease,
        'svc_disease': svc_disease,
        'rf_confidence': rf_confidence,
        'svc_confidence': svc_confidence
    }

# --- Advanced Medication Filtering System ---
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

def get_contraindicated_medications(medical_history):
    """Get list of contraindicated medications based on medical history"""
    contraindicated = {
        'diabetes': [
            'prednisone', 'prednisolone', 'dexamethasone', 'methylprednisolone',
            'cortisone', 'hydrocortisone', 'betamethasone', 'triamcinolone',
            'thiazide', 'hydrochlorothiazide', 'chlorthalidone',
            'propranolol', 'metoprolol', 'atenolol', 'corticosteroids'
        ],
        'hypertension': [
            'ibuprofen', 'naproxen', 'diclofenac', 'celecoxib',
            'pseudoephedrine', 'phenylephrine', 'ephedrine',
            'decongestants', 'nsaids', 'high-sodium'
        ],
        'heart': [
            'ibuprofen', 'naproxen', 'diclofenac', 'nsaids',
            'amitriptyline', 'nortriptyline', 'tricyclic',
            'verapamil', 'diltiazem', 'stimulants'
        ],
        'kidney': [
            'ibuprofen', 'naproxen', 'diclofenac', 'nsaids',
            'lisinopril', 'enalapril', 'captopril', 'ace inhibitors',
            'gentamicin', 'tobramycin', 'aminoglycosides', 'lithium'
        ],
        'liver': [
            'acetaminophen', 'paracetamol', 'tylenol',
            'atorvastatin', 'simvastatin', 'statins',
            'isoniazid', 'phenytoin', 'valproic acid'
        ]
    }
    
    all_contraindicated = []
    if medical_history and medical_history.lower() != 'none':
        history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
        
        for condition in history_conditions:
            for key, meds in contraindicated.items():
                if key in condition:
                    all_contraindicated.extend(meds)
    
    return list(set(all_contraindicated))  # Remove duplicates

def get_safe_alternatives(medical_history, disease):
    """Get safe medication alternatives based on medical history"""
    alternatives = {
        'diabetes': {
            'pain': ['topical analgesics', 'capsaicin cream', 'physical therapy'],
            'inflammation': ['topical nsaids', 'ice therapy', 'compression'],
            'infection': ['penicillin', 'cephalexin', 'azithromycin'],
            'general': ['glucose-neutral medications', 'diabetes-safe alternatives']
        },
        'hypertension': {
            'pain': ['acetaminophen', 'topical analgesics', 'low-dose aspirin'],
            'cold': ['saline nasal spray', 'steam inhalation', 'honey'],
            'allergy': ['loratadine', 'cetirizine', 'fexofenadine'],
            'general': ['bp-neutral medications', 'low-sodium formulations']
        },
        'heart': {
            'pain': ['acetaminophen', 'topical analgesics', 'heat therapy'],
            'anxiety': ['relaxation techniques', 'meditation', 'counseling'],
            'sleep': ['sleep hygiene', 'melatonin', 'cognitive therapy'],
            'general': ['cardio-safe medications', 'heart-friendly alternatives']
        },
        'kidney': {
            'pain': ['acetaminophen', 'topical analgesics', 'physical therapy'],
            'infection': ['penicillin', 'cephalexin', 'trimethoprim-sulfamethoxazole'],
            'hypertension': ['amlodipine', 'losartan', 'calcium channel blockers'],
            'general': ['kidney-safe medications', 'renal-adjusted doses']
        },
        'liver': {
            'pain': ['ibuprofen (low dose)', 'topical analgesics', 'physical therapy'],
            'infection': ['penicillin', 'cephalexin', 'azithromycin'],
            'cholesterol': ['dietary changes', 'exercise', 'plant sterols'],
            'general': ['liver-safe medications', 'hepato-friendly alternatives']
        }
    }
    
    safe_meds = []
    if medical_history and medical_history.lower() != 'none':
        history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
        
        for condition in history_conditions:
            for key, alt_dict in alternatives.items():
                if key in condition:
                    # Add general alternatives
                    safe_meds.extend(alt_dict.get('general', []))
                    
                    # Add disease-specific alternatives
                    disease_lower = disease.lower()
                    if any(pain_word in disease_lower for pain_word in ['pain', 'ache', 'arthritis', 'migraine']):
                        safe_meds.extend(alt_dict.get('pain', []))
                    elif any(cold_word in disease_lower for cold_word in ['cold', 'flu', 'cough']):
                        safe_meds.extend(alt_dict.get('cold', []))
                    elif any(infection_word in disease_lower for infection_word in ['infection', 'pneumonia', 'bronchitis']):
                        safe_meds.extend(alt_dict.get('infection', []))
    
    return list(set(safe_meds))  # Remove duplicates

def filter_medications_by_medical_history(medications_list, medical_history, age, disease):
    """Advanced medication filtering based on medical history and age"""
    print(f"[FILTER DEBUG] Input medications: {medications_list}")
    print(f"[FILTER DEBUG] Medical history: {medical_history}")
    print(f"[FILTER DEBUG] Age: {age}")
    print(f"[FILTER DEBUG] Disease: {disease}")
    
    if not medications_list:
        return ["No medications available for this condition"]
    
    # Get contraindicated medications
    contraindicated_meds = get_contraindicated_medications(medical_history)
    print(f"[FILTER DEBUG] Contraindicated medications: {contraindicated_meds}")
    
    # Filter out contraindicated medications
    safe_medications = []
    removed_medications = []
    
    for med in medications_list:
        if not med or str(med).strip().lower() in ['nan', 'none', '']:
            continue
            
        med_lower = str(med).lower().strip()
        is_contraindicated = False
        
        # Check if medication is contraindicated
        for contra_med in contraindicated_meds:
            if contra_med.lower() in med_lower or med_lower in contra_med.lower():
                is_contraindicated = True
                removed_medications.append(f"❌ {med} (removed - contraindicated)")
                break
        
        if not is_contraindicated:
            safe_medications.append(f"✅ {med}")
    
    print(f"[FILTER DEBUG] Safe medications after filtering: {safe_medications}")
    print(f"[FILTER DEBUG] Removed medications: {removed_medications}")
    
    # Add safe alternatives
    safe_alternatives = get_safe_alternatives(medical_history, disease)
    print(f"[FILTER DEBUG] Safe alternatives: {safe_alternatives}")
    
    # Add alternatives with labels
    for alt in safe_alternatives[:3]:  # Limit to top 3 alternatives
        if alt not in [med.lower() for med in safe_medications]:
            safe_medications.append(f"🔄 {alt} (Safe alternative)")
    
    # Age-specific adjustments
    if age is not None:
        age_int = int(age)
        if age_int < 18:
            # Pediatric adjustments
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
    
    # Add medical history warnings
    if medical_history and medical_history.lower() != 'none':
        history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
        
        warning_messages = []
        if any('diabetes' in condition for condition in history_conditions):
            warning_messages.append("🩺 DIABETES: Monitor blood glucose levels closely")
        if any('hypertension' in condition or 'blood pressure' in condition for condition in history_conditions):
            warning_messages.append("🩺 HYPERTENSION: Monitor blood pressure regularly")
        if any('heart' in condition or 'cardiac' in condition for condition in history_conditions):
            warning_messages.append("🩺 HEART: Avoid medications that stress the heart")
        if any('kidney' in condition or 'renal' in condition for condition in history_conditions):
            warning_messages.append("🩺 KIDNEY: Use kidney-safe medications only")
        if any('liver' in condition or 'hepatic' in condition for condition in history_conditions):
            warning_messages.append("🩺 LIVER: Avoid hepatotoxic medications")
        
        safe_medications.extend(warning_messages)
    
    # Show what was removed for transparency
    if removed_medications:
        safe_medications.append("📋 REMOVED MEDICATIONS:")
        safe_medications.extend(removed_medications)
    
    # If no safe medications remain, provide guidance
    safe_med_count = len([med for med in safe_medications if med.startswith('✅')])
    if safe_med_count == 0:
        return [
            "⚠️ Standard medications for this condition require medical review due to your medical history.",
            "🏥 URGENT: Consult your healthcare provider for personalized treatment options.",
            "👨‍⚕️ Your doctor will prescribe medications that are safe for your specific conditions.",
            "📞 CONTACT: Seek immediate medical attention for proper treatment."
        ]
    
    print(f"[FILTER DEBUG] Final filtered medications: {safe_medications}")
    return safe_medications

# --- Enhanced Helper Function with Advanced Medical History Logic ---
def helper_with_history(dis, medical_history=None, age=None):
    """Enhanced helper function with condition-specific medication selection"""
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

        # Get condition-specific medications from dataset
        selected_medications = []
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
                
                # Check available columns
                available_columns = medications.columns.tolist()
                # print(f"[MEDICATION DEBUG] Available columns: {available_columns}")
                
                # Determine which medication column to use based on age and medical history
                if age is not None and int(age) < 18:
                    # Pediatric patients - always use pediatric medications
                    if 'Pediatric_Medication' in available_columns:
                        selected_medications = parse_medication_list(med_row['Pediatric_Medication'])
                        print(f"[MEDICATION DEBUG] Using Pediatric_Medication: {selected_medications}")
                    else:
                        selected_medications = ["Pediatric medications not available - consult pediatrician"]
                else:
                    # Adult patients - select based on medical history
                    if medical_history and medical_history.lower() != 'none':
                        history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
                        print(f"[MEDICATION DEBUG] Medical history conditions: {history_conditions}")
                        
                        # Priority order for condition-specific medications
                        condition_priority = [
                            ('diabetes', 'Diabetes_Medication'),
                            ('hypertension', 'Hypertension_Medication'), 
                            ('blood pressure', 'Hypertension_Medication'),
                            ('heart', 'Heart_Medication'),
                            ('cardiac', 'Heart_Medication'),
                            ('kidney', 'Kidney_Medication'),
                            ('renal', 'Kidney_Medication'),
                            ('liver', 'Liver_Medication'),
                            ('hepatic', 'Liver_Medication')
                        ]
                        
                        # Find the first matching condition and use its specific medications
                        medication_column_used = None
                        for condition_keyword, med_column in condition_priority:
                            if any(condition_keyword in condition for condition in history_conditions):
                                if med_column in available_columns:
                                    selected_medications = parse_medication_list(med_row[med_column])
                                    medication_column_used = med_column
                                    print(f"[MEDICATION DEBUG] Using {med_column} for {condition_keyword}: {selected_medications}")
                                    break
                        
                        # If no specific condition medications found, use adult medications
                        if not selected_medications:
                            if 'Adult_Medication' in available_columns:
                                selected_medications = parse_medication_list(med_row['Adult_Medication'])
                                medication_column_used = 'Adult_Medication'
                                print(f"[MEDICATION DEBUG] No specific condition meds found, using Adult_Medication: {selected_medications}")
                            elif 'Medication' in available_columns:
                                selected_medications = parse_medication_list(med_row['Medication'])
                                medication_column_used = 'Medication'
                                print(f"[MEDICATION DEBUG] Using general Medication: {selected_medications}")
                    else:
                        # Healthy adult - use standard adult medications
                        if 'Adult_Medication' in available_columns:
                            selected_medications = parse_medication_list(med_row['Adult_Medication'])
                            # print(f"[MEDICATION DEBUG] Healthy adult - using Adult_Medication: {selected_medications}")
                        elif 'Medication' in available_columns:
                            selected_medications = parse_medication_list(med_row['Medication'])
                            # print(f"[MEDICATION DEBUG] Healthy adult - using general Medication: {selected_medications}")
            else:
                print(f"[MEDICATION DEBUG] No medication found for disease: {dis}")
                selected_medications = [f"Standard treatment for {dis} - consult healthcare provider"]
        else:
            selected_medications = ["Medication database not available"]

        # Format medications with appropriate labels
        formatted_medications = []
        for med in selected_medications:
            if med and str(med).strip():
                formatted_medications.append(f"💊 {med}")
        
        # Add condition-specific notes
        if medical_history and medical_history.lower() != 'none' and age is not None and int(age) >= 18:
            history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
            
            if any('diabetes' in condition for condition in history_conditions):
                formatted_medications.append("🩺 DIABETES-SPECIFIC: These medications are specifically selected for diabetic patients")
            elif any('hypertension' in condition or 'blood pressure' in condition for condition in history_conditions):
                formatted_medications.append("🩺 HYPERTENSION-SPECIFIC: These medications are specifically selected for hypertensive patients")
            elif any('heart' in condition or 'cardiac' in condition for condition in history_conditions):
                formatted_medications.append("🩺 HEART-SPECIFIC: These medications are specifically selected for heart patients")
            elif any('kidney' in condition or 'renal' in condition for condition in history_conditions):
                formatted_medications.append("🩺 KIDNEY-SPECIFIC: These medications are specifically selected for kidney patients")
            elif any('liver' in condition or 'hepatic' in condition for condition in history_conditions):
                formatted_medications.append("🩺 LIVER-SPECIFIC: These medications are specifically selected for liver patients")

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

        # Generate personalized notes based on condition-specific medication selection
        personalized_notes = []
        
        # Age-specific notes
        if age is not None:
            age_int = int(age)
            if age_int < 18:
                personalized_notes.extend([
                    f"👶 PEDIATRIC PATIENT (Age {age}): Using pediatric-specific medications",
                    "👨‍⚕️ SUPERVISION: Adult supervision required for all treatments"
                ])
            elif age_int > 65:
                personalized_notes.extend([
                    f"👴 GERIATRIC PATIENT (Age {age}): Consider dose adjustments",
                    "🩺 MONITORING: Enhanced monitoring recommended"
                ])
            else:
                if medical_history and medical_history.lower() != 'none':
                    personalized_notes.append(f"👨‍⚕️ ADULT PATIENT (Age {age}): Using condition-specific medications for your medical history")
                else:
                    personalized_notes.append(f"👨‍⚕️ HEALTHY ADULT (Age {age}): Using standard adult medications")
        
        # Medical history specific notes
        if medical_history and medical_history.lower() != 'none':
            history_conditions = [condition.strip().lower() for condition in medical_history.split(',')]
            
            if any('diabetes' in condition for condition in history_conditions):
                personalized_notes.extend([
                    "⚠️ DIABETES: Medications specifically chosen for diabetic patients",
                    "🍎 DIET: Follow diabetes-appropriate diet recommendations",
                    "📊 MONITORING: Regular blood glucose monitoring required"
                ])
            
            if any('hypertension' in condition or 'blood pressure' in condition for condition in history_conditions):
                personalized_notes.extend([
                    "⚠️ HYPERTENSION: Medications specifically chosen for hypertensive patients",
                    "🧂 DIET: Low sodium diet recommended",
                    "📊 MONITORING: Regular blood pressure monitoring required"
                ])
            
            if any('heart' in condition or 'cardiac' in condition for condition in history_conditions):
                personalized_notes.extend([
                    "❤️ HEART CONDITION: Medications specifically chosen for heart patients",
                    "🏃 EXERCISE: Cardiac-appropriate exercise guidelines",
                    "📊 MONITORING: Regular cardiac monitoring required"
                ])
            
            if any('kidney' in condition or 'renal' in condition for condition in history_conditions):
                personalized_notes.extend([
                    "🫘 KIDNEY CONDITION: Medications specifically chosen for kidney patients",
                    "💧 HYDRATION: Kidney-appropriate hydration guidelines",
                    "📊 MONITORING: Regular kidney function monitoring required"
                ])
            
            if any('liver' in condition or 'hepatic' in condition for condition in history_conditions):
                personalized_notes.extend([
                    "🫀 LIVER CONDITION: Medications specifically chosen for liver patients",
                    "🚫 SUBSTANCES: Avoid alcohol and hepatotoxic substances",
                    "📊 MONITORING: Regular liver function monitoring required"
                ])

        # print(f"[HELPER DEBUG] Final condition-specific medications: {formatted_medications}")
        # print(f"[HELPER DEBUG] Final personalized notes: {personalized_notes}")
        
        return desc, pre, formatted_medications, die, wrkout, personalized_notes
    
    except Exception as e:
        print(f"Error in helper_with_history function: {e}")
        import traceback
        traceback.print_exc()
        return ("Error retrieving information", 
                [["No precautions available"]], 
                ["Error retrieving medications - consult healthcare provider"], 
                ["No diet recommendations available"], 
                ["No workout recommendations available"],
                ["⚠️ Error in processing medical history - consult healthcare provider"])

# --- Routes ---
@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
                user = cursor.fetchone()
                cursor.close()
                connection.close()
                
                if user:
                    session['username'] = username
                    return redirect(url_for('dashboard'))
                else:
                    return render_template('login.html', error='Invalid username or password')
            else:
                return render_template('login.html', error='Database connection error')
        except Exception as e:
            print(f"Login error: {e}")
            return render_template('login.html', error='An error occurred during login')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Get age with proper validation and explicit conversion
        try:
            age = int(request.form.get('age'))
            print(f"[REGISTER DEBUG] Received age input: {age}, type: {type(age)}")
        except (ValueError, TypeError):
            age = 30  # Default if not a valid number
            print(f"[REGISTER DEBUG] Invalid age input, using default: {age}")
        
        # Handle medical history checkboxes
        medical_history_list = request.form.getlist('medical_history')
        if not medical_history_list or 'None' in medical_history_list:
            medical_history = 'None'
        else:
            medical_history = ', '.join(medical_history_list)
        
        print(f"[REGISTER DEBUG] Username: {username}, Age: {age}, Medical History: {medical_history}")
        
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                
                # Check if username already exists
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    cursor.close()
                    connection.close()
                    return render_template('register.html', error='Username already exists')
                
                # Insert new user with explicit age and medical history
                cursor.execute(
                    "INSERT INTO users (username, password, age, medical_history) VALUES (%s, %s, %s, %s)", 
                    (username, password, age, medical_history)
                )
                connection.commit()
                
                # Verify insertion
                cursor.execute("SELECT username, age, medical_history FROM users WHERE username = %s", (username,))
                inserted_data = cursor.fetchone()
                print(f"[REGISTER DEBUG] Inserted data: Username={inserted_data[0]}, Age={inserted_data[1]}, Medical History={inserted_data[2]}")
                
                cursor.close()
                connection.close()
                
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                return render_template('register.html', error='Database connection error')
        except Exception as e:
            print(f"Registration error: {e}")
            import traceback
            traceback.print_exc()
            return render_template('register.html', error=f'An error occurred during registration: {str(e)}')
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('main.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        symptoms = request.form.get('symptoms')

        if not symptoms or symptoms.strip().lower() == "symptoms":
            message = "Please either write symptoms or you have written misspelled symptoms"
            return render_template('main.html', message=message)

        user_symptoms = [s.strip("[]' ") for s in symptoms.split(',')]

        if len(user_symptoms) < 3:
            message = "Please enter at least 3 symptoms for accurate prediction."
            return render_template('main.html', message=message)

        # Use smart algorithm selection (backend comparison)
        prediction_result = predict_disease_smart_selection(user_symptoms)
        
        if prediction_result is None:
            message = "None of the entered symptoms were recognized. Please try again with valid symptoms."
            return render_template('main.html', message=message)

        # Extract the winning result
        predicted_disease = prediction_result['final_disease']
        confidence = prediction_result['final_confidence']
        winning_algorithm = prediction_result['winning_algorithm']

        # Get user's age and medical history from database
        user_age = None
        user_medical_history = None
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT age, medical_history FROM users WHERE username = %s", (session['username'],))
                user_data = cursor.fetchone()
                if user_data:
                    user_age = user_data[0]
                    user_medical_history = user_data[1]
                cursor.close()
                connection.close()
                print(f"[PREDICT DEBUG] User age: {user_age}, Medical history: {user_medical_history}")
        except Exception as e:
            print(f"Error fetching user data: {e}")

        # Use enhanced helper function with advanced medical history filtering
        dis_des, precautions_list, medications_list, rec_diet, workout_list, personalized_notes = helper_with_history(
            predicted_disease, user_medical_history, user_age
        )

        # print(f"[PREDICT DEBUG] Enhanced medications received from helper: {medications_list}")

        # Handle precautions safely
        my_precautions = []
        if precautions_list and len(precautions_list) > 0:
            for i in precautions_list[0]:
                if i and str(i).strip() and str(i).strip().lower() != 'nan':
                    my_precautions.append(str(i))
        
        # If no precautions found, add a default message
        if not my_precautions:
            my_precautions = ["Consult with a healthcare professional for proper guidance"]

        # Save to search_history table (simplified)
        if 'username' in session:
            try:
                connection = get_db_connection()
                if connection:
                    cursor = connection.cursor()
                    
                    # Insert into search_history table
                    symptoms_str = ', '.join(user_symptoms)
                    print(f"[SEARCH HISTORY DEBUG] Saving search: User={session['username']}, Symptoms={symptoms_str}, Disease={predicted_disease}")
                    
                    cursor.execute(
                        "INSERT INTO search_history (username, symptoms, predicted_disease) VALUES (%s, %s, %s)",
                        (session['username'], symptoms_str, predicted_disease)
                    )
                    connection.commit()
                    
                    # Verify the insertion
                    cursor.execute("SELECT id FROM search_history WHERE username = %s ORDER BY searched_at DESC LIMIT 1", 
                                  (session['username'],))
                    last_id = cursor.fetchone()
                    print(f"[SEARCH HISTORY DEBUG] Inserted with ID: {last_id[0] if last_id else 'None'}")
                    
                    # Also save detailed prediction data for algorithm comparison
                    cursor.execute(
                        """INSERT INTO predictions (username, symptoms, predicted_disease, winning_algorithm, 
                           confidence, rf_prediction, svc_prediction, rf_confidence, svc_confidence) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (session['username'], symptoms_str, predicted_disease, winning_algorithm,
                         confidence, prediction_result['rf_disease'], prediction_result['svc_disease'],
                         prediction_result['rf_confidence'], prediction_result['svc_confidence'])
                    )
                    
                    connection.commit()
                    cursor.close()
                    connection.close()
                    print(f"[SEARCH HISTORY DEBUG] Successfully saved search history and prediction data")
            except Exception as e:
                print(f"[SEARCH HISTORY ERROR] Error saving search history: {e}")
                import traceback
                traceback.print_exc()

        # Store prediction data in session for PDF generation
        session['last_prediction'] = {
            'symptoms': user_symptoms,
            'predicted_disease': predicted_disease,
            'confidence': confidence,
            'winning_algorithm': winning_algorithm,
            'description': dis_des,
            'precautions': my_precautions,
            'medications': medications_list,
            'diet': rec_diet,
            'workout': workout_list,
            'personalized_notes': personalized_notes,
            'user_age': user_age,
            'user_medical_history': user_medical_history,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # print(f"[PREDICT DEBUG] Final enhanced medications being passed to template: {medications_list}")

        # Return only the winning result to user (no algorithm comparison shown)
        return render_template('main.html',
                               predicted_disease=predicted_disease,
                               confidence=round(confidence * 100, 2),
                               dis_des=dis_des,
                               my_precautions=my_precautions,
                               medications=medications_list,
                               my_diet=rec_diet,
                               workout=workout_list,
                               personalized_notes=personalized_notes,
                               user_age=user_age,
                               user_medical_history=user_medical_history)

    return redirect(url_for('dashboard'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    print(f"[PROFILE DEBUG] Loading profile for username: {username}")
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Get user's personal data (age and medical history)
            cursor.execute("SELECT age, medical_history FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            
            if user_data:
                age = user_data[0] if user_data[0] else 30
                medical_history = user_data[1] if user_data[1] else 'None'
                print(f"[PROFILE DEBUG] User data - Age: {age}, Medical History: {medical_history}")
            else:
                print(f"[PROFILE DEBUG] No user data found for username: {username}")
                age = 30
                medical_history = 'None'
            
            # Get search history from search_history table
            cursor.execute("""
                SELECT symptoms, predicted_disease, searched_at 
                FROM search_history 
                WHERE username = %s 
                ORDER BY searched_at DESC 
                LIMIT 10
            """, (username,))
            search_history = cursor.fetchall()
            print(f"[PROFILE DEBUG] Retrieved {len(search_history)} search history items")
            
            # Get total search count
            cursor.execute("SELECT COUNT(*) FROM search_history WHERE username = %s", (username,))
            count_result = cursor.fetchone()
            search_count = count_result[0] if count_result else 0
            print(f"[PROFILE DEBUG] Total search count: {search_count}")
            
            cursor.close()
            connection.close()
            
            return render_template('profile.html', 
                                 age=age,
                                 medical_history=medical_history, 
                                 search_history=search_history,
                                 search_count=search_count)
        else:
            print("[PROFILE DEBUG] Database connection failed")
            return render_template('profile.html', 
                                 age=30,
                                 medical_history='None', 
                                 search_history=[],
                                 search_count=0)
    except Exception as e:
        print(f"[PROFILE DEBUG] Error in profile route: {e}")
        import traceback
        traceback.print_exc()
        return render_template('profile.html', 
                             age=30,
                             medical_history='None', 
                             search_history=[],
                             search_count=0)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    
    # Get age with validation
    try:
        age = int(request.form.get('age', 30))
        if age < 1 or age > 120:
            age = 30  # Default if out of range
    except (ValueError, TypeError):
        age = 30  # Default if not a valid number
    
    # Handle multiple medical history checkboxes
    medical_history_list = request.form.getlist('medical_history')
    
    # If "None" is selected or no selections, use "None", otherwise join the selected conditions
    if 'None' in medical_history_list or not medical_history_list:
        medical_history = 'None'
    else:
        medical_history = ', '.join(medical_history_list)
    
    print(f"[PROFILE UPDATE DEBUG] Username: {username}")
    print(f"[PROFILE UPDATE DEBUG] Age: {age}")
    print(f"[PROFILE UPDATE DEBUG] Medical History List: {medical_history_list}")
    print(f"[PROFILE UPDATE DEBUG] Final Medical History: {medical_history}")
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Update user profile with explicit age and medical history
            cursor.execute("UPDATE users SET age = %s, medical_history = %s WHERE username = %s", 
                          (age, medical_history, username))
            connection.commit()
            
            # Verify the update
            cursor.execute("SELECT age, medical_history FROM users WHERE username = %s", (username,))
            updated_data = cursor.fetchone()
            print(f"[PROFILE UPDATE DEBUG] Updated data in DB: Age={updated_data[0]}, Medical History={updated_data[1]}")
            
            cursor.close()
            connection.close()
            
            print(f"[PROFILE UPDATE DEBUG] Profile updated successfully")
        
    except Exception as e:
        print(f"Error updating profile: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect(url_for('profile'))

@app.route('/test_medication_filtering')
def test_medication_filtering():
    """Test route to demonstrate advanced medication filtering"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Test cases to demonstrate filtering
    test_cases = [
        {
            "disease": "Migraine", 
            "medical_history": None, 
            "age": 35,
            "description": "Healthy adult with migraine"
        },
        {
            "disease": "Migraine", 
            "medical_history": "diabetes", 
            "age": 45,
            "description": "Adult with diabetes and migraine"
        },
        {
            "disease": "Arthritis", 
            "medical_history": "hypertension", 
            "age": 55,
            "description": "Adult with hypertension and arthritis"
        },
        {
            "disease": "Common Cold", 
            "medical_history": None, 
            "age": 8,
            "description": "Pediatric patient with common cold"
        },
        {
            "disease": "Arthritis", 
            "medical_history": "diabetes, hypertension, heart disease", 
            "age": 70,
            "description": "Elderly patient with multiple conditions"
        }
    ]
    
    results = []
    for case in test_cases:
        # Get base medications first
        base_medications = []
        if not medications.empty:
            med_rows = medications[medications['Disease'].str.lower() == case['disease'].lower()]
            if not med_rows.empty:
                med_row = med_rows.iloc[0]
                # Use any available medication column
                med_cols = [col for col in medications.columns if 'medication' in col.lower()]
                if med_cols:
                    base_medications = parse_medication_list(med_row[med_cols[0]])
                else:
                    base_medications = ["Standard treatment - consult healthcare provider"]
        
        # Apply filtering
        filtered_medications = filter_medications_by_medical_history(
            base_medications, 
            case['medical_history'], 
            case['age'], 
            case['disease']
        )
        
        results.append({
            'case': case,
            'base_medications': base_medications,
            'filtered_medications': filtered_medications,
            'contraindicated': get_contraindicated_medications(case['medical_history']),
            'safe_alternatives': get_safe_alternatives(case['medical_history'], case['disease'])
        })
    
    return render_template('test_medications.html', results=results)

@app.route('/admin_stats')
def admin_stats():
    """Simple stats page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM search_history")
            result = cursor.fetchone()
            search_count = result[0] if result else 0
            cursor.close()
            connection.close()
        else:
            search_count = 0
    except Exception as e:
        print(f"Error getting stats: {e}")
        search_count = 0
    
    return render_template('simple_stats.html', prediction_count=search_count)

@app.route('/download_report')
def download_report():
    if 'username' not in session or 'last_prediction' not in session:
        return redirect(url_for('dashboard'))
    
    try:
        # Get prediction data from session
        prediction_data = session['last_prediction']
        username = session['username']
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#3498db'),
            leftIndent=0
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20
        )
        
        # Title
        elements.append(Paragraph("MediCare+ MEDICAL PREDICTION REPORT", title_style))
        elements.append(Spacer(1, 20))
        
        # Patient Information
        elements.append(Paragraph("PATIENT INFORMATION", heading_style))
        elements.append(Paragraph(f"<b>Patient Name:</b> {username}", normal_style))
        elements.append(Paragraph(f"<b>Report Date:</b> {prediction_data['timestamp']}", normal_style))
        elements.append(Paragraph(f"<b> Algorithm Used:</b> {prediction_data['winning_algorithm']}", normal_style))
        if 'user_age' in prediction_data and prediction_data['user_age']:
            elements.append(Paragraph(f"<b>Patient Age:</b> {prediction_data['user_age']} years", normal_style))
        if 'user_medical_history' in prediction_data and prediction_data['user_medical_history'] and prediction_data['user_medical_history'] != 'None':
            elements.append(Paragraph(f"<b>Medical History:</b> {prediction_data['user_medical_history']}", normal_style))
        elements.append(Spacer(1, 20))
        
        # Prediction Results
        elements.append(Paragraph("PREDICTION RESULTS", heading_style))
        elements.append(Paragraph(f"<b>Symptoms Reported:</b> {', '.join(prediction_data['symptoms'])}", normal_style))
        elements.append(Paragraph(f"<b>Predicted Condition:</b> {prediction_data['predicted_disease']}", normal_style))
        elements.append(Paragraph(f"<b>Confidence Level:</b> {prediction_data['confidence']:.1f}%", normal_style))
        elements.append(Spacer(1, 20))
        
        # Disease Description
        elements.append(Paragraph("CONDITION DESCRIPTION", heading_style))
        elements.append(Paragraph(prediction_data['description'], normal_style))
        elements.append(Spacer(1, 15))
        
        # Precautions
        elements.append(Paragraph("RECOMMENDED PRECAUTIONS", heading_style))
        for i, precaution in enumerate(prediction_data['precautions'], 1):
            if precaution and precaution.strip():
                elements.append(Paragraph(f"{i}. {precaution}", normal_style))
        elements.append(Spacer(1, 15))
        
        # Medications (Enhanced with filtering info)
        elements.append(Paragraph("PERSONALIZED MEDICATIONS", heading_style))
        elements.append(Paragraph("<b>Note:</b> All medications have been filtered based on your medical history and age for maximum safety.", normal_style))
        for i, medication in enumerate(prediction_data['medications'], 1):
            if medication and medication.strip():
                elements.append(Paragraph(f"{i}. {medication}", normal_style))
        elements.append(Spacer(1, 15))
        
        # Diet Recommendations
        elements.append(Paragraph("DIETARY RECOMMENDATIONS", heading_style))
        for i, diet_item in enumerate(prediction_data['diet'], 1):
            if diet_item and diet_item.strip():
                elements.append(Paragraph(f"{i}. {diet_item}", normal_style))
        elements.append(Spacer(1, 15))
        
        # Exercise Recommendations
        elements.append(Paragraph("EXERCISE RECOMMENDATIONS", heading_style))
        for i, exercise in enumerate(prediction_data['workout'], 1):
            if exercise and exercise.strip():
                elements.append(Paragraph(f"{i}. {exercise}", normal_style))
        elements.append(Spacer(1, 20))

        # Personalized Health Alerts (Enhanced)
        if 'personalized_notes' in prediction_data and prediction_data['personalized_notes']:
            elements.append(Paragraph("PERSONALIZED HEALTH ALERTS", heading_style))
            for i, note in enumerate(prediction_data['personalized_notes'], 1):
                if note and note.strip():
                    elements.append(Paragraph(f"{i}. {note}", normal_style))
            elements.append(Spacer(1, 20))
        
        # AI System Information (Enhanced)
        elements.append(Paragraph("SYSTEM INFORMATION", heading_style))
        ai_info = f"""
        This report was generated using our advanced dual-algorithm AI system with comprehensive medical history filtering. 
        The system automatically compares predictions from RandomForest and Support Vector Machine algorithms, selecting the most 
        confident result. For this prediction, the {prediction_data['winning_algorithm']} algorithm provided the highest 
        confidence score and was selected as the final result.
        
        MEDICATION SAFETY: All medication recommendations have been automatically filtered based on your medical history 
        ({prediction_data.get('user_medical_history', 'None')}) and age ({prediction_data.get('user_age', 'Not specified')}) 
        to ensure maximum safety and avoid contraindicated medications.
        """
        elements.append(Paragraph(ai_info, normal_style))
        elements.append(Spacer(1, 15))
        
        # Enhanced Disclaimer
        disclaimer_text = """
        IMPORTANT MEDICAL DISCLAIMER: This report is generated by an AI-powered medical recommendation system with advanced 
        medical history filtering and is intended for informational purposes only. While our system filters medications 
        based on known contraindications for your medical conditions, this is NOT a substitute for professional medical 
        advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with 
        any questions you may have regarding a medical condition. Never disregard professional medical advice or delay 
        seeking it because of something you have read in this AI-generated report.
        """
        elements.append(Paragraph(disclaimer_text, normal_style))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=MediCare+_Medical_Report_{username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return redirect(url_for('dashboard'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Debug routes for testing
@app.route('/debug_user_data')
def debug_user_data():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'})
    
    username = session['username']
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Get user data
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            
            # Get search history
            cursor.execute("SELECT * FROM search_history WHERE username = %s ORDER BY searched_at DESC LIMIT 5", (username,))
            search_data = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'user_data': user_data,
                'search_history': search_data,
                'message': 'Debug data retrieved successfully'
            })
        else:
            return jsonify({'error': 'Database connection error'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug_medication_filtering/<disease>/<medical_history>/<int:age>')
def debug_medication_filtering(disease, medical_history, age):
    """Debug route to test medication filtering for specific parameters"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'})
    
    # Convert 'none' to None for medical_history
    if medical_history.lower() == 'none':
        medical_history = None
    
    # Get base medications
    base_medications = []
    if not medications.empty:
        med_rows = medications[medications['Disease'].str.lower() == disease.lower()]
        if not med_rows.empty:
            med_row = med_rows.iloc[0]
            if age < 18 and 'Pediatric_Medication' in medications.columns:
                base_medications = parse_medication_list(med_row['Pediatric_Medication'])
            else:
                base_medications = parse_medication_list(med_row.get('Adult_Medication', ''))
    
    # Apply filtering
    filtered_medications = filter_medications_by_medical_history(
        base_medications, medical_history, age, disease
    )
    
    return jsonify({
        'disease': disease,
        'medical_history': medical_history,
        'age': age,
        'base_medications': base_medications,
        'filtered_medications': filtered_medications,
        'contraindicated_medications': get_contraindicated_medications(medical_history),
        'safe_alternatives': get_safe_alternatives(medical_history, disease)
    })

if __name__ == '__main__':
    app.run(debug=True)
