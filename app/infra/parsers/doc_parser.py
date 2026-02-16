"""
DOC 파서 구현 (구 버전 MS Word 문서)
"""
from typing import List
from .base import BaseParser
from .models import ParsedContent, Table, Image


class DOCParser(BaseParser):
    """DOC 파일 전용 파서 (구 버전 MS Word)"""
    
    def get_supported_mime_types(self) -> List[str]:
        return [
            "application/msword",
            "application/vnd.ms-word"
        ]
    
    async def parse(self, file_path: str) -> ParsedContent:
        """DOC 파일에서 구조화된 콘텐츠를 추출합니다."""
        if not self.validate_file(file_path):
            raise ValueError(f"유효하지 않은 DOC 파일: {file_path}")
        
        try:
            # python-docx2txt 사용 (가장 안정적)
            extracted_text = self._extract_with_docx2txt(file_path)
            
            if not extracted_text.strip():
                # fallback으로 antiword 시도
                extracted_text = self._extract_with_antiword(file_path)
            
            if not extracted_text.strip():
                # 최후 수단으로 olefile + 간단한 텍스트 추출
                extracted_text = self._extract_with_olefile(file_path)
            
            if not extracted_text.strip():
                raise ValueError("DOC 파일에서 텍스트를 추출할 수 없습니다.")
            
            # 메타데이터 및 구조 정보
            metadata = {
                "parser": "doc_parser",
                "extraction_method": "docx2txt/antiword/olefile",
                "file_name": file_path.split('/')[-1]
            }
            
            structure = {
                "paragraphs": len([p for p in extracted_text.split('\n') if p.strip()]),
                "characters": len(extracted_text),
                "words": len(extracted_text.split())
            }
            
            return ParsedContent(
                raw_text=extracted_text.strip(),
                metadata=metadata,
                structure=structure,
                tables=[],  # DOC에서 테이블 추출은 복잡하므로 일단 제외
                images=[]   # DOC에서 이미지 추출도 복잡하므로 일단 제외
            )
            
        except Exception as e:
            raise ValueError(f"DOC 파싱 실패: {e}")
    
    def _extract_with_docx2txt(self, file_path: str) -> str:
        """docx2txt 라이브러리를 사용한 텍스트 추출"""
        try:
            import docx2txt
            text = docx2txt.process(file_path)
            self.logger.info("docx2txt를 사용하여 DOC 파일 파싱 성공")
            return text or ""
        except ImportError:
            self.logger.warning("docx2txt가 설치되지 않음. antiword로 시도")
            return ""
        except Exception as e:
            self.logger.warning(f"docx2txt 파싱 실패: {e}")
            return ""
    
    def _extract_with_antiword(self, file_path: str) -> str:
        """antiword 명령어를 사용한 텍스트 추출"""
        try:
            import subprocess
            result = subprocess.run(
                ['antiword', file_path], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            if result.returncode == 0:
                self.logger.info("antiword를 사용하여 DOC 파일 파싱 성공")
                return result.stdout
            else:
                self.logger.warning(f"antiword 실패: {result.stderr}")
                return ""
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            self.logger.warning(f"antiword 사용 불가: {e}")
            return ""
        except Exception as e:
            self.logger.warning(f"antiword 파싱 실패: {e}")
            return ""
    
    def _extract_with_olefile(self, file_path: str) -> str:
        """olefile을 사용한 기본적인 텍스트 추출"""
        try:
            import olefile
            
            if not olefile.isOleFile(file_path):
                return ""
            
            ole = olefile.OleFileIO(file_path)
            
            # WordDocument 스트림에서 텍스트 추출 시도
            if ole.exists('WordDocument'):
                with ole.open('WordDocument') as stream:
                    data = stream.read()
                    
                    # 매우 기본적인 텍스트 추출 (완벽하지 않음)
                    text = ""
                    for i in range(0, len(data) - 1, 2):
                        try:
                            char = data[i:i+2].decode('utf-16le', errors='ignore')
                            if char.isprintable() and char not in '\x00\x01\x02\x03\x04\x05\x06\x07\x08':
                                text += char
                        except:
                            continue
                    
                    # 연속된 공백 정리
                    import re
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    ole.close()
                    
                    if text:
                        self.logger.info("olefile을 사용하여 DOC 파일 파싱 성공")
                        return text
            
            ole.close()
            return ""
            
        except ImportError:
            self.logger.warning("olefile이 설치되지 않음")
            return ""
        except Exception as e:
            self.logger.warning(f"olefile 파싱 실패: {e}")
            return ""
    
    def _extract_with_textract(self, file_path: str) -> str:
        """textract 라이브러리를 사용한 텍스트 추출 (추가 옵션)"""
        try:
            import textract
            text = textract.process(file_path).decode('utf-8')
            self.logger.info("textract를 사용하여 DOC 파일 파싱 성공")
            return text
        except ImportError:
            self.logger.warning("textract이 설치되지 않음")
            return ""
        except Exception as e:
            self.logger.warning(f"textract 파싱 실패: {e}")
            return ""