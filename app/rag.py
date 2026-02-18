import os
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_nomic import NomicEmbeddings
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app import config
from fastapi import HTTPException, status, Response

load_dotenv()

embeddings = NomicEmbeddings(model='nomic-embed-text-v1.5')
llm = ChatGroq(model='llama-3.3-70b-versatile', temperature=0.4)


class ChatRequest(BaseModel):
    question: str
    files: List[str]


def chat(payload: ChatRequest, response: Response):
    question = payload.question
    files = payload.files

    try:
        # Load
        loader = PyPDFDirectoryLoader(
            path = config.UPLOAD_FOLDER,  
            glob = "**/[!.]*.pdf"
        )
        documents = loader.load()
        
        selected_files = set(files)
        selected_documents = [
            doc for doc in documents
            if os.path.basename(doc.metadata.get("source", "")) in selected_files
        ]

        print("pdf's are loaded")

        # Chunk
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
        chunked_data = splitter.split_documents(selected_documents)

        print("data are chuncked")

        # Vectorize
        vector_store = Chroma.from_documents(
            chunked_data,
            embeddings
        )

        # Search
        context = vector_store.max_marginal_relevance_search(
            query=question,
            k=3,
            fetch_k=5
        )

        print("data are vectorized")

        # Generate
        messages = [
            (
                "system",
                '''
                    You are a helpful assistant that answer the questions 
                    only based on the given context.
                '''
                f"context: {context}",
            ),
            ("user", question),
        ]

        ai_response = llm.invoke(messages)

        response.status_code = status.HTTP_200_OK
        return {"message": ai_response.content}
    
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )



