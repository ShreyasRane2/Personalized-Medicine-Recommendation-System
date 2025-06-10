import pandas as pd
import ast

# Test medication data loading
try:
    medications = pd.read_csv("datasets/medications.csv")
    print("Medications CSV loaded successfully!")
    print(f"Shape: {medications.shape}")
    print(f"Columns: {medications.columns.tolist()}")
    print("\nFirst 5 rows:")
    print(medications.head())
    
    print("\nSample diseases:")
    print(medications['Disease'].head(10).tolist())
    
    # Test a specific disease
    test_disease = "Fungal infection"
    print(f"\nTesting disease: {test_disease}")
    
    med_rows = medications[medications['Disease'].str.lower() == test_disease.lower()]
    if not med_rows.empty:
        print("Found matching row!")
        
        # Check available medication columns
        for col in medications.columns:
            if 'medication' in col.lower():
                print(f"Column {col}: {med_rows[col].iloc[0]}")
                
                # Try to parse
                try:
                    med_data = ast.literal_eval(str(med_rows[col].iloc[0]))
                    print(f"Parsed {col}: {med_data}")
                except Exception as e:
                    print(f"Parse error for {col}: {e}")
    else:
        print("No matching row found!")
        print("Available diseases:")
        print(medications['Disease'].unique()[:20])

except Exception as e:
    print(f"Error loading medications: {e}")
    import traceback
    traceback.print_exc()
