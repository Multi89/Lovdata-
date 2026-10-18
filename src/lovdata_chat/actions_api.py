import os
import secrets
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from . import core

app=FastAPI(title='Norsk lovhjelp API',version='0.3.0',description='Uoffisielt juridisk søk. Verifiser alltid originalkilder.')
def auth(authorization: str | None = Header(None)):
    key=os.getenv('LOVDATA_ACTIONS_API_KEY','')
    if not key or not secrets.compare_digest(authorization or '',f'Bearer {key}'):
        raise HTTPException(401,'Mangler gyldig API-nøkkel')
class Query(BaseModel):
    query:str
    limit:int=10
class Research(BaseModel):
    query:str
    level:str='vanlig'
@app.get('/healthz')
def health():return {'status':'ok'}
@app.get('/status',dependencies=[Depends(auth)])
def status():return core.status()
@app.post('/search',dependencies=[Depends(auth)])
def search(q:Query):return {'results':core.search(q.query,q.limit)}
@app.get('/documents/{doc_id:path}',dependencies=[Depends(auth)])
def document(doc_id:str):
    item=core.fetch(doc_id)
    if item is None:raise HTTPException(404,'Fant ikke dokumentet')
    return item
@app.get('/find',dependencies=[Depends(auth)])
def find(doc_id:str,phrase:str):return {'results':core.find_in_document(doc_id,phrase)}
@app.post('/research',dependencies=[Depends(auth)])
def research(q:Research):
    if q.level not in ('lett','vanlig','professor'):raise HTTPException(422,'Ukjent nivå')
    guides={'lett':'Forklar med korte setninger og dagligspråk.', 'vanlig':'Forklar klart med relevante forbehold.', 'professor':'Skill mellom ordlyd, rettskildevekt, tolkning og usikkerhet.'}
    return {'results':core.search(q.query), 'level':q.level,'guidance':guides[q.level],'warning':'Ingen automatisk juridisk konklusjon. Verifiser mot gjeldende originalkilder.'}
@app.get('/privacy')
def privacy():return {'message':'Ikke send sensitive personopplysninger. Se prosjektets dokumentasjon.'}
@app.get('/terms')
def terms():return {'message':'Uoffisiell informasjonstjeneste. Ingen garanti for korrekthet eller oppdatert lovtekst.'}
@app.get('/support')
def support():return {'message':'Opprett sak i prosjektets GitHub-repositorium.'}
def main():
    import uvicorn
    uvicorn.run('lovdata_chat.actions_api:app',host=os.getenv('MCP_HOST','0.0.0.0'),port=int(os.getenv('MCP_PORT','8000')))
if __name__=='__main__':main()
