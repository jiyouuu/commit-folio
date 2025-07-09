#./app/main.py
from fastapi import FastAPI, Query, Depends, HTTPException, status, Request
from typing import Optional, List
#sqlmodel 핵심 기능
from sqlmodel import SQLModel, Field, create_engine, Session, select, Relationship
from sqlalchemy import Text, Integer, Column,literal_column
from sqlalchemy import func

from sqlalchemy.ext.asyncio import AsyncSession
#pydantic BaseModel 출력용으로 사용 => API 입출력 데이터 정의 (직렬화/역직렬화)
from pydantic import BaseModel


# html 인식
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.exc import OperationalError        
#selectinlload
from sqlalchemy.orm import selectinload

# AsyncSessionLocal은 startup에서 데이터 삽입용
from database import engine, AsyncSessionLocal, get_session
import logging


# 로깅 설정 코드-------------------------------------------------------------------------------------
# FastAPI 서버 실행 중 발생하는 정보, 오류, 이벤트 등을 콘솔에 보기 좋게 출력하도록 설정하는 것
logger = logging.getLogger(__name__) # __name__을 사용하면 모듈 이름을 로거 이름으로 가집니다.
logger.setLevel(logging.INFO) # 여기서는 INFO 레벨 이상만 기록하도록 설정

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# 로거에 핸들러 추가
# 중복 추가 방지를 위해 이미 핸들러가 없으면 추가
if not logger.handlers:
    logger.addHandler(handler)

# SQLModel을 이용해서 DB 테이블을 정의--------------------------------------------------------------------------------------------------
class Users(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    profile:Optional["Profiles"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "primaryjoin":"Users.id == Profiles.user_id",
            "foreign_keys":"[Profiles.user_id]",
            "uselist":False,
            "cascade":"all, delete-orphan"
        }
    )

    posts:Optional["Posts"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "primaryjoin":"Users.id == Posts.user_id",
            "foreign_keys":"[Posts.user_id]",
            "uselist":False,
            "cascade":"all, delete-orphan"
        }
    )

#--------------------------------------------------------------------------------------------------
class Profiles(SQLModel, table=True):
    # user_id:Optional[int] = Field(default=None, primary_key=True)
    user_id :Optional[int] = Field(sa_column= Column(Integer,primary_key = True, autoincrement=False))
    bio: Optional[str] = Field(sa_type=Text, nullable=True)
    phone:Optional[str] = Field(default=None, max_length=20, nullable=True)

    user:Optional["Users"] = Relationship(
        back_populates="profile",
        sa_relationship_kwargs={
            "primaryjoin":"Profiles.user_id == Users.id",
            "foreign_keys":"[Profiles.user_id]",
            "uselist":False
        }
    )
#--------------------------------------------------------------------------------------------------
class Posts(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default=None, max_length=100)
    content: Optional[str] = Field(default=None, sa_type=Text, nullable=True)
    user_id: Optional[int] = Field(default=None, nullable=True)
    cnt: Optional[int] = Field(default=0, ge=0)
    
    user:Optional["Users"] = Relationship(
        back_populates="posts",
        sa_relationship_kwargs={
            "primaryjoin":"Posts.user_id == Users.id",
            "foreign_keys":"[Posts.user_id]",
        }
    )

#이 부분의 용도를 찾아라!!!!!!!!!!!!!!!!!!!--------------------------------------------------------------------------------------------------
class UsersProfile(BaseModel):
    id: int
    username:str
    email:str
    # phone과 bio 필드를 최상위 레벨에 Optional로 추가
    phone: Optional[str] = None
    bio: Optional[str] = None

class UserProfile(BaseModel):
    id: int
    username:str
    email:str
    profile: Optional[Profiles] = None
    class Config:
        from_attributes:True
# -----------------------------	게시글을 리스트로 보여줄 때 예쁘게 포맷팅한 용도 (UserPosts 내부에서 사용됨)------------------------------
class PostOutput(BaseModel):
    id: int
    title: str
    content: Optional[str] = None
    cnt: int
    class Config:
        from_attributes:True
class UserPosts(BaseModel):
    id: int
    username:str
    email:str
    posts: List[PostOutput] 
    class Config:
        from_attributes:True



# ------------------------------사용자 조회 시 사용하는 단순 응답용 모델 (GET /users/{id} 등) ------------------------------
class UserRead(BaseModel):
    id:int
    username:str
    email:str
    class Config:
        from_attributes:True # orm 객체에서 딕서녀리 용으로 속성 가져오기 허용

