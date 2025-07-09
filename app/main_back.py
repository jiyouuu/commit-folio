#./app/main.py
from fastapi import FastAPI,Query,Depends, HTTPException, status
from typing import Optional, List, Union
from sqlmodel import Session, select
from models import User

# from app.database import create_db_and_tables, get_session
app = FastAPI()

@app.get("/")
async def read_root():
    return {"message":"Hello everyone"}

@app.get('/items/{item_id}')
async def read_item(item_id:int):
    return {"item_id":item_id,'message': f"아이템 번호는 {item_id}입니다."}

@app.get('/user/{user_id}/items/{item_id}')
async def read_user(user_id:int, item_id : int):
    return {'item_id':item_id, 'user_id':user_id, "message":f'아이템 번호는 {item_id} 이고 사용자 이름은 {user_id} 입니다.'}

@app.get('/user')
async def read_user():
    return {"message":"user를 읽습니다."}

@app.get('/user/me')
async def read_user_me():
    return {'user_id':'current_user','message': '나야 나'}

@app.get('/user/{user_id}')
async def read_user_me(user_id:int):
    return {'user_id':'current_user','message': f'{user_id}는 나야 나'}


import uuid
@ app.get('/products/{product_uuid}')
async def get_product_by_uuid(prodcut_uuid:uuid.UUID):
    return {'product_uuid': str(product_uuid),'message':'product id by UUID'}

@app.get('/product/')
async def read_products(
    q:Optional[str] = None,     # q값이 null값일수도 있다는 의미임. (optional)
    short: bool = False,        # short는 bool값으로 false로 지정
    skip: int =0,               
    limit: int = 10             
):  
    results = {"skip":skip,"limit":limit} 
    if q:        # q가 있으면 
        results.update({"q":q})    # results에다가 q값을 더해라
    if not short:               # short가 false면 
        results.update({"description":"shut upppppp!!!!!!!!!!!!!"})         # results에 더하라
    return results              


# @app.get('/product/')
# async def read_products(q:str,skip:int):   # 얘는 q= 를 하면 "" 공백으로 처리 
#     return {"q":f"{q}","skip":f"{skip}"}

# @app.get('/product/')
# async def read_products(q:Optional[str] = None, skip:int = 0):  # product로 들어가면 {"q":"None","skip":"0"} 이게 기본값
#     return {"q":f"{q}","skip":f"{skip}"}

@app.get('/search_items')
async def search_items(
    # 	필수 파라미터임을 의미 (... = Required)   
    # 예시 URL: /search_items?keyword=맥북
    # ✅ 예시 URL: /search_items?keyword=맥북&max_price=30000004
    # ✅ 예시 URL: /search_items?keyword=맥북&min_price=500000
    keyword:str = Query(..., min_length = 3, max_length =50,        description="검색할 키워드 (3자 이상, 50자 이하)"),
    max_price:Optional[float] = Query(None, gt = 0,description="검색할 상품의 최대 가격 (0보다 큰 값)"),
    min_price:Optional[float] = Query(None, gt = 0,  description="검색할 상품의 최소 가격 (0보다 큰 값)")
):
    results = {'keyword':f"{keyword}"}
    if max_price is not None:
        results.update({'max_price':max_price})
    if min_price is not None:
        results.update({'min_price':min_price})
    return results






# ----------------------------특정 사용자 조회 (ID로 한 명)-------------------------------
# @app.get("/users/{id}", response_model=UserRead)
# async def read_user(id: int, request: Request, session: Session=Depends(get_session)):
#     user = await session.get(Users, id)  # ID로 조회
#     if not user:  # 없으면 404 에러
#         raise HTTPException(status_code=404, detail="User not found")
#     return templates.TemplateResponse(
#         "register1.html",
#         {
#             'request': Request,
#             'user':user
#         })  # 사용자 반환 




# --------------------------------------------------------------------------------
# @app.post("/users/init/")
# def init_users():
#     sample_users = [
#         Users(username=f"User{i}", email=f"user{i}@example.com") for i in range(1, 21)
#     ]
#     with Session(engine) as session:
#         for user in sample_users:
#             session.add(user)
#         session.commit()
#     return {"message": "20 users initialized"}


# ------------------------------------------------------------------------------------------------------------------------------
# @app.get("/profiles/all/", response_model=List[ProfileRead])
# async def read_all_profiles(session: Session=Depends(get_session)):
#     statement = select(Profiles)
#     result = await session.execute(statement)  # AsyncSession의 execute 사용
#     profiles = result.scalars().all()  # 결과에서 스칼라 객체 추출
#     return profiles


# ------------------------------------------------------------------------------------------------------------------------------

# '''
# @app.get("/posts/all/", response_model=List[PostRead])
# async def read_all_posts(session: Session=Depends(get_session)):
#     statement = select(Posts)
#     result = await session.execute(statement)
#     posts = result.scalars().all()  # 결과에서 스칼라 객체 추출
#     return posts
# '''    



#-------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------
# @app.get("/users/", response_model=List[UserRead])
# async def read_paging_users(page:int=Query(1,ge=1),session: Session=Depends(get_session)):
#     size = 10
#     offset = (page-1)*size
#     statement = select(Users).offset(offset).limit(size)
#     result = await session.execute(statement)
#     users = result.scalars().all()  # 결과에서 스칼라 객체 추출
#     return users


# 해당 id가 쓴 글 불러오기 ------------------------------------------------------------------------------------------------------------------------------
# @app.get("/post/{id}", response_model=PostRead)
# async def read_profiles(id: int, session: Session=Depends(get_session)):
#     post = await session.get(Posts, id)  # ID로 조회
#     if not post:  # 없으면 404 에러
#         raise HTTPException(status_code=404, detail="Post not found")
#     return post  # 글 반환 
