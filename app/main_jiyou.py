#./app/main.py
from fastapi import FastAPI,Query,Depends, HTTPException, status
from typing import Optional, List, Union
from sqlalchemy import Text
from sqlmodel import SQLModel, Field, create_engine, Session, select
from database import engine

class Users(SQLModel, table = True):  # table = True : 테이블과 직접적으로 연결하겟다
    id: Optional[int] = Field(default=None,primary_key = True)
    user_name : str
    email: str

class Profiles(SQLModel, table = True):  # table = True : 테이블과 직접적으로 연결하겟다
    user_id: Optional[int] = Field(default=None,primary_key = True)
    bio : Optional[str] = Field(default=None,sa_type = Text, nullable=True)
    phone: Optional[str] = Field(default=None, max_length = 20, nullable= True)

class Posts(SQLModel, table = True):
    id: Optional[int] = Field(default=None,primary_key = True)
    title: str = Field(default=None, max_length = 100)
    content : Optional[str] = Field(default=None,sa_type = Text, nullable=True)
    user_id : Optional[int] = Field(default=None, nullable=True)
    cnt : Optional[int] = Field(default=0,ge = 0)

class UserProfile(SQLModel):
    id: int
    username:str
    email:str
    profile:Optional[Profiles] = None


app = FastAPI()

@app.on_event('startup')
def on_startup(): # db에 붙어서 class에 선언한 것을 점검해라
        SQLModel.metadata.create_all(engine)


@app.get('/posts',response_model=List[Posts])
def read_paging_posts(page:int=Query(1,ge=1)):
    with Session(engine) as session:
        size = 10
        offset = (page-1)*size   # 페이징 하는 방법
        statement = select(Posts).offset(offset).limit(size)
        posts = session.exec(statement).all()  # 실행한다 
        return posts

@app.get('/users/all/', response_model=List[Users])
def read_all_users():
    with Session(engine) as session:
        statement = select(Users)
        users = session.exec(statement).all()  # 실행한다 
        return users
    
# 특정 사용자 조회 (id로 한명)
@app.get('/users/{id}',response_model = Users) # users 테이블 사용
def read_user(id:int):
    with Session(engine) as session: # 세션 열기
        user = session.get(Users, id) # id로 조회
        if not user: # 없으면 404에러
            raise HTTPException(status_code=404, detail = 'User not found')
        return user # 사용자 반환


@app.get('/users/', response_model =List[Users])
def read_paging_users(page:int=Query(1,ge=1)):
    with Session(engine) as session:
        size = 10
        offset = (page-1)*size   # 페이징 하는 방법
        statement = select(Users).offset(offset).limit(size)
        users = session.exec(statement).all()  # 실행한다 
        return users

@app.get('/profiles/all/', response_model=List[Profiles])
def read_all_users_profiles():
    with Session(engine) as session:
        statement = select(Profiles)
        users_profiles = session.exec(statement).all()  # 실행한다 
        return users_profiles


@app.get('/profiles/{user_id}',response_model = Profiles)
def read_profile(user_id:int):
    with Session(engine) as session:
        user_profile = session.get(Profiles,user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail = 'User not found')
        return user_profile # 사용자 반환
    


@app.get('/profiles/', response_model =List[Profiles])
def read_paging_user_profiles(page:int=Query(1,ge=1)):
    with Session(engine) as session:
        size = 10
        offset = (page-1)*size   # 페이징 하는 방법
        statement = select(Profiles).offset(offset).limit(size)
        users_profiles = session.exec(statement).all()  # 실행한다 
        return users_profiles


@app.get('/users/profile/{id}',response_model = UserProfile)
def read_user_profile(id:int):
    with Session(engine) as session:
        statement = (
            select(Users,Profiles)  # 둘이 조인
            .join(Profiles, Users.id ==Profiles.user_id)
            .where(Users.id =={id})
        )
        result = session.exec(statement).first()
        if not result:
            raise HTTPException(status_code=404,detail = 'User not found')
        
        user, profile = result
        return UserProfile(
            id = user.id,
            username = user.user_name,
            email = user.email,
            profile = profile
        )


@app.get('/users/profile/',response_model = List[UserProfile])
def read_paging_user_profiles(page:int=Query(1,ge=1)):
    with Session(engine) as session:
        size = 10
        offset = (page-1)*size   # 페이징 하는 방법
        statement = (
            select(Users,Profiles)  # 둘이 조인
            .join(Profiles, Users.id ==Profiles.user_id)
            .offset(offset).limit(size)
        )
        results = session.exec(statement).all()  # 실행한다 
        user_dic={}
        for user,profile in results:
            if user and user.id not in user_dic:
                user_dic[user.id] = {'id':user.id, 'username':user.user_name,'email':user.email, 'profile':profile}
        return [UserProfile(**data) for data in user_dic.values()]