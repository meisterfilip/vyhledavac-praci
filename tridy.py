from pydantic import BaseModel
from typing import Optional

class Task(BaseModel):
    obor            : Optional[str] = None
    skolni_rok      : Optional[str] = None
    jmeno_prijmeni  : Optional[str] = None
    predmet         : Optional[str] = None
    tema            : Optional[str] = None
    obsah           : Optional[str] = None
    prakticka_cast  : Optional[str] = None
    vedouci         : Optional[str] = None
    
class newUser(BaseModel):
    login           : str
    password        : str
    password_again  : str

class User(BaseModel):
    login       : str
    password    : str

class Filtr(BaseModel):
    obor            : Optional[list] = None
    pocatecni_rok   : Optional[int] = None
    koncovy_rok     : Optional[int] = None
    predmet         : Optional[str] = None
    vedouci         : Optional[str] = None
    jmeno_prijmeni  : Optional[str] = None
    tagy            : Optional[list] = None