#Dockerfile
FROM python:3.10-slim-buster

# 실제로 운영할 폴더 - 앞으로 모든 작업은 /app 폴더에서 하겠다
WORKDIR /app  


# gcc : C 컴파일러 (파이썬 c 확장 모듈 빌드에 필요)
# pkg-config : 라이브러리 정보 찾기 도구 (mysqlclient 빌드에 필요)
# python3-dev : 파이썬 개발 헤더 파일 (파이썬 c 확장 모듈 빌드에 필요)
RUN apt-get update && \
    apt-get install -y default-libmysqlclient-dev gcc pkg-config python3-dev && \
    rm -rf /var/lib/apt/lists/*     
    # 설치 후 캐시 파일 삭제하여 이미지 크기 줄이기



# 호스트(네 컴퓨터)에 있는 requirements.txt 파일을 컨테이너의 /app 폴더로 복사
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt


# 프로젝트 안에 있는 app 폴더를 도커에 있는 컨테이너의 /app/ 폴더로 복사
COPY ./app /app/

# 컨테이너 내부에서 8000번 포트를 열어주겠다
EXPOSE 8000

# 컨테이너를 실행할 때 실제로 실행되는 명령어

# uvicorn으로 FastAPI 앱을 실행하겠다는 의미
# main:app → main.py 파일 안에 있는 app 객체를 실행한다는 뜻.
# --host 0.0.0.0 → 외부에서도 접속 가능하게 열어줌.
# --port 8000 → 8000번 포트에서 실행함.

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]