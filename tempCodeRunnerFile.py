from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import pymysql
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import ast  # Added for parsing string representations of lists
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
            
            # Ensure predictions table exists with algorithm comparison
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
    medications = pd.read_csv("datasets/medications.csv")
    diets = pd.read_csv("datasets/diets.csv")
    
    print("All datasets loaded successfully")
    print("Medications CSV columns:", medications.columns.tolist())
    print("Sample medications data:")
    print(medications.head())
    print("Medications shape:", medications.shape)
    print("Unique diseases in medications:", medications['Disease'].nunique())
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

# --- Enhanced Helper Function with Medical History and Age ---
def helper_with_history(dis, medical_history=None, age=None):
    try:
        print(f"[HELPER DEBUG] Processing disease: {dis}")
        print(f"[HELPER DEBUG] Age: {age}, Medical History: {medical_history}")
        
        # Get description
        if not description.empty:
            desc_rows = description[description['Disease'] == dis]['Description']
            if not desc_rows.empty:
                desc = " ".join([str(w) for w in desc_rows])
            else:
                desc = "No description available for this disease."
        else:
            desc = "No description available for this disease."

        # Get precautions
        if not precautions.empty:
            pre_rows = precautions[precautions['Disease'] == dis][['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']]
            if not pre_rows.empty:
                pre = [col for col in pre_rows.values]
            else:
                pre = [["No precautions available"]]
        else:
            pre = [["No precautions available"]]

        # Get medications - ENHANCED with age consideration
        if not medications.empty:
            print(f"[MEDICATION DEBUG] Looking for disease: {dis}")
            print(f"[MEDICATION DEBUG] Available diseases in medications: {medications['Disease'].unique()[:10]}")
            
            # Try exact match first
            med_rows = medications[medications['Disease'].str.lower() == dis.lower()]
            
            if med_rows.empty:
                # Try partial match
                med_rows = medications[medications['Disease'].str.contains(dis, case=False, na=False)]
            
            if not med_rows.empty:
                print(f"[MEDICATION DEBUG] Found medication row for: {dis}")
                
                # Determine which medication column to use based on age
                if age is not None and int(age) < 18:
                    # Use pediatric medications if available
                    if 'Pediatric_Medication' in medications.columns:
                        med_string = med_rows['Pediatric_Medication'].iloc[0]
                        print(f"[MEDICATION DEBUG] Using Pediatric_Medication: {med_string}")
                    else:
                        # Fall back to adult medications with pediatric modifications
                        med_string = med_rows['Adult_Medication'].iloc[0] if 'Adult_Medication' in medications.columns else med_rows.iloc[0, 1]
                        print(f"[MEDICATION DEBUG] Using Adult_Medication for pediatric modification: {med_string}")
                else:
                    # Use adult medications
                    if 'Adult_Medication' in medications.columns:
                        med_string = med_rows['Adult_Medication'].iloc[0]
                        print(f"[MEDICATION DEBUG] Using Adult_Medication: {med_string}")
                    elif 'Medication' in medications.columns:
                        med_string = med_rows['Medication'].iloc[0]
                        print(f"[MEDICATION DEBUG] Using Medication: {med_string}")
                    else:
                        # Use the second column (assuming first is Disease)
                        med_string = med_rows.iloc[0, 1]
                        print(f"[MEDICATION DEBUG] Using second column: {med_string}")
                
                # Parse medication string
                try:
                    if pd.isna(med_string) or str(med_string).lower() in ['nan', 'none', '']:
                        med = ["No specific medications available for this condition"]
                    else:
                        # Try to parse as list
                        med_string_clean = str(med_string).strip()
                        if med_string_clean.startswith('[') and med_string_clean.endswith(']'):
                            med = ast.literal_eval(med_string_clean)
                        else:
                            # Split by comma if it's a comma-separated string
                            med = [item.strip().strip("'\"") for item in med_string_clean.split(',')]
                        
                        if not isinstance(med, list):
                            med = [str(med_string)]
                        
                        # Remove empty items
                        med = [item for item in med if item and str(item).strip()]
                        print(f"[MEDICATION DEBUG] Parsed medications: {med}")
                except (ValueError, SyntaxError) as e:
                    print(f"[MEDICATION DEBUG] Parsing error: {e}, using raw string")
                    med = [str(med_string)]
                
                # Apply age-specific modifications to medications
                if age is not None:
                    age_int = int(age)
                    print(f"[MEDICATION DEBUG] Applying age modifications for age: {age_int}")
                    
                    if age_int < 18:
                        # Pediatric modifications
                        modified_meds = []
                        for medication in med:
                            med_lower = str(medication).lower()
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
                        print(f"[MEDICATION DEBUG] Pediatric medications: {med}")
                        
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
                        print(f"[MEDICATION DEBUG] Adult medications: {med}")
            else:
                print(f"[MEDICATION DEBUG] No medication found for disease: {dis}")
                if age is not None and int(age) < 18:
                    med = [f"👶 PEDIATRIC ALERT: No specific medications found for {dis}. Please consult a pediatrician for age-appropriate treatment."]
                else:
                    med = [f"No specific medications found for {dis}. Please consult a healthcare provider."]
        else:
            med = ["Medication database not available"]

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

        print(f"[HELPER DEBUG] Final medications: {med}")
        print(f"[HELPER DEBUG] Final personalized notes: {personalized_notes}")
        
        return desc, pre, med, die, wrkout, personalized_notes
    
    except Exception as e:
        print(f"Error in helper_with_history function: {e}")
        import traceback
        traceback.print_exc()
        return ("Error retrieving information", 
                [["No precautions available"]], 
                ["Error retrieving medications"], 
                ["No diet recommendations available"], 
                ["No workout recommendations available"],
                [])

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
        
        # Get age with proper validation
        try:
            age = int(request.form.get('age', 30))
            if age < 1 or age > 120:
                age = 30  # Default if out of range
        except (ValueError, TypeError):
            age = 30  # Default if not a valid number
            
        print(f"[REGISTER DEBUG] Received age: {age}, type: {type(age)}")
        
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
                cursor.execute("SELECT age, medical_history FROM users WHERE username = %s", (username,))
                inserted_data = cursor.fetchone()
                print(f"[REGISTER DEBUG] Inserted data: Age={inserted_data[0]}, Medical History={inserted_data[1]}")
                
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

        # Use age-aware helper function
        dis_des, precautions_list, medications_list, rec_diet, workout_list, personalized_notes = helper_with_history(
            predicted_disease, user_medical_history, user_age
        )

        print(f"[PREDICT DEBUG] Medications received from helper: {medications_list}")

        # Handle precautions safely
        my_precautions = []
        if precautions_list and len(precautions_list) > 0:
            for i in precautions_list[0]:
                if i and str(i).strip() and str(i).strip().lower() != 'nan':
                    my_precautions.append(str(i))
        
        # If no precautions found, add a default message
        if not my_precautions:
            my_precautions = ["Consult with a healthcare professional for proper guidance"]

        # Save prediction history (including backend comparison data)
        if 'username' in session:
            try:
                connection = get_db_connection()
                if connection:
                    cursor = connection.cursor()
                    cursor.execute(
                        """INSERT INTO predictions (username, symptoms, predicted_disease, winning_algorithm, 
                           confidence, rf_prediction, svc_prediction, rf_confidence, svc_confidence) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (session['username'], ', '.join(user_symptoms), predicted_disease, winning_algorithm,
                         confidence, prediction_result['rf_disease'], prediction_result['svc_disease'],
                         prediction_result['rf_confidence'], prediction_result['svc_confidence'])
                    )
                    connection.commit()
                    cursor.close()
                    connection.close()
            except Exception as e:
                print("Error saving prediction history:", e)

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
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        print(f"[PREDICT DEBUG] Final medications being passed to template: {medications_list}")

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
                               user_age=user_age)

    return redirect(url_for('dashboard'))

@app.route('/admin_stats')
def admin_stats():
    """Simple stats page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions")
            result = cursor.fetchone()
            prediction_count = result[0] if result else 0
            cursor.close()
            connection.close()
        else:
            prediction_count = 0
    except Exception as e:
        print(f"Error getting stats: {e}")
        prediction_count = 0
    
    return render_template('simple_stats.html', prediction_count=prediction_count)

# Update the profile route to include basic stats
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Get user's data
            cursor.execute("SELECT medical_history, age FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            
            if user_data:
                medical_history = user_data[0] if user_data[0] else 'None'
                age = user_data[1] if user_data[1] else 30
            else:
                medical_history = 'None'
                age = 30
            
            print(f"[PROFILE DEBUG] Retrieved from DB - Username: {username}, Age: {age}, Medical History: {medical_history}")
            
            # Get prediction history (only show final results to user)
            cursor.execute("""SELECT symptoms, predicted_disease, confidence, winning_algorithm, timestamp 
                             FROM predictions WHERE username = %s ORDER BY timestamp DESC LIMIT 10""", (username,))
            history = cursor.fetchall()
            
            # Get user's prediction count - FIX: Use a fresh query
            cursor.execute("SELECT COUNT(*) FROM predictions WHERE username = %s", (username,))
            count_result = cursor.fetchone()
            user_prediction_count = count_result[0] if count_result else 0
            
            cursor.close()
            connection.close()
            
            return render_template('profile.html', 
                                 medical_history=medical_history, 
                                 age=age,
                                 history=history,
                                 prediction_count=user_prediction_count)
        else:
            return render_template('profile.html', 
                                 medical_history='None', 
                                 age=30,
                                 history=[],
                                 prediction_count=0)
    except Exception as e:
        print(f"Error in profile route: {e}")
        import traceback
        traceback.print_exc()
        return render_template('profile.html', 
                             medical_history='None', 
                             age=30,
                             history=[],
                             prediction_count=0)

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

# Debug route to check user data
@app.route('/debug_user_data')
def debug_user_data():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Get all user data
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            if user_data:
                return jsonify({
                    'id': user_data[0],
                    'username': user_data[1],
                    'age': user_data[3],
                    'medical_history': user_data[4]
                })
            else:
                return jsonify({'error': 'User not found'})
        else:
            return jsonify({'error': 'Database connection error'})
    except Exception as e:
        return jsonify({'error': str(e)})

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
        elements.append(Paragraph("AI-POWERED MEDICAL PREDICTION REPORT", title_style))
        elements.append(Spacer(1, 20))
        
        # Patient Information
        elements.append(Paragraph("PATIENT INFORMATION", heading_style))
        elements.append(Paragraph(f"<b>Patient Name:</b> {username}", normal_style))
        elements.append(Paragraph(f"<b>Report Date:</b> {prediction_data['timestamp']}", normal_style))
        elements.append(Paragraph(f"<b>AI Algorithm Used:</b> {prediction_data['winning_algorithm']}", normal_style))
        if 'user_age' in prediction_data and prediction_data['user_age']:
            elements.append(Paragraph(f"<b>Patient Age:</b> {prediction_data['user_age']} years", normal_style))
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
        
        # Medications
        elements.append(Paragraph("RECOMMENDED MEDICATIONS", heading_style))
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

        # Personalized Notes
        if 'personalized_notes' in prediction_data and prediction_data['personalized_notes']:
            elements.append(Paragraph("PERSONALIZED HEALTH ALERTS", heading_style))
            for i, note in enumerate(prediction_data['personalized_notes'], 1):
                if note and note.strip():
                    elements.append(Paragraph(f"{i}. {note}", normal_style))
            elements.append(Spacer(1, 20))
        
        # AI Information
        elements.append(Paragraph("AI SYSTEM INFORMATION", heading_style))
        ai_info = f"""
        This report was generated using our advanced dual-algorithm AI system. The system automatically 
        compares predictions from RandomForest and Support Vector Machine algorithms, selecting the most 
        confident result. For this prediction, the {prediction_data['winning_algorithm']} algorithm 
        provided the highest confidence score and was selected as the final result.
        """
        elements.append(Paragraph(ai_info, normal_style))
        elements.append(Spacer(1, 15))
        
        # Disclaimer
        disclaimer_text = """
        This report is generated by an AI-powered medical recommendation system and is intended for 
        informational purposes only. This is NOT a substitute for professional medical advice, diagnosis, 
        or treatment. Always seek the advice of your physician or other qualified health provider with any 
        questions you may have regarding a medical condition.
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
        response.headers['Content-Disposition'] = f'attachment; filename=AI_Medical_Report_{username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
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

if __name__ == '__main__':
    app.run(debug=True)
