from fastapi import APIRouter, Depends, UploadFile, File

from app.domains.code.dependencies import CodeServiceDep
from app.domains.code.schemas import CodeGenerationRequest, CodeGenerationResponse, CodeExecutionResponse, \
    CodeExecutionRequest
from app.domains.file.dependencies import FileServiceDep
from fastapi import APIRouter, Depends, UploadFile, File

from app.domains.code.dependencies import CodeServiceDep
from app.domains.code.schemas import CodeGenerationRequest, CodeGenerationResponse, CodeExecutionResponse, \
    CodeExecutionRequest
from app.domains.file.dependencies import FileServiceDep

router = APIRouter()


@router.post("/generate", response_model=CodeGenerationResponse)
async def generate_code(code_service: CodeServiceDep,
                        file_service: FileServiceDep,
                        request: CodeGenerationRequest = Depends(CodeGenerationRequest.as_form),
                        file: UploadFile = File(None, description="파일")):
    file_content = await extract_file_content(file, file_service)

    result = await code_service.generate_code(request, file_content)
    return result


async def extract_file_content(file, file_service):
    # 파일 내용 추출
    if not file:
        return None

    file_result = await file_service.extract_file_content(file)
    if file_result and file_result.content:
        return file_result.content


@router.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(request: CodeExecutionRequest,
                       code_service: CodeServiceDep):
    result = await code_service.execute_code(request)
    return result
