import os

from pathlib import Path
from urllib.parse import unquote, urlparse

import docx
from chromadb.config import Settings as ChromaSettings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings
from app.core.enum import DocumentStatus
from app.db.database import SessionLocal
from app.models.companies import CompanyDocument

VECTOR_DB_DIR = str(Path("chroma_db").resolve())
COLLECTION_NAME = "company_policies"


def resolve_document_path(file_url: str) -> str:
    parsed_url = urlparse(file_url)
    raw_path = unquote(parsed_url.path or file_url)

    if parsed_url.scheme in {"http", "https", "file"}:
        if raw_path.startswith("/") and len(raw_path) > 2 and raw_path[2] == ":":
            return raw_path.lstrip("/")
        return str(Path(raw_path.lstrip("/")).resolve())

    return str(Path(file_url).expanduser().resolve())


def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    if not settings.GOOGLE_API_KEY:
        raise ValueError("Thiếu GOOGLE_API_KEY, không thể tạo embedding.")

    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=settings.GOOGLE_API_KEY,
    )


def _get_vector_store(with_embeddings: bool = True) -> Chroma:
    embedding_function = _get_embeddings() if with_embeddings else None
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_function,
        persist_directory=VECTOR_DB_DIR,
        client_settings=ChromaSettings(anonymized_telemetry=False),
    )


def _build_chunk_ids(doc_id: int, chunk_count: int) -> list[str]:
    return [f"company_doc_{doc_id}_chunk_{index}" for index in range(chunk_count)]


def _update_document_status(doc_id: int, status: DocumentStatus, db) -> None:
    document = db.query(CompanyDocument).filter(CompanyDocument.id == doc_id).first()
    if document:
        document.status = status
        db.commit()


def process_and_store_document(doc_id: int, file_path: str, company_id: int):
    db = SessionLocal()
    try:
        normalized_path = resolve_document_path(file_path)
        if not os.path.exists(normalized_path):
            raise FileNotFoundError(f"Không tìm thấy file tài liệu: {normalized_path}")

        ext = os.path.splitext(normalized_path)[1].lower()
        if ext != ".docx":
            raise ValueError(f"Hệ thống AI hiện chỉ hỗ trợ đọc file .docx. File tải lên: {ext}")

        doc = docx.Document(normalized_path)
        full_text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        if not full_text.strip():
            raise ValueError("File tài liệu trống, không có nội dung văn bản.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        chunks = text_splitter.split_text(full_text)
        if not chunks:
            raise ValueError("Không thể tách nội dung tài liệu thành các đoạn để nhúng.")

        metadatas = [{"company_id": company_id, "doc_id": doc_id} for _ in chunks]
        chunk_ids = _build_chunk_ids(doc_id, len(chunks))

        vector_store = _get_vector_store(with_embeddings=True)
        delete_document_from_chroma(doc_id, company_id)
        vector_store.add_texts(texts=chunks, metadatas=metadatas, ids=chunk_ids)

        _update_document_status(doc_id, DocumentStatus.ready, db)
        print(f"AI đã học xong tài liệu DOCX ID: {doc_id}")
    except Exception as e:
        print(f"Lỗi RAG Processing ({file_path}): {str(e)}")
        _update_document_status(doc_id, DocumentStatus.failed, db)
    finally:
        db.close()


def delete_document_from_chroma(doc_id: int, company_id: int):
    vector_store = _get_vector_store(with_embeddings=False)
    results = vector_store._collection.get(
        where={"$and": [{"doc_id": doc_id}, {"company_id": company_id}]},
        include=[],
    )
    ids = results.get("ids", [])
    if ids:
        vector_store.delete(ids=ids)