# ------------------------------	프로필 정보 조회 시 사용하는 응답용 모델 (GET /profiles/{user_id} 등)------------------------------
class ProfileRead(BaseModel):
    user_id: int
    bio:Optional[str] = None
    phone:Optional[str] = None
    class Config:
        from_attributes:True   # orm 객체에서 속성 가져오기 허용

# ------------------------------	게시글 조회 시 사용하는 단순 응답용 모델 (GET /posts/ 등) ------------------------------
class PostRead(BaseModel):
    id:int
    title:str
    content:Optional[str] = None
    user_id:Optional[int] = None
    cnt:Optional[int] = None

    class Config:
        from_attributes = True


# ------------------------------사용자 회원가입 시 클라이언트에서 보낸 데이터를 받을 때 사용 (POST /users/) ------------------------------
class UserCreate(SQLModel):
    username: str
    email: str  
    phone: Optional[str] = None
    bio: Optional[str] = None


# -----------------------------프로필 수정 시 받는 데이터용 (PATCH /profile/edit/{user_id}) ------------------------------------------
class ProfileUpdate(BaseModel):
    user_id: int
    bio: Optional[str] = None   
    phone: Optional[str] = None


#-------------------------게시물 작성시 사용--------------------------------
class PostWrite(BaseModel):
    title:str
    content: Optional[str] = None   

# ---- 페이징 할려고 만듦 
class PostListResponse(BaseModel):
    total: int
    posts: List[PostRead]



# -----------------------------------------------------------------------------------------------------
app = FastAPI()
templates= Jinja2Templates(directory='templates')
@app.on_event("startup")
async def on_startup():
    #SQLModel.metadata.create_all(engine)
    async with engine.begin() as conn: # 비동기 컨넥션 시작
        await conn.run_sync(SQLModel.metadata.create_all) 


# -------------------------------------사용자 등록 HTML -------------------------------------------------------------------------------------------
@app.get('/register',response_class="HTMLResponse")
async def get_register_page(request:Request):
    return templates.TemplateResponse('register.html',{'request':request})



