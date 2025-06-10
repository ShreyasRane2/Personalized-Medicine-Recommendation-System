import pandas as pd
import ast

# Load the medications dataset
medications = pd.read_csv("datasets/medications.csv")

def test_medication_differences():
    """
    Test function to demonstrate how medical history affects medication recommendations
    """
    print("=" * 80)
    print("MEDICAL HISTORY IMPACT TESTING")
    print("=" * 80)
    
    # Test diseases that have contraindications
    test_diseases = [
        "Allergy",
        "Hypertension", 
        "Migraine",
        "Arthritis",
        "Heart attack",
        "Bronchial Asthma",
        "Urinary tract infection"
    ]
    
    # Test medical conditions
    test_conditions = ["diabetes", "hypertension", "heart disease", "kidney disease", "liver disease"]
    
    for disease in test_diseases:
        print(f"\n🏥 DISEASE: {disease}")
        print("-" * 60)
        
        # Get the disease row
        disease_row = medications[medications['Disease'] == disease]
        if disease_row.empty:
            print(f"❌ Disease '{disease}' not found in dataset")
            continue
            
        # Show original adult medications
        try:
            original_meds = ast.literal_eval(disease_row['Adult_Medication'].iloc[0])
            print(f"📋 ORIGINAL MEDICATIONS (No Medical History):")
            for i, med in enumerate(original_meds, 1):
                print(f"   {i}. {med}")
        except:
            print("❌ Could not parse original medications")
            continue
        
        print(f"\n🔍 IMPACT OF MEDICAL CONDITIONS:")
        
        # Test each medical condition
        for condition in test_conditions:
            condition_key = None
            if 'diabetes' in condition:
                condition_key = 'Diabetes'
            elif 'hypertension' in condition:
                condition_key = 'Hypertension'
            elif 'heart' in condition:
                condition_key = 'Heart'
            elif 'kidney' in condition:
                condition_key = 'Kidney'
            elif 'liver' in condition:
                condition_key = 'Liver'
            
            if condition_key:
                contraindicated_col = f"{condition_key}_Contraindicated"
                alternative_col = f"{condition_key}_Alternative"
                
                if contraindicated_col in disease_row.columns and alternative_col in disease_row.columns:
                    try:
                        contraindicated = ast.literal_eval(str(disease_row[contraindicated_col].iloc[0]))
                        alternatives = ast.literal_eval(str(disease_row[alternative_col].iloc[0]))
                        
                        if contraindicated and contraindicated != [False] and str(contraindicated) != 'False':
                            print(f"\n   🚨 {condition.upper()} PATIENT:")
                            print(f"      ❌ AVOID: {contraindicated}")
                            print(f"      ✅ ALTERNATIVES: {alternatives}")
                            
                            # Show what would be changed
                            modified_meds = original_meds.copy()
                            changes_made = []
                            
                            for contra_med in contraindicated:
                                if contra_med:
                                    for i, orig_med in enumerate(modified_meds):
                                        if str(contra_med).lower() in str(orig_med).lower():
                                            if alternatives and len(alternatives) > 0:
                                                for alt in alternatives:
                                                    if alt and str(alt).strip():
                                                        modified_meds[i] = f"{alt} (safer for {condition})"
                                                        changes_made.append(f"Replaced '{contra_med}' with '{alt}'")
                                                        break
                            
                            if changes_made:
                                print(f"      🔄 CHANGES MADE:")
                                for change in changes_made:
                                    print(f"         • {change}")
                    except:
                        pass
        
        print("\n" + "=" * 60)

def compare_age_groups():
    """
    Compare pediatric vs adult medications
    """
    print("\n" + "=" * 80)
    print("AGE GROUP MEDICATION COMPARISON")
    print("=" * 80)
    
    sample_diseases = ["Common Cold", "Pneumonia", "Bronchitis", "Tonsillitis"]
    
    for disease in sample_diseases:
        disease_row = medications[medications['Disease'] == disease]
        if not disease_row.empty:
            print(f"\n🏥 DISEASE: {disease}")
            print("-" * 40)
            
            try:
                adult_meds = ast.literal_eval(disease_row['Adult_Medication'].iloc[0])
                pediatric_meds = ast.literal_eval(disease_row['Pediatric_Medication'].iloc[0])
                
                print(f"👨 ADULT MEDICATIONS:")
                for med in adult_meds:
                    print(f"   • {med}")
                
                print(f"\n👶 PEDIATRIC MEDICATIONS:")
                for med in pediatric_meds:
                    print(f"   • {med}")
                
                print(f"\n📊 KEY DIFFERENCES:")
                # Find medications that are different
                adult_set = set([str(m).lower() for m in adult_meds])
                pediatric_set = set([str(m).lower() for m in pediatric_meds])
                
                only_adult = adult_set - pediatric_set
                only_pediatric = pediatric_set - adult_set
                
                if only_adult:
                    print(f"   🚫 ADULT ONLY: {', '.join(only_adult)}")
                if only_pediatric:
                    print(f"   👶 PEDIATRIC ONLY: {', '.join(only_pediatric)}")
                    
            except Exception as e:
                print(f"❌ Error processing {disease}: {e}")

