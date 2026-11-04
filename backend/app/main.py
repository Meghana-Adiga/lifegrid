from datetime import datetime
from enum import Enum
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./lifegrid.db')
SECRET = os.getenv('JWT_SECRET', 'local-development-secret-change-me')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
security = HTTPBearer()
app = FastAPI(title='LIFEGRID Phase 1 API', version='0.1.0')
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__='users'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    name: Mapped[str]=mapped_column(String(120)); email: Mapped[str]=mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str]=mapped_column(String(255)); role: Mapped[str]=mapped_column(String(30), default='member')
class Category(Base):
    __tablename__='categories'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); name: Mapped[str]=mapped_column(String(100), unique=True)
class Resource(Base):
    __tablename__='resources'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); owner_id: Mapped[int]=mapped_column(ForeignKey('users.id'))
    category_id: Mapped[int]=mapped_column(ForeignKey('categories.id')); title: Mapped[str]=mapped_column(String(160))
    description: Mapped[str]=mapped_column(Text, default=''); quantity: Mapped[int]=mapped_column(Integer, default=1)
    location: Mapped[str]=mapped_column(String(200), default=''); available: Mapped[bool]=mapped_column(default=True)
class Request(Base):
    __tablename__='requests'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); requester_id: Mapped[int]=mapped_column(ForeignKey('users.id'))
    category_id: Mapped[int]=mapped_column(ForeignKey('categories.id')); title: Mapped[str]=mapped_column(String(160))
    description: Mapped[str]=mapped_column(Text, default=''); quantity: Mapped[int]=mapped_column(Integer, default=1); status: Mapped[str]=mapped_column(String(30), default='open')
class Assignment(Base):
    __tablename__='assignments'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); request_id: Mapped[int]=mapped_column(ForeignKey('requests.id'))
    resource_id: Mapped[int]=mapped_column(ForeignKey('resources.id')); assigned_by: Mapped[int]=mapped_column(ForeignKey('users.id'))
    status: Mapped[str]=mapped_column(String(30), default='proposed'); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
class Audit(Base):
    __tablename__='audit_events'
    id: Mapped[int]=mapped_column(Integer, primary_key=True); actor_id: Mapped[int]=mapped_column(Integer)
    action: Mapped[str]=mapped_column(String(80)); entity: Mapped[str]=mapped_column(String(40)); entity_id: Mapped[int]=mapped_column(Integer)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
Base.metadata.create_all(engine)
def db():
    s=SessionLocal()
    try: yield s
    finally: s.close()
def actor(c: HTTPAuthorizationCredentials=Depends(security), s: Session=Depends(db)):
    try: uid=jwt.decode(c.credentials, SECRET, algorithms=['HS256'])['sub']
    except (JWTError, KeyError): raise HTTPException(401, 'Invalid token')
    user=s.get(User, int(uid))
    if not user: raise HTTPException(401, 'Unknown user')
    return user
def log(s, u, action, entity, eid): s.add(Audit(actor_id=u.id, action=action, entity=entity, entity_id=eid))
class Signup(BaseModel): name:str; email:EmailStr; password:str
class Login(BaseModel): email:EmailStr; password:str
class CategoryIn(BaseModel): name:str
class ResourceIn(BaseModel): category_id:int; title:str; description:str=''; quantity:int=1; location:str=''; available:bool=True
class RequestIn(BaseModel): category_id:int; title:str; description:str=''; quantity:int=1
class RequestUpdate(BaseModel): title:Optional[str]=None; description:Optional[str]=None; quantity:Optional[int]=None; status:Optional[str]=None
@app.get('/health')
def health(): return {'status':'ok'}
@app.post('/auth/register')
def register(x:Signup,s:Session=Depends(db)):
    if s.query(User).filter_by(email=x.email).first(): raise HTTPException(409,'Email already registered')
    u=User(name=x.name,email=x.email,password_hash=pwd.hash(x.password)); s.add(u); s.commit(); s.refresh(u)
    return {'id':u.id,'name':u.name,'email':u.email,'role':u.role}
@app.post('/auth/login')
def login(x:Login,s:Session=Depends(db)):
    u=s.query(User).filter_by(email=x.email).first()
    if not u or not pwd.verify(x.password,u.password_hash): raise HTTPException(401,'Invalid credentials')
    return {'access_token':jwt.encode({'sub':str(u.id)},SECRET,algorithm='HS256'),'token_type':'bearer'}
@app.get('/me')
def me(u:User=Depends(actor)): return {'id':u.id,'name':u.name,'email':u.email,'role':u.role}
@app.get('/categories')
def categories(s:Session=Depends(db)): return [{'id':c.id,'name':c.name} for c in s.query(Category).all()]
@app.post('/categories')
def add_category(x:CategoryIn,s:Session=Depends(db),u:User=Depends(actor)):
    if u.role!='admin': raise HTTPException(403,'Admin role required')
    c=Category(name=x.name); s.add(c); s.commit(); s.refresh(c); log(s,u,'create','category',c.id); s.commit(); return {'id':c.id,'name':c.name}
@app.get('/resources')
def resources(q:Optional[str]=None,category_id:Optional[int]=None,available:Optional[bool]=None,s:Session=Depends(db)):
    rows=s.query(Resource)
    if q: rows=rows.filter(Resource.title.ilike(f'%{q}%'))
    if category_id: rows=rows.filter_by(category_id=category_id)
    if available is not None: rows=rows.filter_by(available=available)
    return [{'id':r.id,'owner_id':r.owner_id,'category_id':r.category_id,'title':r.title,'description':r.description,'quantity':r.quantity,'location':r.location,'available':r.available} for r in rows.all()]
