"""
PDF 파서 구현
"""
from typing import List
from .base import BaseParser
from .models import ParsedContent, Table, Image


class PDFParser(BaseParser):
    """PDF 파일 전용 파서"""
    
    def get_supported_mime_types(self) -> List[str]:
        return ["application/pdf"]
    
    async def parse(self, file_path: str) -> ParsedContent:
        """PDF 파일에서 구조화된 콘텐츠를 추출합니다."""
        if not self.validate_file(file_path):
            raise ValueError(f"유효하지 않은 PDF 파일: {file_path}")
        
        try:
            # 1차 시도: PyMuPDF 사용 (가장 강력)
            return await self._parse_with_pymupdf(file_path)
        except ImportError:
            self.logger.warning("PyMuPDF가 없습니다. PyPDF2로 fallback합니다.")
            return await self._parse_with_pypdf2(file_path)
        except Exception as e:
            self.logger.warning(f"PyMuPDF 파싱 실패: {e}. PyPDF2로 fallback합니다.")
            return await self._parse_with_pypdf2(file_path)
    
    async def _parse_with_pymupdf(self, file_path: str) -> ParsedContent:
        """PyMuPDF를 사용한 고급 PDF 파싱"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            
            # 텍스트 추출
            full_text = ""
            tables = []
            images = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 페이지 텍스트 추출
                page_text = page.get_text()
                if page_text.strip():
                    full_text += f"[페이지 {page_num + 1}]\n{page_text}\n\n"
                
                # 테이블 감지 (PyMuPDF 1.23+에서 지원)
                try:
                    page_tables = page.find_tables()
                    for table in page_tables:
                        table_data = table.extract()
                        if table_data and len(table_data) > 0:
                            headers = table_data[0] if table_data else []
                            rows = table_data[1:] if len(table_data) > 1 else []
                            
                            tables.append(Table(
                                headers=headers,
                                rows=rows,
                                position={"page": page_num + 1},
                                metadata={"extraction_method": "pymupdf"}
                            ))
                except AttributeError:
                    # 구버전 PyMuPDF는 find_tables 미지원
                    pass
                
                # 이미지 정보 추출
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    images.append(Image(
                        name=f"image_{page_num + 1}_{img_index + 1}",
                        format="unknown",  # 추후 개선 가능
                        position={"page": page_num + 1},
                        metadata={"extraction_method": "pymupdf"}
                    ))
            
            # 메타데이터 추출
            metadata = {
                "page_count": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "parser": "pymupdf"
            }
            
            doc.close()
            
            return ParsedContent(
                raw_text=full_text.strip(),
                metadata=metadata,
                structure={"type": "pdf", "pages": len(doc)},
                tables=tables,
                images=images
            )
            
        except ImportError:
            raise ImportError("PyMuPDF가 설치되지 않았습니다: pip install PyMuPDF")
        except Exception as e:
            raise ValueError(f"PyMuPDF PDF 파싱 실패: {e}")
    
    async def _parse_with_pypdf2(self, file_path: str) -> ParsedContent:
        """PyPDF2를 사용한 기본 PDF 파싱 (fallback)"""
        try:
            import PyPDF2
            
            full_text = ""
            page_count = 0
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            full_text += f"[페이지 {page_num + 1}]\n{page_text}\n\n"
                    except Exception as e:
                        self.logger.warning(f"페이지 {page_num + 1} 추출 실패: {e}")
                        continue
                
                # 메타데이터 추출
                metadata = {
                    "page_count": page_count,
                    "parser": "pypdf2"
                }
                
                # PyPDF2 메타데이터 추출 (가능한 경우)
                try:
                    if pdf_reader.metadata:
                        metadata.update({
                            "title": pdf_reader.metadata.get("/Title", ""),
                            "author": pdf_reader.metadata.get("/Author", ""),
                            "subject": pdf_reader.metadata.get("/Subject", ""),
                            "creator": pdf_reader.metadata.get("/Creator", "")
                        })
                except Exception:
                    pass
            
            return ParsedContent(
                raw_text=full_text.strip(),
                metadata=metadata,
                structure={"type": "pdf", "pages": page_count},
                tables=[],  # PyPDF2로는 테이블 추출 어려움
                images=[]   # PyPDF2로는 이미지 정보 추출 어려움
            )
            
        except ImportError:
            raise ImportError("PyPDF2가 설치되지 않았습니다: pip install PyPDF2")
        except Exception as e:
            raise ValueError(f"PyPDF2 PDF 파싱 실패: {e}")