def simulate_real_scenarios():
    """
    Simulate real patient scenarios to show the impact
    """
    print("\n" + "=" * 80)
    print("REAL PATIENT SCENARIOS")
    print("=" * 80)
    
    scenarios = [
        {
            "name": "John (45, Diabetes + Hypertension)",
            "age": 45,
            "conditions": ["diabetes", "hypertension"],
            "disease": "Migraine"
        },
        {
            "name": "Sarah (8, No medical history)",
            "age": 8,
            "conditions": [],
            "disease": "Common Cold"
        },
        {
            "name": "Robert (65, Heart Disease + Kidney Disease)",
            "age": 65,
            "conditions": ["heart disease", "kidney disease"],
            "disease": "Arthritis"
        },
        {
            "name": "Maria (30, Asthma)",
            "age": 30,
            "conditions": ["asthma"],
            "disease": "Hypertension"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n👤 PATIENT: {scenario['name']}")
        print(f"📋 DIAGNOSED WITH: {scenario['disease']}")
        print("-" * 50)
        
        disease_row = medications[medications['Disease'] == scenario['disease']]
        if disease_row.empty:
            continue
            
        # Get base medications
        if scenario['age'] < 18:
            base_meds = ast.literal_eval(disease_row['Pediatric_Medication'].iloc[0])
            print(f"📋 BASE MEDICATIONS (Pediatric):")
        else:
            base_meds = ast.literal_eval(disease_row['Adult_Medication'].iloc[0])
            print(f"📋 BASE MEDICATIONS (Adult):")
        
        for med in base_meds:
            print(f"   • {med}")
        
        # Apply medical history modifications
        if scenario['conditions']:
            print(f"\n🚨 MEDICAL HISTORY ADJUSTMENTS:")
            modified_meds = base_meds.copy()
            warnings = []
            
            for condition in scenario['conditions']:
                condition_key = None
                if 'diabetes' in condition:
                    condition_key = 'Diabetes'
                elif 'hypertension' in condition:
                    condition_key = 'Hypertension'
                elif 'heart' in condition:
                    condition_key = 'Heart'
                elif 'kidney' in condition:
                    condition_key = 'Kidney'
                elif 'asthma' in condition:
                    # For asthma, we'd need to add this to our CSV
                    print(f"   ⚠️ {condition.upper()}: Special considerations needed")
                    continue
                
                if condition_key:
                    contraindicated_col = f"{condition_key}_Contraindicated"
                    alternative_col = f"{condition_key}_Alternative"
                    
                    if contraindicated_col in disease_row.columns:
                        try:
                            contraindicated = ast.literal_eval(str(disease_row[contraindicated_col].iloc[0]))
                            alternatives = ast.literal_eval(str(disease_row[alternative_col].iloc[0]))
                            
                            if contraindicated and contraindicated != [False]:
                                for contra_med in contraindicated:
                                    if contra_med:
                                        warnings.append(f"❌ AVOID {contra_med} due to {condition}")
                                        if alternatives:
                                            for alt in alternatives:
                                                if alt:
                                                    warnings.append(f"✅ USE {alt} instead")
                                                    break
                        except:
                            pass
            
            for warning in warnings:
                print(f"   {warning}")
        else:
            print(f"\n✅ NO MEDICAL HISTORY - Standard medications apply")

if __name__ == "__main__":
    # Run all tests
    test_medication_differences()
    compare_age_groups()
    simulate_real_scenarios()
    
    print("\n" + "=" * 80)
    print("🎯 HOW TO TEST IN YOUR APPLICATION:")
    print("=" * 80)
    print("1. Create two user accounts:")
    print("   - User A: No medical history")
    print("   - User B: Add diabetes, hypertension")
    print("\n2. Use same symptoms for both users:")
    print("   - Example: 'headache, nausea, dizziness' (Migraine)")
    print("\n3. Compare the medication recommendations")
    print("\n4. Look for these differences:")
    print("   - ⚠️ Warning messages about contraindications")
    print("   - ✅ Substituted medications")
    print("   - 📋 Additional recommended medications")
    print("=" * 80)
