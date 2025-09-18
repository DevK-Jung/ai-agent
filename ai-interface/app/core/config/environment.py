from enum import Enum


class Environment(str, Enum):
    """환경 프로파일 정의"""
    DEVELOPMENT = "development"
    LOCAL = "local"
    PRODUCTION = "production"
    TESTING = "testing"

    @property
    def env_file(self) -> str:
        """환경에 따른 .env 파일 경로 반환"""
        env_files = {
            self.DEVELOPMENT: ".env.development",
            self.LOCAL: ".env.local",
            self.PRODUCTION: ".env.production",
            self.TESTING: ".env.testing"
        }
        return env_files[self]

    @property
    def is_debug(self) -> bool:
        """디버그 모드 여부"""
        return self in [self.DEVELOPMENT, self.LOCAL, self.TESTING]

    @property
    def default_log_level(self) -> str:
        """환경별 기본 로그 레벨"""
        if self == self.PRODUCTION:
            return "WARNING"
        return "DEBUG"

    @property
    def default_host(self) -> str:
        """환경별 기본 호스트"""
        if self == self.PRODUCTION:
            return "0.0.0.0"
        return "127.0.0.1"