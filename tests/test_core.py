import os
from lovdata_chat import core

def test_empty_database(tmp_path, monkeypatch):
    monkeypatch.setenv('LOVDATA_DB_PATH',str(tmp_path/'test.sqlite3'))
    assert core.status()['indexed_documents']==0
    assert core.search('barn')==[]

def test_search_and_find(tmp_path, monkeypatch):
    monkeypatch.setenv('LOVDATA_DB_PATH',str(tmp_path/'test.sqlite3'))
    with core.connect() as con:
        con.execute("INSERT INTO documents VALUES (?,?,?,?)",('NL/lov/test','Testlov','Rett til innsyn i journal.','test'))
    assert core.search('innsyn')[0]['title']=='Testlov'
    assert len(core.find_in_document('NL/lov/test','journal'))==1
    assert core.fetch('mangler') is None
