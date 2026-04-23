from .BaseController import BaseController
from .ProjectController import ProjectController
from models import ProcessingEnum
import os
import re
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
class ProcessController(BaseController):
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.project_dir = ProjectController().get_project_dir(project_id=project_id)

    def get_file_extension(self, file_id: str):
        return os.path.splitext(file_id)[-1]

    def get_file_loader(self, file_id: str):
        file_extension = self.get_file_extension(file_id=file_id)
        file_path = os.path.join(
            self.project_dir,
            file_id)
        if not os.path.exists(file_path):
            return None
        if file_extension == ProcessingEnum.TEXT.value:
            return TextLoader(file_path=file_path,encoding="utf-8")
        elif file_extension == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path=file_path)
        return None

    def get_file_content(self, file_id: str):
        loader = self.get_file_loader(file_id=file_id)
        if loader:
            return loader.load()
        return None
    def clean_text(self,text: str) -> str:
        """Clean common extraction artifacts before chunking for text and pdf files."""
        # remove page numbers (standalone numbers on a line)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        # normalize multiple newlines to double (paragraph boundary)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # join hyphenated line breaks (common in PDFs: "algo-\nrithm" → "algorithm")
        text = re.sub(r'-\n(\w)', r'\1', text)
        # replace single newlines with space (mid-paragraph line wrapping)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        # collapse multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()
    def process_file_content(self, file_content: list,file_id: str,chunk_size: int = 100,overlap_size: int = 20)->list:
        
        text_splitter = RecursiveCharacterTextSplitter(
         chunk_size=chunk_size,
         chunk_overlap=overlap_size,
         length_function=len)
        
        file_content_texts=[
            self.clean_text(record.page_content)
            for record in file_content
         ]
        file_content_metadata=[
            record.metadata
            for record in file_content
         ]
        chunks=text_splitter.create_documents(
            file_content_texts,
            metadatas=file_content_metadata)
        return chunks