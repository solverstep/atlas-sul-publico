"""Read-only regression contract for the public territorial revision."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));os.environ['ATLAS_PUBLIC_READ_ONLY']='1'
from backend import server as api
class RevisionTest(unittest.TestCase):
 def test_snapshot_and_members(self):
  s=api.current();old=json.loads((ROOT/'versions/v1.0.0.json').read_text('utf-8'))
  self.assertEqual(s['version'],'v1.0.1');api.check(s['assignments'])
  self.assertEqual(sum(old['assignments'][c]!=d for c,d in s['assignments'].items()),9)
  self.assertEqual(s['assignments']['4320800'],'RS17')
  self.assertEqual(s['assignments']['4323200'],'RS18')
  self.assertEqual(s['assignments']['4310876'],'RS18')
 def test_names_and_totals(self):
  rows=api.api_municipalities();self.assertEqual(len(rows),1191)
  for m in rows:self.assertEqual(m['province_name'],api.P_META[m['province_id']]['name'])
  p={p['id']:p for p in api.api_provinces()}
  self.assertEqual((p['RS17']['count'],p['RS18']['count']),(55,35))
  self.assertEqual((p['RS17']['population'],p['RS18']['population']),(562412,339850))
 def test_versioned_geometry(self):
  current=api.provinces_geo(api.current());self.assertEqual(len(current['features']),63)
  self.assertEqual(sum(a!=b for a,b in zip(api.BASE_MAP['features'],current['features'])),2)
  self.assertEqual(api.provinces_geo({'sequence':0}),api.BASE_MAP)
  with self.assertRaises(api.HTTPException) as ctx:api.provinces_geo({'sequence':999,'version':'v1.0.999'})
  self.assertEqual(ctx.exception.status_code,503)
 def test_public_guard(self):
  with self.assertRaises(api.HTTPException) as ctx:api.require_write_access()
  self.assertEqual(ctx.exception.status_code,403)
if __name__=='__main__':unittest.main()
