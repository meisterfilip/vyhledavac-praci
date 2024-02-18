# import knihovny databazoveho systemu Supabase a knihovny OS

from supabase import create_client, Client
import os
from dotenv import load_dotenv
load_dotenv()


# vytvoreni klienta databaze

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# import knihoven FastAPI

from fastapi import FastAPI, Path, UploadFile
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import datetime


app = FastAPI()


# konfigurace FastAPI, aby mohla bezet na vsech adresach

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# basemodel maturitni prace

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
    predmet         : Optional[list] = None
    vedouci         : Optional[str] = None
    tagy            : Optional[list] = None


# endpoint k overeni, zda API funguje

@app.get("/")
async def index():
    return {"Message": "API funguje!"}

# endpoint search_id - vyhleda radek v databazi se zadanym ID a vrati vsechny data tohoto radku

@app.get("/search_task_by_id/{id}")
async def search_task_by_id(id: int):

    try:
        data = supabase.table("tasks").select("*").eq("id", f"{id}").execute()
        print(data.dict()["data"][0])
        return data.dict()["data"][0]
    
    except:
        return {"Error": f"Task s id {id} neexistuje"}
    
@app.get("/print_ids")
async def print_ids():
    data = supabase.table("tasks").select("id").execute()
    return data

@app.post("/create_task")
async def create_task(task : Task):
    data = supabase.table("tasks").insert(task.dict()).execute()
    return task

# funkce load_ids() slouzi k nacteni ID vsech praci v db do pole (all_ids)

async def load_ids():
    all_ids = []
    db_response = supabase.table("tasks").select("id").execute().dict()["data"]

    for task in db_response:
        all_ids.append(task["id"])

    return all_ids

# endpoint delete_id - vyhleda radek v databazi se zadanym ID a vymaze cely radek s timto ID (DODELAT RETURN!!!)

@app.delete("/delete_task_by_id/{id}")
async def delete_task_by_id(id):

    ids = load_ids()

    if int(id) in ids:
        data = supabase.table("tasks").delete().eq("id", f"{id}").execute()
        return {"Message": f"Task s ID {id} byl úspěšně smazán!"}

    else:
        return {"Error": f"Task s ID {id} nebyl nalezen! Smazani neproběhlo!"}
    
@app.get("/test")
async def test():
    load_ids()
    return 0

# endpoint na registraci noveho uzivatele

@app.post("/register")
async def register(newuser : newUser):

    data = supabase.table("users").select("login").execute()

    data = data.dict()
    data = data["data"]
    logins = []

    for jmeno in data:
        logins.append(jmeno["login"])


    if newuser.login in logins:
        print("Jmeno uz existuje!")
        return {"Message": f"Uzivatel se jmenem '{newuser.login}' jiz existuje!"}
    
    if newuser.password != newuser.password_again:
        return {"Message": "Hesla se neshodují!"}
    
    if len(newuser.password) < 8:
        return {"Message": "Heslo musí mít minimálně 8 znaků!"}

    hasher = hashlib.sha256()

    hasher.update(newuser.password.encode('utf-8'))
    hashed_password = hasher.hexdigest()

    data = supabase.table("users").insert({'login': f"{newuser.login}", 'hashed_password': f"{hashed_password}"}).execute()

    return {"Message": f"Uzivatel {newuser.login} uspesne zaregistrovan!"}

# endpoint na login uzivatele

@app.post("/login")
async def login(user : User):

    hasher = hashlib.sha256()
    hashed_password_pokus = ""

    hasher.update(user.password.encode('utf-8'))
    hashed_password_pokus = hasher.hexdigest()

    data = supabase.table("users").select("*").execute()
    data = data.dict()
    data = data["data"]
    
    for i in data:
        
        if i["login"] == user.login:
            if i["hashed_password"] == hashed_password_pokus:
                
                return {"Message": "Úspěšně jste se přihlásili!"}

    return {"Message": "Špatné heslo!"}


@app.post("/upload_file")
async def upload_file(soubor: UploadFile):

    data = supabase.storage.from_("soubory").upload(soubor.filename, soubor.filename)

    return {"Message": "Soubor byl uspesne nahran!"}

@app.get("/download_file")
async def download_file():

    data = supabase.storage.from_("soubory").get_public_url("bitcoin.jpg")

    return {"Message": data}



# SYSTÉM VYHLEDÁVÁNÍ

