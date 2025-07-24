from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Field, SQLModel, Session, create_engine, select
from typing import Optional, List
from datetime import datetime

class AdvertisementBase(SQLModel):
    title: str
    description: Optional[str] = None
    price: float
    author: str

class Advertisement(AdvertisementBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AdvertisementCreate(AdvertisementBase):
    pass

class AdvertisementRead(AdvertisementBase):
    id: int
    created_at: datetime

class AdvertisementUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    author: Optional[str] = None

app = FastAPI()
engine = create_engine("sqlite:///ads.db")
SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

@app.post("/advertisement", response_model=AdvertisementRead, status_code=201)
def create_ad(ad: AdvertisementCreate, session: Session = Depends(get_session)):
    db_ad = Advertisement.from_orm(ad)
    session.add(db_ad)
    session.commit()
    session.refresh(db_ad)
    return db_ad

@app.patch("/advertisement/{ad_id}", response_model=AdvertisementRead)
def update_ad(ad_id: int, ad_update: AdvertisementUpdate, session: Session = Depends(get_session)):
    ad = session.get(Advertisement, ad_id)
    if not ad:
        raise HTTPException(status_code=404)
    for k, v in ad_update.dict(exclude_unset=True).items():
        setattr(ad, k, v)
    session.add(ad)
    session.commit()
    session.refresh(ad)
    return ad

@app.delete("/advertisement/{ad_id}", status_code=204)
def delete_ad(ad_id: int, session: Session = Depends(get_session)):
    ad = session.get(Advertisement, ad_id)
    if not ad:
        raise HTTPException(status_code=404)
    session.delete(ad)
    session.commit()

@app.get("/advertisement/{ad_id}", response_model=AdvertisementRead)
def get_ad(ad_id: int, session: Session = Depends(get_session)):
    ad = session.get(Advertisement, ad_id)
    if not ad:
        raise HTTPException(status_code=404)
    return ad

@app.get("/advertisement", response_model=List[AdvertisementRead])
def search_ads(
    title: Optional[str] = None,
    author: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    session: Session = Depends(get_session),
):
    stmt = select(Advertisement)
    if title:
        stmt = stmt.where(Advertisement.title.contains(title))
    if author:
        stmt = stmt.where(Advertisement.author == author)
    if price_min is not None:
        stmt = stmt.where(Advertisement.price >= price_min)
    if price_max is not None:
        stmt = stmt.where(Advertisement.price <= price_max)
    return session.exec(stmt).all()
