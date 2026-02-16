"""
CSV 파서 구현
"""
import csv
import io
from typing import List
from .base import BaseParser
from .models import ParsedContent, Table, Image


class CSVParser(BaseParser):
    """CSV 파일 전용 파서"""
    
    def get_supported_mime_types(self) -> List[str]:
        return [
            "text/csv",
            "application/csv"
        ]
    
    async def parse(self, file_path: str) -> ParsedContent:
        """CSV 파일에서 구조화된 콘텐츠를 추출합니다."""
        if not self.validate_file(file_path):
            raise ValueError(f"유효하지 않은 CSV 파일: {file_path}")
        
        try:
            # CSV 파일 인코딩 추정 및 읽기
            content = self._read_csv_file(file_path)
            
            # CSV 파싱
            csv_data = self._parse_csv_content(content)
            
            if not csv_data:
                raise ValueError("CSV 파일에서 데이터를 읽을 수 없습니다.")
            
            # 헤더와 데이터 분리
            headers = csv_data[0] if csv_data else []
            rows = csv_data[1:] if len(csv_data) > 1 else []
            
            # 텍스트 형태로 변환 (검색/청킹용)
            full_text = self._convert_to_text(headers, rows)
            
            # 테이블 생성
            table = Table(
                headers=headers,
                rows=rows,
                position={"file": file_path},
                metadata={
                    "extraction_method": "csv_parser",
                    "total_rows": len(rows),
                    "total_columns": len(headers),
                    "file_name": file_path.split('/')[-1]
                }
            )
            
            # 구조 정보
            structure = {
                "total_rows": len(rows),
                "total_columns": len(headers),
                "headers": headers,
                "data_types": self._analyze_data_types(rows, headers) if rows else {}
            }
            
            # 메타데이터
            metadata = {
                "parser": "csv_parser",
                "encoding": "utf-8",  # 성공적으로 읽은 인코딩
                "total_rows": len(rows),
                "total_columns": len(headers),
                "file_size": len(content)
            }
            
            return ParsedContent(
                raw_text=full_text,
                metadata=metadata,
                structure=structure,
                tables=[table],
                images=[]  # CSV에는 이미지가 없음
            )
            
        except Exception as e:
            raise ValueError(f"CSV 파싱 실패: {e}")
    
    def _read_csv_file(self, file_path: str) -> str:
        """CSV 파일을 다양한 인코딩으로 시도하여 읽기"""
        # 한국어 파일에 많이 사용되는 인코딩 순서로 시도
        encodings = ['cp949', 'euc-kr', 'utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    # 내용이 비어있지 않고 한글이 포함되어 있으면 성공으로 간주
                    if content.strip():
                        self.logger.info(f"CSV 파일을 {encoding} 인코딩으로 성공적으로 읽음")
                        return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.logger.warning(f"{encoding} 인코딩으로 읽기 실패: {e}")
                continue
        
        # 모든 인코딩이 실패하면 바이너리로 읽어서 chardet으로 감지 시도
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                if detected['encoding'] and detected['confidence'] > 0.7:
                    encoding = detected['encoding']
                    content = raw_data.decode(encoding)
                    self.logger.info(f"chardet으로 감지된 인코딩 {encoding} (신뢰도: {detected['confidence']:.2f})로 읽기 성공")
                    return content
        except ImportError:
            self.logger.warning("chardet 라이브러리가 설치되지 않아 자동 인코딩 감지를 사용할 수 없습니다")
        except Exception as e:
            self.logger.warning(f"chardet으로 인코딩 감지 실패: {e}")
        
        raise ValueError(f"CSV 파일의 인코딩을 식별할 수 없습니다: {file_path}")
    
    def _parse_csv_content(self, content: str) -> List[List[str]]:
        """CSV 내용을 파싱하여 2차원 리스트로 변환"""
        try:
            # CSV 방언 자동 감지
            sample = content[:1024]
            sniffer = csv.Sniffer()
            
            # 구분자 감지 시도
            try:
                dialect = sniffer.sniff(sample, delimiters=',;\t')
            except csv.Error:
                # 기본값으로 콤마 사용
                dialect = csv.excel
            
            # CSV 파싱
            csv_reader = csv.reader(io.StringIO(content), dialect=dialect)
            data = []
            
            for row_idx, row in enumerate(csv_reader):
                # 빈 행 건너뛰기
                if not any(cell.strip() for cell in row):
                    continue
                
                # 행 데이터 정리
                cleaned_row = [cell.strip() for cell in row]
                data.append(cleaned_row)
                
                # 너무 많은 행은 제한 (메모리 보호)
                if row_idx > 10000:
                    self.logger.warning(f"CSV 파일이 너무 큽니다. 첫 10,000행만 처리합니다.")
                    break
            
            return data
            
        except Exception as e:
            raise ValueError(f"CSV 내용 파싱 실패: {e}")
    
    def _convert_to_text(self, headers: List[str], rows: List[List[str]]) -> str:
        """CSV 데이터를 텍스트 형태로 변환"""
        text_lines = []
        
        # 헤더 추가
        if headers:
            text_lines.append(" | ".join(headers))
            text_lines.append("-" * len(" | ".join(headers)))
        
        # 데이터 행 추가 (너무 길어지지 않도록 제한)
        max_preview_rows = 100
        for i, row in enumerate(rows[:max_preview_rows]):
            if len(row) == len(headers):  # 컬럼 수가 맞는 경우만
                text_lines.append(" | ".join(row))
            else:
                # 컬럼 수가 맞지 않으면 빈 값으로 채우거나 자르기
                padded_row = row + [""] * (len(headers) - len(row))
                padded_row = padded_row[:len(headers)]
                text_lines.append(" | ".join(padded_row))
        
        if len(rows) > max_preview_rows:
            text_lines.append(f"... ({len(rows) - max_preview_rows}행 더 있음)")
        
        return "\n".join(text_lines)
    
    def _analyze_data_types(self, rows: List[List[str]], headers: List[str]) -> dict:
        """각 컬럼의 데이터 타입을 분석"""
        if not rows or not headers:
            return {}
        
        data_types = {}
        
        # 각 컬럼별로 데이터 타입 분석 (처음 몇 행만 샘플링)
        sample_size = min(100, len(rows))
        
        for col_idx, header in enumerate(headers):
            col_values = []
            
            # 해당 컬럼의 값들 수집
            for row in rows[:sample_size]:
                if col_idx < len(row) and row[col_idx].strip():
                    col_values.append(row[col_idx].strip())
            
            if not col_values:
                data_types[header] = "empty"
                continue
            
            # 데이터 타입 추정
            numeric_count = 0
            date_count = 0
            
            for value in col_values:
                # 숫자 체크
                try:
                    float(value.replace(",", ""))
                    numeric_count += 1
                    continue
                except ValueError:
                    pass
                
                # 날짜 체크 (간단한 패턴)
                if any(pattern in value for pattern in ["-", "/", "년", "월", "일"]):
                    date_count += 1
            
            total_values = len(col_values)
            
            if numeric_count / total_values > 0.8:
                data_types[header] = "numeric"
            elif date_count / total_values > 0.5:
                data_types[header] = "date"
            else:
                data_types[header] = "text"
        
        return data_types