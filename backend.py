import sys
import os

# --- INICIO DE LA SOLUCIÓN DEFINITIVA ---
# Añade la carpeta 'src' al path de Python para que pueda encontrar el módulo 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
# --- FIN DE LA SOLUCIÓN DEFINITIVA ---

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controller.app_controller import AppController
from app.database.db_manager import initialize_database
from typing import List
from pydantic import BaseModel
import datetime

# --- Inicialización ---
initialize_database()
app = FastAPI()

# --- Configuración de CORS ---
origins = [
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

controller = AppController(view=None)

# --- Modelos Pydantic (Validación de Datos) ---
class TransactionModel(BaseModel):
    id: int
    date: datetime.date
    description: str
    amount: float
    type: str
    category: str
    account_id: int

    class Config:
        from_attributes = True

# --- Endpoints de la API ---
@app.get("/api/transactions", response_model=List[TransactionModel])
def get_transactions():
    transactions = controller.get_all_transactions_for_api()
    return transactions

@app.on_event("startup")
def startup_event():
    print("Procesando transacciones recurrentes al inicio...")
    controller.process_recurring_transactions()

# --- Cómo ejecutarlo (para pruebas) ---
if __name__ == "__main__":
    import uvicorn
    # Se usa string para el reload
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)