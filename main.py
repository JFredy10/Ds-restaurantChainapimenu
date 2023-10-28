from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import List
import os
from starlette.requests import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import declarative_base

# Configuración de la base de datos (PostgreSQL)
DATABASE_URL = "postgresql://databasemenu_user:ZnoY5wh7SjJ3aybp42olfAeaR6xmzWWm@dpg-ckr9rehrfc9c73djbtu0-a/databasemenu"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Definir el modelo de producto usando SQLAlchemy
Base = declarative_base()

class ProductDB(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    imagen = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    precio = Column(Float, nullable=False)

# Pydantic model para la validación de datos
class Product(BaseModel):
    nombre: str
    descripcion: str
    precio: float

# Rutas para operaciones CRUD

@app.post("/products/", response_model=Product)
async def create_product(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(...),
    precio: float = Form(...),
    imagen: UploadFile = File(...)
):
    # Guardar la imagen en el servidor
    imagen_nombre = imagen.filename
    with open(f"static/archivos/{imagen_nombre}", "wb") as f:
        f.write(imagen.file.read())

    db_product = ProductDB(nombre=nombre, descripcion=descripcion, precio=precio, imagen=imagen_nombre)

    # Guardar el producto en la base de datos
    db = SessionLocal()
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    db.close()

    return templates.TemplateResponse("create.html", {"request": request, "message": "Producto creado con éxito"})

@app.get("/products/", response_model=List[Product])
async def read_products(request: Request):
    db = SessionLocal()
    products = db.query(ProductDB).all()
    db.close()
    return templates.TemplateResponse("list_products.html", {"request": request, "products": products})

@app.get("/products/{product_id}", response_model=Product)
async def read_product(product_id: int, request: Request):
    db = SessionLocal()
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    db.close()
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return templates.TemplateResponse("read.html", {"request": request, "product": product})

@app.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(...),
    precio: float = Form(...),
    imagen: UploadFile = File(None)
):
    db = SessionLocal()
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()

    if not product:
        db.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Actualizar los datos del producto
    product.nombre = nombre
    product.descripcion = descripcion
    product.precio = precio

    if imagen:
        # Guardar la nueva imagen en el servidor
        imagen_nombre = imagen.filename
        with open(f"static/archivos/{imagen_nombre}", "wb") as f:
            f.write(imagen.file.read())
        product.imagen = imagen_nombre

    db.commit()
    db.close()

    return templates.TemplateResponse("update.html", {"request": request, "message": "Producto actualizado con éxito"})

@app.delete("/products/{product_id}", response_model=Product)
async def delete_product(product_id: int, request: Request):
    db = SessionLocal()
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()

    if not product:
        db.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Eliminar la imagen del servidor
    imagen_path = f"static/archivos/{product.imagen}"
    if os.path.exists(imagen_path):
        os.remove(imagen_path)

    db.delete(product)
    db.commit()
    db.close()

    return templates.TemplateResponse("delete.html", {"request": request, "message": "Producto eliminado con éxito"})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
