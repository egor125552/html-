import pandas as pd

def convert_excel_to_text(excel_file, text_file):
    try:
        df = pd.read_excel(excel_file)
        # We are interested in the 'Название' column
        if 'Название' in df.columns:
            df['Название'].to_csv(text_file, index=False, header=False)
            print(f"Successfully converted '{excel_file}' to '{text_file}'")
        else:
            print(f"ERROR: 'Название' column not found in '{excel_file}'")
    except Exception as e:
        print(f"An error occurred while converting {excel_file}: {e}")

convert_excel_to_text('products_garfield_1.xlsx', 'products_garfield_1.txt')
convert_excel_to_text('products_garfield_2.xlsx', 'products_garfield_2.txt')
convert_excel_to_text('products_garfield_3.xlsx', 'products_garfield_3.txt')