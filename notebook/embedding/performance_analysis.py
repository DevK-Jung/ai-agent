"""
임베딩 기반 검색 성능 분석 스크립트

주피터 노트북 없이도 성능 분석을 실행할 수 있는 스탠드얼론 스크립트입니다.
CI/CD 파이프라인이나 정기 성능 모니터링에 활용할 수 있습니다.
"""

import sys
import os
import numpy as np
import time
import json
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from app.infra.ai.embedding_service import BGEEmbeddingService
from app.dependencies import get_embedding_service


@dataclass
class PerformanceMetrics:
    """성능 측정 결과를 담는 데이터 클래스"""
    avg_similarity: float
    max_similarity: float
    std_similarity: float
    embedding_time_ms: float
    search_time_ms: float
    batch_speedup: float
    prefix_improvement_pct: float
    optimal_k: int
    optimal_threshold: float


class EmbeddingPerformanceAnalyzer:
    """임베딩 기반 검색 성능 분석기"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.test_passages = [
            "데이터베이스는 정보를 체계적으로 저장하고 관리하는 시스템입니다. MariaDB는 MySQL의 포크로 개발된 관계형 데이터베이스입니다.",
            "인공지능은 컴퓨터가 인간의 지능을 모방하는 기술입니다. 머신러닝과 딥러닝이 주요 방법론입니다.",
            "파이썬은 간결하고 읽기 쉬운 프로그래밍 언어입니다. 데이터 과학과 웹 개발에 널리 사용됩니다.",
            "클라우드 컴퓨팅은 인터넷을 통해 컴퓨팅 자원을 제공하는 서비스입니다. AWS, Azure, GCP가 대표적입니다.",
            "FastAPI는 현대적이고 빠른 웹 API 프레임워크입니다. 자동 문서 생성과 타입 힌트를 지원합니다.",
            "벡터 데이터베이스는 고차원 벡터를 효율적으로 저장하고 검색하는 특수한 데이터베이스입니다.",
            "자연어 처리(NLP)는 컴퓨터가 인간의 언어를 이해하고 처리하는 기술입니다. 번역, 요약, 감정 분석 등에 활용됩니다.",
            "임베딩은 단어나 문장을 고차원 벡터로 표현하는 방법입니다. 의미적 유사성을 수치로 측정할 수 있습니다.",
            "PostgreSQL은 강력한 오픈소스 관계형 데이터베이스입니다. pgvector 확장으로 벡터 검색을 지원합니다.",
            "검색 엔진 최적화(SEO)는 웹사이트가 검색 결과에서 높은 순위를 얻도록 하는 방법입니다."
        ]
        
        self.test_queries = [
            "데이터베이스 관리",
            "머신러닝 기술", 
            "웹 API 개발",
            "벡터 기반 검색",
            "자연어 처리"
        ]

    def cosine_similarity_matrix(self, queries: np.ndarray, passages: np.ndarray) -> np.ndarray:
        """코사인 유사도 매트릭스 계산"""
        return np.dot(queries, passages.T)

    def get_top_k_results(self, similarity_matrix: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Top-K 결과 추출"""
        top_k_indices = np.argsort(-similarity_matrix, axis=1)[:, :k]
        top_k_scores = np.take_along_axis(similarity_matrix, top_k_indices, axis=1)
        return top_k_indices, top_k_scores

    def analyze_embeddings(self) -> Dict[str, Any]:
        """임베딩 기본 분석"""
        print("📊 임베딩 생성 및 기본 분석...")
        
        # Passage 임베딩 생성 (BGE-M3 최적화)
        passage_embeddings = self.embedding_service.encode_passages(self.test_passages)
        passage_embeddings_array = np.array(passage_embeddings)
        
        # 쿼리 임베딩 생성
        query_embeddings = [self.embedding_service.encode_query(q) for q in self.test_queries]
        query_embeddings_array = np.array(query_embeddings)
        
        # 유사도 계산
        similarity_matrix = self.cosine_similarity_matrix(query_embeddings_array, passage_embeddings_array)
        
        return {
            'similarity_matrix': similarity_matrix,
            'passage_embeddings': passage_embeddings_array,
            'query_embeddings': query_embeddings_array,
            'stats': {
                'avg_similarity': float(similarity_matrix.mean()),
                'max_similarity': float(similarity_matrix.max()),
                'std_similarity': float(similarity_matrix.std()),
                'min_similarity': float(similarity_matrix.min())
            }
        }

    def benchmark_performance(self) -> Dict[str, float]:
        """성능 벤치마크"""
        print("⚡ 성능 벤치마크 실행...")
        
        test_texts = ["테스트 문장입니다."] * 100
        
        # 단일 임베딩 성능
        start_time = time.time()
        for text in test_texts[:10]:
            self.embedding_service.encode_passage(text)
        single_time = (time.time() - start_time) / 10
        
        # 배치 임베딩 성능
        start_time = time.time()
        self.embedding_service.encode_passages(test_texts, batch_size=32)
        batch_time = time.time() - start_time
        
        # 검색 성능
        query_emb = self.embedding_service.encode_query("테스트 쿼리")
        passage_embs = np.random.randn(1000, 1024)  # 가상의 1000개 문서
        
        start_time = time.time()
        similarities = self.cosine_similarity_matrix(
            query_emb.reshape(1, -1), passage_embs
        )
        top_k_indices, top_k_scores = self.get_top_k_results(similarities, k=5)
        search_time = time.time() - start_time
        
        speedup = (single_time * len(test_texts)) / batch_time
        
        return {
            'single_embedding_ms': single_time * 1000,
            'batch_embedding_total_s': batch_time,
            'batch_embedding_per_doc_ms': (batch_time / len(test_texts)) * 1000,
            'search_time_ms': search_time * 1000,
            'batch_speedup': speedup
        }

    def test_prefix_effect(self) -> Dict[str, Any]:
        """BGE-M3 Prefix 효과 테스트"""
        print("🔬 BGE-M3 Prefix 효과 분석...")
        
        # Prefix 있는 임베딩
        with_prefix_passages = self.embedding_service.encode_passages(self.test_passages)
        with_prefix_queries = [self.embedding_service.encode_query(q) for q in self.test_queries]
        
        # Prefix 없는 임베딩
        without_prefix_passages = self.embedding_service.get_embeddings(self.test_passages)
        without_prefix_queries = [self.embedding_service.get_embeddings(q) for q in self.test_queries]
        
        # 유사도 계산
        with_prefix_sim = self.cosine_similarity_matrix(
            np.array(with_prefix_queries), np.array(with_prefix_passages)
        )
        without_prefix_sim = self.cosine_similarity_matrix(
            np.array(without_prefix_queries), np.array(without_prefix_passages)
        )
        
        # 개선 효과 계산
        improvement = (with_prefix_sim.mean() - without_prefix_sim.mean()) / without_prefix_sim.mean() * 100
        
        return {
            'with_prefix_avg': float(with_prefix_sim.mean()),
            'without_prefix_avg': float(without_prefix_sim.mean()),
            'improvement_pct': float(improvement),
            'with_prefix_max': float(with_prefix_sim.max()),
            'without_prefix_max': float(without_prefix_sim.max())
        }

    def optimize_parameters(self, similarity_matrix: np.ndarray) -> Dict[str, Any]:
        """최적 파라미터 탐색"""
        print("🎯 최적 파라미터 탐색...")
        
        k_values = [1, 3, 5, 10, 20]
        thresholds = [0.3, 0.5, 0.6, 0.7, 0.8]
        
        # Top-K 최적화
        best_k = 5
        best_k_score = 0
        k_results = {}
        
        for k in k_values:
            top_k_indices, top_k_scores = self.get_top_k_results(similarity_matrix, k)
            avg_top_score = top_k_scores[:, 0].mean()
            avg_all_scores = top_k_scores.mean()
            
            # 종합 점수 (최고 점수 70% + 전체 점수 30%)
            combined_score = 0.7 * avg_top_score + 0.3 * avg_all_scores
            
            k_results[k] = {
                'avg_top_score': float(avg_top_score),
                'avg_all_scores': float(avg_all_scores),
                'combined_score': float(combined_score)
            }
            
            if combined_score > best_k_score:
                best_k_score = combined_score
                best_k = k
        
        # Threshold 최적화
        best_threshold = 0.6
        best_threshold_score = 0
        threshold_results = {}
        
        for threshold in thresholds:
            results_count = []
            scores_above_threshold = []
            
            for query_idx in range(similarity_matrix.shape[0]):
                query_scores = similarity_matrix[query_idx]
                valid_scores = query_scores[query_scores >= threshold]
                results_count.append(len(valid_scores))
                scores_above_threshold.extend(valid_scores)
            
            avg_count = np.mean(results_count)
            avg_score = np.mean(scores_above_threshold) if scores_above_threshold else 0
            
            # 최적 결과 수는 3-5개
            count_penalty = abs(avg_count - 4) / 4
            combined_score = avg_score * (1 - count_penalty * 0.3)
            
            threshold_results[threshold] = {
                'avg_count': float(avg_count),
                'avg_score': float(avg_score),
                'combined_score': float(combined_score)
            }
            
            if combined_score > best_threshold_score:
                best_threshold_score = combined_score
                best_threshold = threshold
        
        return {
            'optimal_k': best_k,
            'optimal_threshold': best_threshold,
            'k_analysis': k_results,
            'threshold_analysis': threshold_results
        }

    def run_full_analysis(self) -> PerformanceMetrics:
        """전체 성능 분석 실행"""
        print("🚀 임베딩 검색 성능 분석 시작")
        print("=" * 50)
        
        # 1. 기본 임베딩 분석
        embedding_results = self.analyze_embeddings()
        
        # 2. 성능 벤치마크
        performance_results = self.benchmark_performance()
        
        # 3. Prefix 효과 분석
        prefix_results = self.test_prefix_effect()
        
        # 4. 파라미터 최적화
        optimization_results = self.optimize_parameters(embedding_results['similarity_matrix'])
        
        # 5. 결과 종합
        metrics = PerformanceMetrics(
            avg_similarity=embedding_results['stats']['avg_similarity'],
            max_similarity=embedding_results['stats']['max_similarity'],
            std_similarity=embedding_results['stats']['std_similarity'],
            embedding_time_ms=performance_results['single_embedding_ms'],
            search_time_ms=performance_results['search_time_ms'],
            batch_speedup=performance_results['batch_speedup'],
            prefix_improvement_pct=prefix_results['improvement_pct'],
            optimal_k=optimization_results['optimal_k'],
            optimal_threshold=optimization_results['optimal_threshold']
        )
        
        # 6. 결과 출력
        self.print_results(metrics, embedding_results, performance_results, 
                          prefix_results, optimization_results)
        
        return metrics

    def print_results(self, metrics: PerformanceMetrics, *result_dicts):
        """결과 출력"""
        embedding_results, performance_results, prefix_results, optimization_results = result_dicts
        
        print("\n📊 분석 결과 요약")
        print("=" * 50)
        
        print(f"\n🎯 검색 품질 지표:")
        print(f"  평균 유사도: {metrics.avg_similarity:.4f}")
        print(f"  최대 유사도: {metrics.max_similarity:.4f}")
        print(f"  표준편차: {metrics.std_similarity:.4f}")
        
        print(f"\n⚡ 성능 지표:")
        print(f"  단일 임베딩 시간: {metrics.embedding_time_ms:.1f}ms")
        print(f"  검색 시간 (1000개 문서): {metrics.search_time_ms:.1f}ms")
        print(f"  배치 처리 속도 향상: {metrics.batch_speedup:.1f}x")
        
        print(f"\n🔬 BGE-M3 Prefix 효과:")
        print(f"  성능 개선: +{metrics.prefix_improvement_pct:.1f}%")
        print(f"  Prefix 있음: {prefix_results['with_prefix_avg']:.4f}")
        print(f"  Prefix 없음: {prefix_results['without_prefix_avg']:.4f}")
        
        print(f"\n🎯 최적 파라미터:")
        print(f"  Top-K: {metrics.optimal_k}")
        print(f"  Threshold: {metrics.optimal_threshold}")
        
        print(f"\n💡 권장 설정:")
        print(f"  - BGE-M3 Prefix: ✅ 필수 사용")
        print(f"  - Top-K 검색: k={metrics.optimal_k}")
        print(f"  - Threshold: {metrics.optimal_threshold}")
        print(f"  - 배치 크기: 32")
        
        print(f"\n🚀 예상 프로덕션 성능:")
        print(f"  - 단일 검색 응답시간: ~{metrics.search_time_ms:.0f}ms")
        print(f"  - 문서당 임베딩 시간: ~{performance_results['batch_embedding_per_doc_ms']:.1f}ms")
        print(f"  - 검색 품질: {metrics.max_similarity:.1%} (최고 유사도)")

    def save_results(self, metrics: PerformanceMetrics, output_path: str = None):
        """결과를 JSON 파일로 저장"""
        if output_path is None:
            output_path = f"embedding_performance_{int(time.time())}.json"
        
        results = {
            'timestamp': time.time(),
            'model': self.embedding_service.model_name,
            'device': self.embedding_service.device,
            'metrics': {
                'avg_similarity': metrics.avg_similarity,
                'max_similarity': metrics.max_similarity,
                'std_similarity': metrics.std_similarity,
                'embedding_time_ms': metrics.embedding_time_ms,
                'search_time_ms': metrics.search_time_ms,
                'batch_speedup': metrics.batch_speedup,
                'prefix_improvement_pct': metrics.prefix_improvement_pct,
                'optimal_k': metrics.optimal_k,
                'optimal_threshold': metrics.optimal_threshold
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 결과 저장: {output_path}")


def main():
    """메인 실행 함수"""
    analyzer = EmbeddingPerformanceAnalyzer()
    
    try:
        metrics = analyzer.run_full_analysis()
        analyzer.save_results(metrics)
        
        print("\n✅ 분석 완료!")
        return metrics
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()