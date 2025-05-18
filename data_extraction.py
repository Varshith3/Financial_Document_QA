import re
import io
import fitz 
import sqlite3
import pytesseract
from PIL import Image




def init_db(db_path):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metric_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT,
            value TEXT,
            fiscal_period TEXT,
            year INTEGER,
            source_doc TEXT
        )
    """)
    conn.commit()
    conn.close()





def extract_text_and_images(pdf_path):

    doc = fitz.open(pdf_path)
    text = ""
    images = []
    
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text += page.get_text("text")  
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            images.append(image)
    
    return text, images





def text_from_images(images):

    extracted_text = []
    
    for i, image in enumerate(images):
        try:
            image = image.convert("RGB")
            
            ocr_text = pytesseract.image_to_string(image)

            if not ocr_text.strip():  
                continue  
    
            extracted_text.append(ocr_text)
        
        except Exception as e:
            print(f"Error processing image {i + 9}: {e}")
            continue 
    
    return extracted_text





def extract_metrics(text):

    metrics = {
        "Revenue": None,
        "EBITDA": None,
        "EBITDA Margin": None,
        "Growth Rate": None,
        "PAT": None,
        "PAT Margin": None,
        "Net Profit": None,
        "Operating Margin": None
    }
    patterns = {
        "Revenue": r"Revenue\s*[:=]?\s*(\d+[\.,]?\d*)\s*(million|billion)?",
        "EBITDA": r"EBITDA\s*[:=]?\s*(\d+[\.,]?\d*)\s*(million|billion)?",
        "EBITDA Margin": r"EBITDA Margin\s*[:=]?\s*(\d+[\.,]?\d*)\s*%",
        "Growth Rate": r"Growth Rate\s*[:=]?\s*(\d+[\.,]?\d*)\s*%",
        "PAT": r"PAT\s*[:=]?\s*(\d+[\.,]?\d*)\s*(million|billion)?",
        "PAT Margin": r"PAT Margin\s*[:=]?\s*(\d+[\.,]?\d*)\s*%",
        "Net Profit": r"Net Profit\s*[:=]?\s*(\d+[\.,]?\d*)\s*(million|billion)?",
        "Operating Margin": r"Operating Margin\s*[:=]?\s*(\d+[\.,]?\d*)\s*%"
    }

    for metric_name, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            metrics[metric_name] = match.group(1)
    
    return metrics




def store_metrics(db_path, metric_name, value, fiscal_period, year, source_doc):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    init_db(db_path)
    
    cursor.execute('''
    INSERT INTO metric_table (metric_name, value, fiscal_period, year, source_doc)
    VALUES (?, ?, ?, ?, ?)
    ''', (metric_name, value, fiscal_period, year, source_doc))
    
    conn.commit()
    conn.close()    





def get_sql_data(db_path, query):
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT metric_name, value, fiscal_period, year, source_doc
            FROM metric_table
            WHERE metric_name LIKE ?
        """, (f"%{query}%",))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "No structured data found for the given query."

        result = "Structured Financial Metrics:\n"
        for row in rows:
            metric_name, value, fiscal_period, year, source_doc = row
            result += f"- {metric_name}: {value} (Fiscal Period: {fiscal_period}, Year: {year}, Source: {source_doc})\n"

        return result

    except sqlite3.Error as e:
        return f"Error querying the database: {e}"
