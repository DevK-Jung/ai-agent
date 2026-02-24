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
    
    def encode_query(self, query: str) -> np.ndarray:
        """
        검색 질의용 임베딩 생성 (BGE-M3 최적화)
        
        Args:
            query: 검색 질의 텍스트
            
        Returns:
            np.ndarray: 임베딩 벡터
        """
        return self.get_embeddings(f"query: {query}")
    
    def encode_passage(self, text: str) -> np.ndarray:
        """
        문서 청크용 임베딩 생성 (BGE-M3 최적화)
        
        Args:
            text: 문서 텍스트
            
        Returns:
            np.ndarray: 임베딩 벡터
        """
        return self.get_embeddings(f"passage: {text}")
    
    def encode_passages(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        여러 문서 청크의 임베딩 일괄 생성 (BGE-M3 최적화 + 배치 처리)
        
        Args:
            texts: 문서 텍스트 리스트
            batch_size: 배치 크기
            
        Returns:
            List[np.ndarray]: 임베딩 벡터 리스트
        """
        prefixed_texts = [f"passage: {text}" for text in texts]
        self._load_model()
        
        all_embeddings = []
        
        for i in range(0, len(prefixed_texts), batch_size):
            batch = prefixed_texts[i:i + batch_size]
            try:
                batch_embeddings = self.model.encode(
                    batch,
                    normalize_embeddings=True,
                    batch_size=batch_size
                )
                all_embeddings.extend(batch_embeddings)
                
                # 진행률 로그
                processed = min(i + batch_size, len(prefixed_texts))
                self.logger.info(f"임베딩 진행률: {processed}/{len(prefixed_texts)} ({processed/len(prefixed_texts)*100:.1f}%)")
                
            except Exception as e:
                self.logger.error(f"배치 {i//batch_size + 1} 처리 실패: {e}")
                # 실패한 배치는 None으로 채우기
                all_embeddings.extend([None] * len(batch))
        
        return all_embeddings
    
    def get_embedding_dimension(self) -> int:
        """
        임베딩 벡터의 차원을 반환합니다.
        
        Returns:
            int: 임베딩 차원 (모델에서 직접 가져옴)
        """
        self._load_model()
        return self.model.get_sentence_embedding_dimension()
    
    
    
    def unload_model(self):
        """메모리에서 모델을 해제합니다."""
        if self.model is not None:
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.logger.info("BGE-M3 모델이 메모리에서 해제되었습니다.")