# -----------------사용자 등록해서 DB 저장 -----------------------------------------------------
@app.post('/users/', response_model=Users, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, session: Session = Depends(get_session)):
    # 이메일 중복 체크
    existing_user = await session.execute(select(Users).where(Users.email == user.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

    # Pydantic 모델이나 딕셔너리 등으로 받은 데이터를 Users SQLModel 인스턴스로 검증하고 변환하는 작업
    db_user = Users.model_validate(user)
    try:
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        # 프로필 생성
        db_profile = Profiles(user_id=db_user.id, bio="기본 소개", phone=None)
        session.add(db_profile)
        await session.commit()
        await session.refresh(db_profile)
        logger.info(f"사용자 명: {db_user.username}")
        return db_user
    except Exception as e:
        await session.rollback()  # 여기 꼭 await 붙여야 함
        logger.error(f"사용자 생성 오류: {e}")
        raise HTTPException(status_code=400, detail="사용자 추가에 실패했습니다.")



# 로그인 기능(API) :  이메일로 로그인 후 user_id 리턴------------------------------------------------------------------------------------------------------------------------------
@app.get("/login")
async def login_user(email: str, session: Session = Depends(get_session)):
    statement = select(Users).where(Users.email == email)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()   # 해당하는 한명의 사용자를 찾기 위함
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return {"user_id": user.id}


# FastAPI 라우터에서 로그인 HTML을 서빙하는 코드 -----------------------------------------------------------------------------------------------------------------------------
@app.get("/login.html", response_class=HTMLResponse)
async def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# 로그인 성공 후 보여줄 프로필 HTML 페이지 렌더링용--------------------------------------------------------------------------------------------------------------
@app.get("/profiles/view/{user_id}", response_class = HTMLResponse)
async def read_profiles(
    request:Request,
    user_id:int,
    session : Session=Depends(get_session)
):
    profiles = await session.get(Profiles, user_id) # id로 조회
    if not profiles: 
        raise HTTPException(status_code=404, detail="Profile not found")
    return templates.TemplateResponse(  # ← 템플릿 렌더링해서 HTML 응답
        "profile.html",
        {
            "request": request,
            "profiles":profiles
        }
    )

# JSON API 응답용(JSON 형태로 사용자 프로필 데이터 반환)
# 해당 user_id에 맞는 사람을 찾음 ------------------------------------------------------------------------------------------------------------------------------
@app.get("/profiles/{user_id}", response_model=ProfileRead)
async def read_profiles(user_id: int, session: Session=Depends(get_session)):
    profiles = await session.get(Profiles, user_id)  # ID로 조회
    if not profiles:  # 없으면 404 에러
        raise HTTPException(status_code=404, detail="Profile not found")
    return profiles  # 사용자 정보 반환 ← Pydantic 모델에 맞춰 JSON 응답





# ------------------------------------------------------------------------------------------------------------------------------
# @app.get("/posts/user/{user_id}", response_model=UserPosts)
# async def read_user_posts(user_id: int, page: int = Query(1, ge=1), session: Session = Depends(get_session)):
#     size = 10
#     offset = (page - 1) * size

#     user_stmt = select(Users).where(Users.id == user_id)
#     user_result = await session.execute(user_stmt)
#     user = user_result.scalar_one_or_none()
#     if not user:
#         raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

#     posts_stmt = (
#         select(Posts)
#         .where(Posts.user_id == user_id)
#         .limit(size)
#         .offset(offset)
        
#     )
#     posts_result = await session.execute(posts_stmt)
#     posts_list_from_db = posts_result.scalars().all()

#     return UserPosts(
#         id=user.id,
#         username=user.username,
#         email=user.email,
#         posts=[PostOutput.model_validate(post, from_attributes=True) for post in posts_list_from_db]  
#     )






# 이 부분의 목적이 뭔가???????????------------------------------------------------------------------------------------------------------------------------------
@app.get("/users/profile/{id}", response_model=UserProfile)
async def read_user_profile(id:int,session: Session=Depends(get_session)):
    statement = (
        select(Users, Profiles)
        .join(Profiles, Users.id==Profiles.user_id)
        .where(Users.id==id)
    )
    result = (await session.execute(statement)).first()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    user, profile = result
    
    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        profile=profile
    )



# ------------------------------------------------------------------------------------------------------------------------------
@app.get("/users/profile/", response_model=List[UsersProfile])
def read_paging_user_profile(page:int=Query(1,ge=1)):
    with Session(engine) as session:  # 세션 열기
        size = 10
        offset = (page-1)*size
        statement = (
            select(Users, Profiles)
            .join(Profiles, Users.id==Profiles.user_id)
            .offset(offset).limit(size)
        )
        results = session.exec(statement).all()
        user_profiles_list = []
        for user, profile in results:
            if user: # user 객체가 유효한 경우에만 처리
                # phone과 bio를 담을 변수를 None으로 초기화
                phone_data = None
                bio_data = None

                if profile: # profile 객체가 실제로 존재하는 경우
                    phone_data = profile.phone
                    bio_data = profile.bio

                # UsersProfile 모델에 맞게 데이터 구성
                user_profiles_list.append(
                    UsersProfile(
                        id=user.id,
                        username=user.username,
                        email=user.email,
                        phone=phone_data, # phone 데이터를 직접 매핑
                        bio=bio_data      # bio 데이터를 직접 매핑
                    )
                )
        return user_profiles_list # 최종 리스트 반환
        
        #select(Posts).offset(offset).limit(size)






# 프로필 수정 HTML 서빙 라우터 ------------------------------------------------------------------------------------------------------------------------------
@app.get("/edit/profile/{user_id}", response_class=HTMLResponse)
async def get_profile_page(user_id: int, request: Request, session: Session = Depends(get_session)):

     # 조인: Users + Profiles (Profiles.user_id == Users.id)
    statement = (
        select(Users, Profiles)
        .join(Profiles, Users.id == Profiles.user_id)
        .where(Users.id == user_id)
    )
    result = await session.execute(statement)
    row = result.first()


    if not row:
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")
    user, profile = row  # 튜플 언패킹
    return templates.TemplateResponse("edit_profile.html", {
        "request": request,
        "profiles": profile,
        "user":user
    })

# 로그인 이후 프로필 수정 페이지도 자동으로 이메일 기반으로 불러와서 수정 --------------------------------------------
@app.patch("/edit/profile/{user_id}")
async def update_profile(user_id: int, update_data: ProfileUpdate, session: Session = Depends(get_session)):
    db_profile = await session.get(Profiles, user_id)
    if not db_profile:
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")

    db_profile.bio = update_data.bio
    db_profile.phone = update_data.phone
    await session.commit()
    await session.refresh(db_profile)
    return {"message": "프로필이 성공적으로 수정되었습니다."}



# ---- 쌤꺼 update-------------
# @app.patch('/profiles/{user_id}',response_model = Users)
# async def update_user(user_id: int , user_update : ProfileUpdate,session: Session=Depends(get_session)):
    
#     user = await session.get(Users,user_id)
#     user_data= user_update.model_dump(exclude_unset=True)
#     if not user_data:
#         raise HTTPException(status_code=400,detail='업데이트할 컬럼이 없습니다.')

#     for key, value in user_data.items():
#         setattr(user,key,value)
    
#     session.add(user)
#     await session.commit()
#     session.refresh(user)
#     return user



# 모든 회원 불러오기 api ------------------------------------------------------------------------------------------------------------------
@app.get("api/users/all/", response_model=List[UserRead])
async def read_all_users(session: AsyncSession=Depends(get_session)):
    statement = select(Users).order_by(Users.id.desc())
    result = await session.execute(statement)
    users = result.scalars().all()  # 결과에서 스칼라 객체 추출
    return users


# 모든 회원 불러오기 html -----------------------------------------------------------------------------------------------------------------------------
@app.get("/users/all/", response_class=HTMLResponse)
async def read_all_users_page(request: Request, session: AsyncSession=Depends(get_session)):
    statement = select(Users).order_by(Users.id.desc())
    result = await session.execute(statement)
    users = result.scalars().all()  # 결과에서 스칼라 객체 추출
    if not users:
        raise HTTPException(status_code = 404, detail = '등록된 user 없습니다.')
    return templates.TemplateResponse('user_list.html',{
        "request" : request,
        "users":users
    })

# 회원 삭제용 fastapi 라우터------------------------------------------------------------------------------------------
@app.delete('/users/{userId}',status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(userId:int, session:Session=Depends(get_session)):
    user = await session.get(Users,userId)
    profile = await session.get(Profiles, userId)
    if not user:
        raise HTTPException(status_code = 404, detail = '사용자 찾을 수 없음')
    if profile:
        await session.delete(profile)

    await session.delete(user)
    await session.commit()
    return 


# # 글 등록용 fastapi 라우터------------------------------------------------------------------------------------------
@app.post('/write/post/{userId}',response_model = Posts, status_code = status.HTTP_201_CREATED)
async def write_post(userId : int , post:PostWrite, session:Session=Depends(get_session)):
    result = await session.execute(select(Users).where(Users.id == userId))
    user = result.scalars().first()
    if not user:
         raise HTTPException(status_code = 404, detail = '사용자 찾을 수 없음')
    
   
    db_post = Posts(title=post.title, content=post.content, user_id=userId)

    try:
        session.add(db_post)
        await session.commit()
        await session.refresh(db_post)
        return db_post
    except Exception as e:
        await session.rollback()
        logger.error(f"글 생성 오류: {e}")
        raise HTTPException(status_code=400, detail="글 추가에 실패했습니다.")


# -----------------------글 등록 페이지HTML 불러오기 ----------------------------------------
@app.get('/write/post/{userId}',response_class='HTMLResponse')
async def write_post(request:Request,userId:int):
    return templates.TemplateResponse('write_post.html',{'request':request, 'user_id':userId})



# -----------------------작성 글 목록 페이지HTML 불러오기 ----------------------------------------
@app.get('/show/post/{userId}',response_class='HTMLResponse')
async def show_post(request:Request,userId:int):
    return templates.TemplateResponse('show_post.html',{'request':request, 'user_id':userId})

# 내가 쓴 글 불러오게 함 ------------------------------------------------------------------------------------------------------------------------------
@app.get("/posts/user/{user_id}", response_model=PostListResponse )
async def read_paging_posts(user_id: int,page:int=Query(1,ge=1), size: int = Query(10, ge=1),session: Session=Depends(get_session)):
    offset = (page - 1) * size  # 꼭 정수


     # 전체 게시글 수 계산 (이게 꼭 넘어가야 페이징 할 수 있음!!!!!!!)
    total_stmt = select(func.count()).select_from(Posts).where(Posts.user_id == user_id)
    total_result = await session.execute(total_stmt)
    total_count = total_result.scalar_one()

    # SQLAlchemy는 limit().offset() 순서로 작성해야 함 
        # 해당 페이지 게시글 가져오기
    stmt = select(Posts).where(Posts.user_id == user_id).limit(size).offset(offset)
    result = await session.execute(stmt)
    posts = result.scalars().all()

# PostRead.from_orm(post) 또는 model_validate(post) 를 써서 Pydantic 모델로 변환
    # ✅ Pydantic(PostRead) 모델로 변환
    post_list = [PostRead.model_validate(post) for post in posts]
    return PostListResponse(total=total_count, posts= post_list )


#----------------- profile보기에서 작성글 보기 누르면 show_post 로딩되는 라우터 추가----------------------------
@app.get("/posts/view/{user_id}", response_class=HTMLResponse)
async def show_user_posts(user_id: int, request: Request):
    return templates.TemplateResponse("show_post.html", {"request": request, "user_id": user_id})