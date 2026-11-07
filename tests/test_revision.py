"""Read-only regression contract for the public territorial revision."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));os.environ['ATLAS_PUBLIC_READ_ONLY']='1'
from backend import server as api
class RevisionTest(unittest.TestCase):
 def test_snapshot_and_members(self):
  s=json.loads((ROOT/'versions/v1.0.1.json').read_text('utf-8'));old=json.loads((ROOT/'versions/v1.0.0.json').read_text('utf-8'))
  self.assertEqual(s['version'],'v1.0.1');api.check(s['assignments'])
  self.assertEqual(sum(old['assignments'][c]!=d for c,d in s['assignments'].items()),9)
  self.assertEqual(s['assignments']['4320800'],'RS17')
  self.assertEqual(s['assignments']['4323200'],'RS18')
  self.assertEqual(s['assignments']['4310876'],'RS18')
 def test_names_and_totals(self):
  rows=api.api_municipalities();self.assertEqual(len(rows),1191)
  for m in rows:self.assertEqual(m['province_name'],api.metadata_for(api.current())[m['province_id']]['name'])
  p={p['id']:p for p in api.api_provinces()}
  legacy={p['id']:p for p in api.summary(json.loads((ROOT/'versions/v1.0.1.json').read_text('utf-8')))}
  self.assertEqual((legacy['RS17']['count'],legacy['RS18']['count']),(55,35))
  self.assertEqual((legacy['RS17']['population'],legacy['RS18']['population']),(562412,339850))
 def test_versioned_geometry(self):
  current=api.provinces_geo(json.loads((ROOT/'versions/v1.0.1.json').read_text('utf-8')));self.assertEqual(len(current['features']),63)
  self.assertEqual(sum(a!=b for a,b in zip(api.BASE_MAP['features'],current['features'])),2)
  self.assertEqual(api.provinces_geo({'sequence':0}),api.BASE_MAP)
  with self.assertRaises(api.HTTPException) as ctx:api.provinces_geo({'sequence':999,'version':'v1.0.999'})
  self.assertEqual(ctx.exception.status_code,503)
 def test_public_guard(self):
  with self.assertRaises(api.HTTPException) as ctx:api.require_write_access()
  self.assertEqual(ctx.exception.status_code,403)
 def test_general_revision_preserves_regions(self):
  s=json.loads((ROOT/'versions/v1.0.2.json').read_text('utf-8'));self.assertEqual(s['version'],'v1.0.2');api.check(s['assignments'])
  old=json.loads((ROOT/'versions/v1.0.1.json').read_text('utf-8'))
  self.assertEqual(sum(old['assignments'][c]!=p for c,p in s['assignments'].items()),125)
  for pid in ['RS01','SC01','PR01']:
   self.assertEqual({c for c,p in s['assignments'].items() if p==pid},{c for c,p in old['assignments'].items() if p==pid})
  rows=api.api_provinces();self.assertEqual(len(rows),63)
  self.assertTrue(all(p['count']>=4 for p in rows))
  self.assertEqual({u:sum(p['uf']==u for p in rows) for u in ['RS','SC','PR']},{'RS':22,'SC':18,'PR':23})
 def test_versioned_names_and_maps(self):
  s=json.loads((ROOT/'versions/v1.0.2.json').read_text('utf-8'));meta=api.metadata_for(s)
  self.assertEqual(meta['PR15']['name'],'Campo Mourão e entorno')
  old=json.loads((ROOT/'versions/v1.0.1.json').read_text('utf-8'))
  self.assertEqual(api.metadata_for(old)['PR15']['name'],'Campo Mourão–Cianorte')
  before=api.provinces_geo(old);after=api.provinces_geo(s)
  for pid in ['RS01','SC01','PR01']:
   self.assertEqual(next(f for f in before['features'] if f['properties']['id']==pid),next(f for f in after['features'] if f['properties']['id']==pid))
  self.assertEqual({f['properties']['id']:f['properties']['name'] for f in after['features']},{pid:p['name'] for pid,p in meta.items()})
 def test_maquine_corrected_proposal(self):
  s=api.current();self.assertEqual(s['version'],'v1.0.3');api.check(s['assignments'])
  old=json.loads((ROOT/'versions/v1.0.2.json').read_text('utf-8'))
  self.assertEqual([c for c in s['assignments'] if old['assignments'][c]!=s['assignments'][c]],['4311775'])
  self.assertEqual(s['assignments']['4311775'],'RS04')
  self.assertEqual(s['district_names'],old['district_names'])
  self.assertFalse(s['event']['institutionallyApproved'])
  rows=api.api_municipalities();m=next(m for m in rows if m['code']=='4311775')
  self.assertEqual((m['name'],m['uf'],m['province_id'],m['province_name']),('Maquiné','RS','RS04','Litoral Norte'))
  p={p['id']:p for p in api.api_provinces()}
  self.assertEqual((p['RS02']['count'],p['RS04']['count']),(32,19))
  self.assertEqual((p['RS02']['review'],p['RS04']['review']),('em_revisao','em_revisao'))
  before=api.provinces_geo(old);after=api.provinces_geo(s)
  changed=[a['properties']['id'] for a,b in zip(before['features'],after['features']) if a!=b]
  self.assertEqual(set(changed),{'RS02','RS04'})
  self.assertEqual(sum(p['population'] for p in api.summary(old)),sum(p['population'] for p in p.values()))
if __name__=='__main__':unittest.main()
