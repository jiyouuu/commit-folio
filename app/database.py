#./database.py
from sqlmodel import Session
from dotenv import load_dotenv
import os
#SQLAlchemy의 비동기 엔지과 비동기 세션을 명시적으로 임포트
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker #세션 팩토리 생성을 위해 필요
from sqlalchemy.ext.asyncio import AsyncSession
# .env file load
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL 환경변수가 설정되지 않았습니다.")

# 데이터 베이스 엔진생성: create_engine 대신 create_async_engine 사용
# echo=-TRue는 SQL 쿼리를 콘솔에 출력하여 디버깅 도움을 줌
engine = create_async_engine(DATABASE_URL, echo=True)

# 비동기 세션 팩토리 생성
# SQLModel을 사용하므로, sqlmodel,Session을 class_로 지정함.
# 내부적으로 SQLAlchem의 AsyncSession을 사용
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession, #SQLModel의 Session크래스를 사용(내부적으로 AsyncSession 래핑)
    expire_on_commit=False, #커밋 후 객체 상태 유지(FastAPI 응답에 유리)
    autocommit=False,
    autoflush=False
)

#의존성 주입을 위한 함수(main.py에서 사용)
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session