"""Atlas Territorial do Sul — API local, histórico imutável e validação geográfica."""
from __future__ import annotations
from pathlib import Path
from collections import Counter,defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import csv,hashlib,io,json,os,threading,uuid
from typing import Optional

from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse,JSONResponse,Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field

ROOT=Path(__file__).resolve().parent.parent
PROCESSED=ROOT/'data'/'processed'; VERSIONS=ROOT/'versions'; POINTER=VERSIONS/'CURRENT.json'
BASE_MUN=PROCESSED/'municipios_baseline.json'; BASE_GEO=PROCESSED/'provincias_map.geojson'; MUNIC_GEO=PROCESSED/'municipios_geometry_full.geojson'; MUNIC_MAP=PROCESSED/'municipios_map.geojson'
PUBLIC_READ_ONLY=os.getenv('ATLAS_PUBLIC_READ_ONLY','').strip().lower() in {'1','true','yes','on'}
VERSIONS.mkdir(parents=True,exist_ok=True)
MUNICIPALITIES=json.loads(BASE_MUN.read_text('utf-8'))
BY_CODE={m['code']:m for m in MUNICIPALITIES}
P_META={}
for m in MUNICIPALITIES:
 P_META[m['province_id']]={'id':m['province_id'],'name':m['province_name'],'uf':m['uf'],'category':'metropolitana' if m['province_id'].endswith('01') else 'ordinaria'}
BASE_MAP=json.loads(BASE_GEO.read_text('utf-8'))
COUNTS={'RS':497,'SC':295,'PR':399}
LOCK=threading.RLock()
_GEO=None


