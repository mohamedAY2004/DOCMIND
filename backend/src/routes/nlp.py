from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
import logging
from schemas.nlp import PushRequest, SearchRequest, AnswerRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers import NLPController
from models import ResponseSignal

logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"]
)


@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: str, push_request: PushRequest):
    project_model = await ProjectModel.create_instance(db_pool=request.app.db_pool)
    chunk_model = await ChunkModel.create_instance(db_pool=request.app.db_pool)

    project = await project_model.get_project_or_create_one(project_id=project_id)
    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.PROJECT_NOT_FOUND.value}
        )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    page = 1
    inserted_count = 0
    while True:
        page_chunks = await chunk_model.get_chunks_by_project_id(project_id=project.id, page=page, page_size=25)
        if len(page_chunks) == 0:
            break
        is_inserted = await nlp_controller.index_into_vectordb(
            project=project, chunks=page_chunks, do_reset=(push_request.do_reset if page == 1 else 0)
        )
        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"signal": ResponseSignal.INSET_INTO_VECTORDB_FAILED.value}
            )
        page += 1
        inserted_count += len(page_chunks)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.PROJECT_INDEXED_SUCCESSFULLY.value,
            "inserted_count": inserted_count,
            "page_count": page - 1,
        }
    )


@nlp_router.get("/index/info/{project_id}")
async def get_index_info(request: Request, project_id: str):
    project_model = await ProjectModel.create_instance(db_pool=request.app.db_pool)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )
    collection_info = await nlp_controller.get_vectordb_collection_info(project=project)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseSignal.INDEX_INFO_FETCHED_SUCCESSFULLY.value, "collection_info": collection_info}
    )


@nlp_router.post("/index/search/{project_id}")
async def search_project(request: Request, project_id: str, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(db_pool=request.app.db_pool)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )
    results = await nlp_controller.search_vectordb(
        project=project, query=search_request.query, limit=search_request.limit, threshold=search_request.threshold
    )
    results = [{"text": result.chunk_text, "score": result.score} for result in results]

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseSignal.SEARCH_COMPLETED_SUCCESSFULLY.value, "search_results": results}
    )


@nlp_router.post("/answer/{project_id}")
async def answer_project(request: Request, project_id: str, answer_request: AnswerRequest):
    project_model = await ProjectModel.create_instance(db_pool=request.app.db_pool)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )
    answer = await nlp_controller.answer_rag_question(
        project=project, query=answer_request.query, limit=answer_request.limit, threshold=answer_request.threshold
    )

    if not answer:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.RAG_ANSWER_FAILED.value}
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseSignal.RAG_ANSWER_COMPLETED_SUCCESSFULLY.value, "answer": answer}
    )