@app.post('/resources')
def add_resource(x:ResourceIn,s:Session=Depends(db),u:User=Depends(actor)):
    if not s.get(Category,x.category_id): raise HTTPException(404,'Category not found')
    r=Resource(owner_id=u.id,**x.model_dump()); s.add(r); s.flush(); log(s,u,'create','resource',r.id); s.commit(); s.refresh(r); return {'id':r.id,'title':r.title}
@app.patch('/resources/{rid}')
def update_resource(rid:int,x:ResourceIn,s:Session=Depends(db),u:User=Depends(actor)):
    r=s.get(Resource,rid)
    if not r: raise HTTPException(404,'Resource not found')
    if r.owner_id!=u.id and u.role!='admin': raise HTTPException(403,'Not allowed')
    for k,v in x.model_dump().items(): setattr(r,k,v)
    log(s,u,'update','resource',rid); s.commit(); return {'id':r.id,'title':r.title}
@app.post('/requests')
def add_request(x:RequestIn,s:Session=Depends(db),u:User=Depends(actor)):
    if not s.get(Category,x.category_id): raise HTTPException(404,'Category not found')
    r=Request(requester_id=u.id,**x.model_dump()); s.add(r); s.flush(); log(s,u,'create','request',r.id); s.commit(); return {'id':r.id,'status':r.status}
@app.get('/requests')
def requests(q:Optional[str]=None,status:Optional[str]=None,s:Session=Depends(db),u:User=Depends(actor)):
    rows=s.query(Request)
    if q: rows=rows.filter(Request.title.ilike(f'%{q}%'))
    if status: rows=rows.filter_by(status=status)
    return [{'id':r.id,'requester_id':r.requester_id,'category_id':r.category_id,'title':r.title,'description':r.description,'quantity':r.quantity,'status':r.status} for r in rows.all()]
@app.post('/assignments')
def assign(request_id:int,resource_id:int,s:Session=Depends(db),u:User=Depends(actor)):
    if u.role not in ('coordinator','admin'): raise HTTPException(403,'Coordinator role required')
    req=s.get(Request,request_id); res=s.get(Resource,resource_id)
    if not req or not res: raise HTTPException(404,'Request or resource not found')
    if not res.available or req.category_id!=res.category_id: raise HTTPException(409,'Resource unavailable or category mismatch')
    a=Assignment(request_id=request_id,resource_id=resource_id,assigned_by=u.id); req.status='matched'; s.add(a); s.flush(); log(s,u,'create','assignment',a.id); s.commit(); return {'id':a.id,'status':a.status}
@app.patch('/assignments/{aid}')
def assignment_status(aid:int,status:str,s:Session=Depends(db),u:User=Depends(actor)):
    if status not in ('proposed','accepted','in_progress','completed','cancelled'): raise HTTPException(400,'Invalid status')
    a=s.get(Assignment,aid)
    if not a: raise HTTPException(404,'Assignment not found')
    a.status=status; log(s,u,'status_change','assignment',aid); s.commit(); return {'id':aid,'status':status}
@app.get('/dashboard')
def dashboard(s:Session=Depends(db),u:User=Depends(actor)):
    return {'resources':s.query(Resource).count(),'available_resources':s.query(Resource).filter_by(available=True).count(),'open_requests':s.query(Request).filter(Request.status.in_(['open','matched'])).count(),'assignments':s.query(Assignment).count()}
@app.get('/audit')
def audit(s:Session=Depends(db),u:User=Depends(actor)):
    if u.role!='admin': raise HTTPException(403,'Admin role required')
    return [{'actor_id':a.actor_id,'action':a.action,'entity':a.entity,'entity_id':a.entity_id,'created_at':a.created_at.isoformat()} for a in s.query(Audit).order_by(Audit.id.desc()).limit(100).all()]

@app.patch('/requests/{rid}')
def update_request(rid:int,x:RequestUpdate,s:Session=Depends(db),u:User=Depends(actor)):
    r=s.get(Request,rid)
    if not r: raise HTTPException(404,'Request not found')
    if r.requester_id!=u.id and u.role not in ('coordinator','admin'): raise HTTPException(403,'Not allowed')
    if x.status is not None and u.role not in ('coordinator','admin'): raise HTTPException(403,'Coordinator role required to change status')
    if x.status is not None and x.status not in ('open','matched','in_progress','completed','cancelled'): raise HTTPException(400,'Invalid status')
    for k,v in x.model_dump(exclude_unset=True).items(): setattr(r,k,v)
    log(s,u,'update','request',rid); s.commit(); return {'id':rid,'status':r.status}
@app.delete('/requests/{rid}')
def delete_request(rid:int,s:Session=Depends(db),u:User=Depends(actor)):
    r=s.get(Request,rid)
    if not r: raise HTTPException(404,'Request not found')
    if r.requester_id!=u.id and u.role!='admin': raise HTTPException(403,'Not allowed')
    log(s,u,'delete','request',rid); s.delete(r); s.commit(); return {'deleted':rid}
@app.delete('/resources/{rid}')
def delete_resource(rid:int,s:Session=Depends(db),u:User=Depends(actor)):
    r=s.get(Resource,rid)
    if not r: raise HTTPException(404,'Resource not found')
    if r.owner_id!=u.id and u.role!='admin': raise HTTPException(403,'Not allowed')
    log(s,u,'delete','resource',rid); s.delete(r); s.commit(); return {'deleted':rid}
