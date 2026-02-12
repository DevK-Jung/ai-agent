import numpy as np
from typing import List, Optional, Union
from sentence_transformers import SentenceTransformer
import logging
import torch

from app.core.config import settings


class BGEEmbeddingService:
    """BGE-M3 임베딩 서비스"""
    
    def __init__(self, model_name: str = None, device: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model: Optional[SentenceTransformer] = None
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.logger = logging.getLogger(__name__)
        
    def _load_model(self):
        """모델을 로드합니다. (지연 로딩)"""
        if self.model is None:
            try:
                self.logger.info(f"{self.model_name} 모델 로딩 중... (device: {self.device})")
                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    trust_remote_code=True
                )
                self.logger.info(f"{self.model_name} 모델 로딩 완료")
            except Exception as e:
                self.logger.error(f"모델 로딩 실패: {e}")
                raise
    
    def get_embeddings(self, texts: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        """
        텍스트(들)의 임베딩을 생성합니다.
        
        Args:
            texts: 단일 텍스트 또는 텍스트 리스트
            
        Returns:
            np.ndarray: 임베딩 벡터(들)
        """
        self._load_model()
        
        try:
            # 입력이 단일 문자열인 경우
            if isinstance(texts, str):
                embeddings = self.model.encode([texts], normalize_embeddings=True)
                return embeddings[0]  # 첫 번째 벡터 반환
            
            # 입력이 리스트인 경우
            embeddings = self.model.encode(texts, normalize_embeddings=True)
            return embeddings
            
        except Exception as e:
            self.logger.error(f"임베딩 생성 실패: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """
        임베딩 벡터의 차원을 반환합니다.
        
        Returns:
            int: 임베딩 차원 (환경변수에서 설정)
        """
        return settings.EMBEDDING_DIMENSIONS
    
    def batch_encode(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        대량의 텍스트를 배치로 처리하여 임베딩을 생성합니다.
        
        Args:
            texts: 텍스트 리스트
            batch_size: 배치 크기
            
        Returns:
            List[np.ndarray]: 임베딩 리스트
        """
        self._load_model()
        
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                batch_embeddings = self.model.encode(
                    batch, 
                    normalize_embeddings=True,
                    batch_size=batch_size
                )
                all_embeddings.extend(batch_embeddings)
                
                # 진행률 로그
                processed = min(i + batch_size, len(texts))
                self.logger.info(f"임베딩 진행률: {processed}/{len(texts)} ({processed/len(texts)*100:.1f}%)")
                
            except Exception as e:
                self.logger.error(f"배치 {i//batch_size + 1} 처리 실패: {e}")
                # 실패한 배치는 None으로 채우기
                all_embeddings.extend([None] * len(batch))
        
        return all_embeddings
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        두 임베딩 간의 코사인 유사도를 계산합니다.
        
        Args:
            embedding1: 첫 번째 임베딩
            embedding2: 두 번째 임베딩
            
        Returns:
            float: 코사인 유사도 (-1 ~ 1)
        """
        try:
            # 정규화된 벡터의 내적 = 코사인 유사도
            similarity = np.dot(embedding1, embedding2)
            return float(similarity)
        except Exception as e:
            self.logger.error(f"유사도 계산 실패: {e}")
            return 0.0
    
    def unload_model(self):
        """메모리에서 모델을 해제합니다."""
        if self.model is not None:
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.logger.info("BGE-M3 모델이 메모리에서 해제되었습니다.")


# 전역 임베딩 서비스 인스턴스 (싱글톤 패턴)
_embedding_service: Optional[BGEEmbeddingService] = None

def get_embedding_service() -> BGEEmbeddingService:
    """임베딩 서비스 인스턴스를 반환합니다."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = BGEEmbeddingService()
    return _embedding_service