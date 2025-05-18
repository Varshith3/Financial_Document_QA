import os
import data_extraction
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
from langchain_cohere import CohereEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter


load_dotenv()

api_key = os.getenv("COHERE_API_KEY")
db_path = "metrics.db"
vector_db_path = "faiss.index"
pdf_folder = "data/"


data_extraction.init_db(db_path)

all_texts = ""
all_documents = []
pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]


for pdf_file in pdf_files:
    pdf_path = os.path.join(pdf_folder, pdf_file)
    
    text, images = data_extraction.extract_text_and_images(pdf_path)
    img_text = data_extraction.text_from_images(images[8:])
    text = text + "\n".join(img_text)

    metrics = data_extraction.extract_metrics(text)

    fiscal_period = os.path.basename(pdf_path)[:2]
    year = "20"+ os.path.basename(pdf_path)[4:]
    source_doc = os.path.basename(pdf_path)


    for metric_name, value in metrics.items():
        data_extraction.store_metrics(
            db_path=db_path,
            metric_name=metric_name,
            value=value,
            fiscal_period=fiscal_period, 
            year=year,
            source_doc=source_doc)

    all_texts += text + "\n\n"


llm = ChatCohere(temparature=0, cohere_api_key=api_key)
embeddings = CohereEmbeddings(model="embed-v4.0", cohere_api_key=api_key)

text_splitter = CharacterTextSplitter(
    chunk_size=1000,  
    chunk_overlap=300
)

chunks = text_splitter.split_text(all_texts)

all_documents = [Document(page_content=chunk) for chunk in chunks]

vector_db = FAISS.from_documents(all_documents,embeddings)
vector_db.save_local("faiss.index")

loaded_vector_db = FAISS.load_local("faiss.index", embeddings, allow_dangerous_deserialization=True)



def query_data(query):
    if not loaded_vector_db:
        return {"answer": "Vector database has not been built yet."}
        
    query_classifier_prompt = f"""
    Determine if the following question is primarily asking about:
    1. Specific financial metrics that would be in a structured database (e.g., revenue, EBITDA, margins, growth rates, PAT, net profits, operating margins)
    2. Unstructured information (e.g., management commentary, strategic plans, risk factors)
    3. Both structured metrics and contextual information
        
    Question: {query}
        
    Answer with just the number: 1, 2, or 3.
    """
        
    query_type = llm.predict(query_classifier_prompt).strip()
        
    retrieved_docs = loaded_vector_db.similarity_search(query,k=3)
    vector_context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        
    sql_data = ""
    if query_type == "1" or query_type == "3":
        sql_context = data_extraction.get_sql_data(db_path, query)
        if sql_context:
            sql_data = f"STRUCTURED FINANCIAL METRICS:\n{sql_context}\n\n"
        
    
    combined_prompt = f"""
    You are a financial analyst assistant. Answer the following question based on the provided information.
    Question: {query}
        
    {sql_data}
        
    DOCUMENT CONTEXT:
    {vector_context}
        
    Based on the above information only, provide a clear, concise answer to the question.
    If the information doesn't contain the answer, say "I don't have enough information to answer this question."
    If the question asks for trends or changes over time, explain the pattern clearly.
    """
        
    answer = llm.predict(combined_prompt)
        
    return answer