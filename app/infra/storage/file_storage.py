import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import uuid

from app.schemas.storage import FileUploadResult
from app.core.config import settings


class FileStorageService:
    """로컬 파일 스토리지 서비스"""
    
    def __init__(self, upload_dir: str = None):
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(
        self, 
        file: UploadFile, 
        document_id: uuid.UUID
    ) -> FileUploadResult:
        """
        업로드된 파일을 로컬에 저장하고 파일 정보를 반환합니다.
        
        Args:
            file: 업로드된 파일
            document_id: 문서 ID
            
        Returns:
            FileUploadResult: 업로드 결과 정보
        """
        # 파일 확장자 추출
        file_extension = Path(file.filename or "").suffix
        
        # 저장할 파일명 생성 (document_id + 확장자)
        saved_filename = f"{document_id}{file_extension}"
        file_path = self.upload_dir / saved_filename
        
        # 파일 저장 및 해시 계산
        content_hash = hashlib.sha256()
        file_size = 0
        
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(8192):  # 8KB씩 읽기
                buffer.write(chunk)
                content_hash.update(chunk)
                file_size += len(chunk)
        
        return FileUploadResult(
            file_path=str(file_path),
            content_hash=content_hash.hexdigest(),
            file_size=file_size
        )
    
    def delete_file(self, file_path: str) -> bool:
        """
        파일을 삭제합니다.
        
        Args:
            file_path: 삭제할 파일 경로
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        텍스트 파일의 내용을 읽어옵니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            str: 파일 내용 (UTF-8 디코딩)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # UTF-8이 아닌 경우 다른 인코딩 시도
            try:
                with open(file_path, 'r', encoding='cp949') as f:
                    return f.read()
            except:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        return f.read()
                except:
                    return None
        except Exception:
            return None
    
    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        파일 크기를 반환합니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            int: 파일 크기 (bytes)
        """
        try:
            return os.path.getsize(file_path)
        except:
            return None