def now(): return datetime.now(timezone.utc).isoformat()
def sha(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
def require_write_access():
 if PUBLIC_READ_ONLY:raise HTTPException(403,'Edição desativada na versão pública do Atlas')
def atomic_json(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 temp=p.parent/(p.name+'.'+str(uuid.uuid4())+'.tmp')
 with temp.open('w',encoding='utf-8') as f:
  json.dump(data,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
 os.replace(temp,p)

def snapshot(seq, assignments, reviews, event):
 version=f'v1.0.{seq}'
 obj={'version':version,'sequence':seq,'timestamp':now(),'assignments':assignments,'reviews':reviews,'event':event}
 obj['sha256']=sha({'assignments':assignments,'reviews':reviews})
 filename=VERSIONS/(version+'.json')
 if filename.exists():raise ValueError('Versão já existente: '+version)
 atomic_json(filename,obj)
 atomic_json(POINTER,{'version':version,'sequence':seq,'sha256':obj['sha256']})
 return obj

def current():
 if not POINTER.exists():
  with LOCK:
   if not POINTER.exists(): snapshot(0,{m['code']:m['province_id'] for m in MUNICIPALITIES},{p:'nao_revisada' for p in P_META},{'action':'baseline','note':'Cadastro histórico importado, sem homologação por este aplicativo'})
 ptr=json.loads(POINTER.read_text('utf-8'))
 obj=json.loads((VERSIONS/(ptr['version']+'.json')).read_text('utf-8'))
 if obj['sha256']!=sha({'assignments':obj['assignments'],'reviews':obj['reviews']}):raise RuntimeError('Integridade do snapshot comprometida')
 return obj

def check(assign):
 if set(assign)!=set(BY_CODE):raise ValueError('Faltam ou sobram códigos IBGE')
 if len(assign)!=1191 or len(P_META)!=63:raise ValueError('Contagem territorial inválida')
 count=Counter()
 for code,p in assign.items():
  if p not in P_META or P_META[p]['uf']!=BY_CODE[code]['uf']:raise ValueError(f'Província de UF incorreta: {code} {p}')
  count[p]+=1
 if not all(count[p]>0 for p in P_META):raise ValueError('Uma Província ficaria sem municípios')
 return count

def summary(snap):
 group=defaultdict(list)
 for m in MUNICIPALITIES:group[snap['assignments'][m['code']]].append(m)
 return [{**meta,'count':len(group[pid]),'population':sum(x['pop'] for x in group[pid]),'area':round(sum(x['area'] for x in group[pid]),3),'density':round(sum(x['pop'] for x in group[pid])/sum(x['area'] for x in group[pid]),2),'review':snap['reviews'].get(pid,'nao_revisada')} for pid,meta in sorted(P_META.items())]

def geom_store():
 global _GEO
 if not MUNIC_GEO.exists():return None
 if _GEO is None:
  from shapely.geometry import shape
  obj=json.loads(MUNIC_GEO.read_text(encoding='utf-8'))
  _GEO={str(f['properties']['code']):shape(f['geometry']) for f in obj['features']}
  if set(_GEO)!=set(BY_CODE):raise RuntimeError('Arquivo de geometrias municipais não contém os 1.191 códigos do cadastro')
 return _GEO

def geometry_for(pid, assign):
 from shapely.ops import unary_union
 store=geom_store()
 if store is None:return None
 members=[store[code] for code,p in assign.items() if p==pid]
 if not members:return None
 return unary_union(members)

def geofeature(pid,geom):
 from shapely.geometry import mapping
 from shapely.ops import transform
 from shapely.validation import make_valid
 if not geom.is_valid:geom=make_valid(geom)
 # geometria simplificada apenas na visualização; cálculo de validação usa malha completa
 simplified=geom.simplify(.0018,preserve_topology=True)
 return {'type':'Feature','properties':P_META[pid],'geometry':mapping(simplified)}

def provinces_geo(snap):
 if PUBLIC_READ_ONLY:return BASE_MAP
 if geom_store() is None:
  if snap['sequence']==0 or snap['assignments']=={m['code']:m['province_id'] for m in MUNICIPALITIES}:
   return BASE_MAP
  # sem polígonos municipais, não deveriam existir edições confirmadas
  return BASE_MAP
 return {'type':'FeatureCollection','features':[geofeature(pid,geometry_for(pid,snap['assignments'])) for pid in sorted(P_META)]}

def components(pid,assign):
 from shapely.ops import unary_union
 g=geometry_for(pid,assign)
 if g is None:return None
 if g.geom_type=='Polygon':return 1
 return len(g.geoms) if g.geom_type=='MultiPolygon' else 1

def evaluate_transfer(code,dest,snap):
 if code not in BY_CODE:raise HTTPException(404,'Código IBGE municipal inexistente')
 if dest not in P_META:raise HTTPException(400,'Província de destino inexistente')
 src=snap['assignments'][code]
 if src==dest:raise HTTPException(400,'Município já pertence à Província de destino')
 if P_META[dest]['uf']!=BY_CODE[code]['uf']:raise HTTPException(400,'Transferência entre Estados Constituintes é proibida')
 if sum(p==src for p in snap['assignments'].values())<=1:raise HTTPException(400,'A origem ficaria sem municípios')
 if geom_store() is None:raise HTTPException(409,'Faltam malhas municipais oficiais. Importe os três ZIPs IBGE 2024 antes de transferir.')
 geom=geom_store()[code]
 old_origin=geometry_for(src,snap['assignments']); old_dest=geometry_for(dest,snap['assignments'])
 adj_border=geom.boundary.intersection(old_dest.boundary)
 contiguous=adj_border.length>0.000001
 before={src:components(src,snap['assignments']),dest:components(dest,snap['assignments'])}
 trial=dict(snap['assignments']);trial[code]=dest
 check(trial)
 after={src:components(src,trial),dest:components(dest,trial)}
 warnings=[]
 if not contiguous:warnings.append('Município não possui fronteira linear com a Província de destino')
 for p in (src,dest):
  if after[p]>before[p]:warnings.append(f'{p}: componentes geográficos aumentaram de {before[p]} para {after[p]} (revisar ilhas, lagoas, costa e contiguidade)')
  elif after[p]>1:warnings.append(f'{p}: área permanece com {after[p]} componentes (descontinuidade ou ilhas, conferir manualmente)')
 previews={'before':{'type':'FeatureCollection','features':[geofeature(src,old_origin),geofeature(dest,old_dest)]},'after':{'type':'FeatureCollection','features':[geofeature(src,geometry_for(src,trial)),geofeature(dest,geometry_for(dest,trial))]}}
 m=BY_CODE[code]
 return {'code':code,'name':m['name'],'source':src,'destination':dest,'uf':m['uf'],'population':m['pop'],'area':m['area'],'version':snap['version'],'adjacent':contiguous,'components_before':before,'components_after':after,'warnings':warnings,'preview':previews}

class PreviewReq(BaseModel):
 code:str; destination:str
class TransferReq(PreviewReq):
 expected_version:str; reason:str=''
class ReviewReq(BaseModel):
 status:str; expected_version:str
class RestoreReq(BaseModel):
 version:str; expected_version:str

app=FastAPI(title='Atlas Territorial do Sul — Público' if PUBLIC_READ_ONLY else 'Atlas Territorial do Sul — Local',version='1.1',docs_url=None if PUBLIC_READ_ONLY else '/docs',redoc_url=None if PUBLIC_READ_ONLY else '/redoc',openapi_url=None if PUBLIC_READ_ONLY else '/openapi.json')
@app.get('/api/status')
def api_status():
 s=current(); cnt=check(s['assignments'])
 has_geometry=MUNIC_MAP.exists() if PUBLIC_READ_ONLY else geom_store() is not None
 return {'version':s['version'],'hash':s['sha256'],'mode':'public_read_only' if PUBLIC_READ_ONLY else 'administrative','public_read_only':PUBLIC_READ_ONLY,'municipalities':len(BY_CODE),'provinces':len(P_META),'state_counts':COUNTS,'has_municipal_geometry':has_geometry,'geometry_provinces':63,'reviewed':sum(x=='validada' for x in s['reviews'].values()),'population':sum(m['pop'] for m in MUNICIPALITIES),'province_counts_valid':len(cnt)==63,'note':'Regionalização hipotética. Cadastro proveniente de consolidação anterior; confirmação visual ainda pendente.'}
@app.get('/api/provinces')
def api_provinces():return summary(current())
@app.get('/api/municipalities')
def api_municipalities():
 s=current()
 return [{**m,'province_id':s['assignments'][m['code']]} for m in MUNICIPALITIES]
@app.get('/api/map/provinces')
def api_map_provinces():return provinces_geo(current())
@app.get('/api/map/municipalities')
def api_map_municipalities():
 f=MUNIC_MAP
 if not f.exists():raise HTTPException(409,'Malha municipal não importada')
 return FileResponse(f,media_type='application/geo+json')
@app.get('/api/history')
def api_history():
 result=[]
 for p in sorted(VERSIONS.glob('v1.0.*.json'),key=lambda x:int(x.stem.split('.')[-1]),reverse=True):
  v=json.loads(p.read_text('utf-8'))
  event=v['event']
  if PUBLIC_READ_ONLY:event={k:event[k] for k in ('action','code','municipality','source','destination','province','status') if k in event}
  result.append({'version':v['version'],'timestamp':v['timestamp'],'sha256':v['sha256'],'event':event})
 return result
@app.get('/api/preview')
def api_preview(code:str,destination:str):
 require_write_access()
 return evaluate_transfer(code,destination,current())
@app.post('/api/transfers')
def api_transfer(req:TransferReq):
 require_write_access()
 with LOCK:
  s=current()
  if s['version']!=req.expected_version:raise HTTPException(409,'Versão desatualizada; atualize a página')
  ev=evaluate_transfer(req.code,req.destination,s)
  nxt=dict(s['assignments']);nxt[req.code]=req.destination
  reviews=dict(s['reviews']);reviews[ev['source']]='em_revisao';reviews[req.destination]='em_revisao'
  obj=snapshot(s['sequence']+1,nxt,reviews,{'action':'transfer','code':req.code,'municipality':ev['name'],'source':ev['source'],'destination':req.destination,'population':ev['population'],'area':ev['area'],'reason':req.reason,'warnings':ev['warnings'],'reversible_from':s['version']})
  return {'version':obj['version'],'hash':obj['sha256'],'event':obj['event']}
@app.post('/api/restore')
def api_restore(req:RestoreReq):
 require_write_access()
 with LOCK:
  current_snap=current()
  if current_snap['version']!=req.expected_version:raise HTTPException(409,'Versão desatualizada')
  old_file=VERSIONS/(req.version+'.json')
  if not old_file.exists():raise HTTPException(404,'Versão não encontrada')
  old=json.loads(old_file.read_text('utf-8'));check(old['assignments'])
  new=snapshot(current_snap['sequence']+1,old['assignments'],old['reviews'],{'action':'restore','from':current_snap['version'],'restored':old['version']})
  return {'version':new['version']}
@app.post('/api/undo')
def api_undo(expected_version:str):
 require_write_access()
 with LOCK:
  s=current()
  if s['version']!=expected_version:raise HTTPException(409,'Versão desatualizada')
  if s['sequence']==0:raise HTTPException(400,'Não há alterações para desfazer')
  prior=VERSIONS/(f"v1.0.{s['sequence']-1}.json")
  old=json.loads(prior.read_text('utf-8'));check(old['assignments'])
  new=snapshot(s['sequence']+1,old['assignments'],old['reviews'],{'action':'undo','from':s['version'],'reverted_to':old['version']})
  return {'version':new['version']}
@app.post('/api/review/{pid}')
def api_review(pid:str,req:ReviewReq):
 require_write_access()
 with LOCK:
  s=current()
  if pid not in P_META:raise HTTPException(404,'Província inexistente')
  if s['version']!=req.expected_version:raise HTTPException(409,'Versão desatualizada')
  if req.status not in ['nao_revisada','em_revisao','validada','divergencia']:raise HTTPException(400,'Status inválido')
  reviews=dict(s['reviews']);reviews[pid]=req.status
  new=snapshot(s['sequence']+1,s['assignments'],reviews,{'action':'review','province':pid,'status':req.status})
  return {'version':new['version']}
@app.get('/api/export/{kind}')
def api_export(kind:str):
 s=current()
 if kind=='json':
  content=[{**m,'province_id':s['assignments'][m['code']]} for m in MUNICIPALITIES]
  return JSONResponse(content,headers={'Content-Disposition':'attachment; filename="cadastro_provincial.json"'})
 if kind=='csv':
  f=io.StringIO();wr=csv.writer(f,delimiter=';');wr.writerow(['UF','Codigo_IBGE','Municipio','Provincia','Populacao_2022','Area_km2'])
  for m in MUNICIPALITIES:wr.writerow([m['uf'],m['code'],m['name'],s['assignments'][m['code']],m['pop'],str(m['area']).replace('.',',')])
  return Response('\ufeff'+f.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="cadastro_provincial.csv"'})
 if kind=='geojson':
  return JSONResponse(provinces_geo(s),headers={'Content-Disposition':'attachment; filename="provincias_sul.geojson"'})
 if kind=='audit':return JSONResponse(api_history(),headers={'Content-Disposition':'attachment; filename="historico_auditoria.json"'})
 if kind=='audit-csv':
  f=io.StringIO();wr=csv.writer(f,delimiter=';');wr.writerow(['Versao','DataHora','Acao','Municipio','Codigo_IBGE','Origem','Destino','Motivo','SHA256'])
  for x in api_history():
   e=x['event'];wr.writerow([x['version'],x['timestamp'],e.get('action',''),e.get('municipality',''),e.get('code',''),e.get('source',''),e.get('destination',''),e.get('reason',''),x['sha256']])
  return Response('\ufeff'+f.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="historico_auditoria.csv"'})
 raise HTTPException(404,'Formato não reconhecido')

app.mount('/',StaticFiles(directory=str(ROOT/'frontend'),html=True),name='frontend')
