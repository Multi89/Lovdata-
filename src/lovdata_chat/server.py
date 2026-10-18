from mcp.server.fastmcp import FastMCP
from . import core
mcp=FastMCP('Norsk lovhjelp',host='0.0.0.0',port=8000)
@mcp.tool()
def lovdata_status()->dict:return core.status()
@mcp.tool()
def lovdata_search(query:str,limit:int=10)->list[dict]:return core.search(query,limit)
@mcp.tool()
def lovdata_fetch(doc_id:str)->dict:return core.fetch(doc_id) or {'error':'Ikke funnet'}
@mcp.tool()
def lovdata_find_in_document(doc_id:str,phrase:str)->list[dict]:return core.find_in_document(doc_id,phrase)
@mcp.tool()
def lovdata_research(query:str,level:str='vanlig')->dict:
    return {'results':core.search(query),'level':level,'warning':'Sjekk alltid gyldighet og kilde mot Lovdata.'}
def main():mcp.run(transport='streamable-http')
if __name__=='__main__':main()
