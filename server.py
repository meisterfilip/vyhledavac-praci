# import knihovny databazoveho systemu Supabase a knihovny OS

from tridy import *
from supabase import create_client#, Client
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException#, Path, UploadFile
#from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
#import hashlib
import datetime
from math import ceil


load_dotenv()

# vytvoreni klienta databaze
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

app = FastAPI()

# konfigurace FastAPI, aby mohla bezet na vsech adresach
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    

@app.get("/get-vedouci")
async def getVedouci():
    vedouci = []

    data = supabase.table("tasks").select("*").execute()
    data = data.dict()["data"]

    for prace in data:
        if prace["vedouci"] not in vedouci:
            vedouci.append(prace["vedouci"])

    return sorted(vedouci)


@app.get("/get-predmety")
async def getPredmety():
    predmety = []
    
    
    data = supabase.table("tasks").select("*").execute()
    data = data.dict()["data"]

    for prace in data:
        if prace["predmet"] not in predmety:
            predmety.append(prace["predmet"])

    return predmety

@app.get("/get-autori")
async def getAutori():
    autori = []
    
    data = supabase.table("tasks").select("*").execute()
    data = data.dict()["data"]

    for prace in data:
        if prace["jmeno_prijmeni"] not in autori:
            autori.append(prace["jmeno_prijmeni"])

    

    return sorted(autori)


@app.get("/get-oldest-year")
async def getOldestYear():

    data = supabase.table("tasks").select("*").execute()
    data = data.dict()["data"]

    oldestYear = int(data[0]["skolni_rok"][0:4])

    for prace in data:
        if int(prace["skolni_rok"][0:4]) < oldestYear:
            oldestYear = int(prace["skolni_rok"][0:4])


    return oldestYear

@app.post("/filter-page/{strana}")
async def filtrStrana(strana: int, filtr: Filtr, sortBy: str, directionDown: bool):

    if filtr.obor == [] or filtr.obor[0] == "string":
        filtr.obor = None

    if filtr.pocatecni_rok == 0:
        filtr.pocatecni_rok = 2000

    if filtr.koncovy_rok == 0:
        today = datetime.date.today()
        aktualni_rok = today.year
        filtr.koncovy_rok = aktualni_rok

    if filtr.predmet == "" or filtr.predmet == "string":
        filtr.predmet = None

    if filtr.vedouci == "" or filtr.vedouci == "string":
        filtr.vedouci = None

    if filtr.jmeno_prijmeni == "" or filtr.jmeno_prijmeni == "string":
        filtr.jmeno_prijmeni = None

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
            if prace["predmet"].lower() == filtr.predmet.lower():
                platne_prace.append(prace)

        data = platne_prace
        platne_prace = []
        if data == []:
            return {"Message": "Žádná práce se zadanými parametry nebyla nalezena!"}
    
    
    # filtrovani vedouciho

    if filtr.vedouci != None:
        for prace in data:
            if prace["vedouci"].lower() == filtr.vedouci.lower():
                platne_prace.append(prace)

        data = platne_prace
        platne_prace = []
        if data == []:
            return {"Message": "Žádná práce se zadanými parametry nebyla nalezena!"}
        
    # filtrovani autora
        
    if filtr.jmeno_prijmeni != None:
        for prace in data:  
            if prace["jmeno_prijmeni"].lower() == filtr.jmeno_prijmeni.lower():
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
    
    pocet_stran = getPageCount(data)

    sorted_data = sorted(data, key=lambda x: x[f"{sortBy}"])

    startIndex = strana * 15 - 15
    endIndex = strana * 15

    if directionDown == False:
        sorted_data.reverse()

    sorted_data = sorted_data[startIndex:endIndex]

    return {"pocet_stran": pocet_stran, "prace" : sorted_data}


def getPageCount(tasks: list):
    pocetPraci = len(tasks)
    pocetStran = ceil(pocetPraci / 15)

    return pocetStran

@app.post("/search-page/{strana}")
async def searchPage(strana: int, sortBy: str, directionDown: bool, searchString: str = None):

    

    if searchString != None:
        sloupce = ["jmeno_prijmeni", "tema", "obsah", "prakticka_cast", "vedouci"]
        platne_prace = []

        for sloupec in sloupce:
            data = supabase.table("tasks").select("*").ilike(f"{sloupec}", f"%{searchString}%").execute()
            data = data.dict()
            data = data["data"]

            if data != []:
                for prace in data:
                    if prace not in platne_prace:
                        platne_prace.append(prace)

    else:
        platne_prace = supabase.table("tasks").select("*").execute()
        platne_prace = platne_prace.dict()["data"]

                    
    if platne_prace == []:
        return {"Message": "Žádná práce nebyla nalezena!"}
    
    pocetStran = getPageCount(platne_prace)

    sorted_data = sorted(platne_prace, key=lambda x: x[f"{sortBy}"])   

    startIndex = strana * 15 - 15
    endIndex = strana * 15

    if directionDown == False:
        sorted_data.reverse()

    sorted_data = sorted_data[startIndex:endIndex]

    return {"pocet_stran": pocetStran, "prace": sorted_data}

@app.get("/get-images-from-id/{user_id}")
async def get_image(user_id: str):

    public_urls = []
    user_images = supabase.storage.from_("user-images").list(user_id)
    for file_name in user_images:
        if len(user_images) > 0:
            public_urls.append(supabase.storage.from_("user-images").get_public_url(f"{user_id}/{file_name['name']}"))

    return public_urls

@app.get("/insert-image-by-id/{user_id}") # U této funkce dodělat možnost nahrání obrázku přímo od uživatele
async def insert_image(user_id: str):

    bucketName = "user-images"
    allIds = []
    
    response = supabase.storage.from_(bucketName).list()
    for folder in response:
        folderName = folder["name"]
        allIds.append(folderName)

    # Lze optimalizovat - nemusí zde být if else - později upravit
    if user_id in allIds:
        print("ano, složka již existuje")
        with open("test.txt", 'rb') as f:
            supabase.storage.from_(bucketName).upload(file=f ,path=f"{user_id}/{f.name}")
        # Zde bude funkce, která vezme obrázek a vloží ji do složky s příslušným ID

    else:
        print("ne, složka zatím neexistuje, bude vytvořena")

        with open("test.txt", 'rb') as f:
            supabase.storage.from_(bucketName).upload(file=f ,path=f"{user_id}/{f.name}") # !!!Tuto část kódu smazat poté co zde bude vložena funkce!!!

        # Zde bude funkce, která vezme obrázek a vloží ji do složky s příslušným ID

    return {"Message": f"Soubor {f.name} úspěšně nahrán do bucketu {bucketName} do adresáře {user_id}/{f.name}"}