@app.post("/search")
async def search(vyraz : str):

    sloupce = ["jmeno_prijmeni", "tema", "obsah", "prakticka_cast", "vedouci"]
    platne_prace = []

    for sloupec in sloupce:
        data = supabase.table("tasks").select("*").ilike(f"{sloupec}", f"%{vyraz}%").execute()
        data = data.dict()
        data = data["data"]

        if data != []:
            for prace in data:
                if prace not in platne_prace:
                    platne_prace.append(prace)
                    
    if platne_prace == []:
        return {"Message": "Žádná práce nebyla nalezena!"}
    
    return platne_prace

@app.post("/search-by-filter")
async def filtr(filtr : Filtr):

    if filtr.obor == [] or filtr.obor[0] == "string":
        filtr.obor = None

    if filtr.pocatecni_rok == 0:
        filtr.pocatecni_rok = 2000

    if filtr.koncovy_rok == 0:
        today = datetime.date.today()
        aktualni_rok = today.year
        filtr.koncovy_rok = aktualni_rok

    if filtr.predmet == [] or filtr.predmet[0] == "string":
        filtr.predmet = None

    if filtr.vedouci == "" or filtr.vedouci == "string":
        filtr.vedouci = None

    if filtr.tagy == [] or filtr.tagy[0] == "string":
        filtr.tagy = None

    
    # filtrovani oboru
    
    platne_prace = []
        
        
    if filtr.obor != None:
        data = supabase.table("tasks").select("*").execute()
        data = data.dict()
        data = data["data"]
        for prace in data:
            if prace["obor"] in filtr.obor:
                platne_prace.append(prace)


    else:
        data = supabase.table("tasks").select("*").execute()
        data = data.dict()
        data = data["data"]
        platne_prace = data
        

    
    if platne_prace == []:
        return {"Message": "Žádná práce se zadanými parametry nebyla nalezena!"}

    data = platne_prace
    platne_prace = []

    # filtrovani roku
    
    if filtr.pocatecni_rok != None or filtr.koncovy_rok != None:
        for prace in data:
            #print(prace["skolni_rok"][5:9])
            koncovy_rok = int(prace["skolni_rok"][5:9]) #vezme koncovy rok z promenne skolni_rok a prevede ho na int
            pocatecni_rok = koncovy_rok - 1
            if (koncovy_rok >= filtr.pocatecni_rok) and (pocatecni_rok <= filtr.koncovy_rok):
                platne_prace.append(prace)

        data = platne_prace
        platne_prace = []

        if data == []:
            return {"Message": "Žádná práce se zadanými parametry nebyla nalezena!"}


    # filtrovani predmetu

    if filtr.predmet != None:
        for prace in data:
            if prace["predmet"] in filtr.predmet:
                platne_prace.append(prace)

        data = platne_prace
        platne_prace = []
        if data == []:
            return {"Message": "Žádná práce se zadanými parametry nebyla nalezena!"}
    
    
    # filtrovani vedouciho

    if filtr.vedouci != None:
        for prace in data:
            if prace["vedouci"] == filtr.vedouci:
                platne_prace.append(prace)

        data = platne_prace
        platne_prace = []
        if data == []:
            return {"Message": "Žádná práce se zadanými parametry nebyla nalezena!"}
        
    # tagy

    if filtr.tagy != None:

        for tag in filtr.tagy:
            for prace in data:
                for sloupec in prace:
                    if str(tag).lower() in str(prace[sloupec]).lower() and sloupec != "id":
                        if prace not in platne_prace:
                            platne_prace.append(prace)

        data = platne_prace
        platne_prace = []

    return data

@app.get("/get-vedouci")
async def getVedouci():
    vedouci = []

    data = supabase.table("tasks").select("*").execute()
    data = data.dict()["data"]

    for prace in data:
        if prace["vedouci"] not in vedouci:
            vedouci.append(prace["vedouci"])

    return vedouci

@app.get("/get-predmety")
async def getPredmety():
    predmety = []

    data = supabase.table("tasks").select("*").execute()
    data = data.dict()["data"]

    for prace in data:
        if prace["predmet"] not in predmety:
            predmety.append(prace["predmet"])

    return predmety

# Obory
#26-41-M/01 Elektrotechnika
#18-20-M/01 Informační technologie
#23-41-M/01 Strojírenství

# Školní rok
#
#
#
