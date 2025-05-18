# 📊 Financial Presentation RAG Pipeline

This project builds an end-to-end pipeline to extract structured and unstructured information from financial presentation PDFs (e.g., investor presentations, earnings reports) and enables intelligent querying through Retrieval-Augmented Generation (RAG). The system integrates OCR, SQL storage, vector embedding, and an LLM-powered query interface.

## Preview   

https://github.com/user-attachments/assets/823cd0d8-9e7f-4cf5-b86d-623b07fb370a   


## Features   

Allows users to ask natural language questions like:   
What is the trend in net profit over the last 8 quarters?   
What did the CEO say about Q2 2023?   
How has operating margin evolved year over year?


### 📥 Data Ingestion
- Extracts structured financial metrics like Revenue, EBITDA, PAT, etc.
- Stores structured metrics in a SQL table (`metric_table`).
- Parses unstructured narrative and commentary from PDFs and stores in FAISS vector database.

