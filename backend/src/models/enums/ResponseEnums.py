from enum import Enum
class ResponseSignal(Enum):
    
    FILE_VALIDATION_SUCCESS = "file_validation_success"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_IS_EXCEEDED = "file_size_is_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"

    FILE_PROCESSING_SUCCESS = "file_processing_success"
    FILE_PROCESSING_FAILED = "file_processing_failed"
    NO_FILES_TO_PROCESS = "no_files_to_process"
    FILE_NOT_FOUND = "file_not_found"

    PROJECT_NOT_FOUND = "project_not_found"
    PROJECT_INDEXED_SUCCESSFULLY = "project_indexed_successfully"
    INSET_INTO_VECTORDB_FAILED = "inset_into_vectordb_failed"
    INDEX_INFO_FETCHED_SUCCESSFULLY = "index_info_fetched_successfully"
    SEARCH_COMPLETED_SUCCESSFULLY = "search_completed_successfully"

    RAG_ANSWER_FAILED = "rag_answer_failed"
    RAG_ANSWER_COMPLETED_SUCCESSFULLY = "rag_answer_completed_successfully"