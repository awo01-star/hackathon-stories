"""Download separate, openly licensed example photos. Never changes transactions."""
from pathlib import Path
import urllib.parse,json,hashlib,re,time,subprocess
from html import unescape
R=Path(__file__).resolve().parents[1]
OUT=R/'drink-lens/dist/assets/references';OUT.mkdir(exist_ok=True)
HEADERS={'User-Agent':'StoriesDrinkLensEducationalPrototype/1.0 (drink reference image research)'}
def get(url):
 for attempt in range(3):
  try:
   return subprocess.check_output(['curl','--fail','--location','--silent','--show-error','--max-time','40','--user-agent',HEADERS['User-Agent'],url])
  except Exception:
   if attempt==2:raise
   time.sleep(2)
def plain(s):return unescape(re.sub('<[^>]+>','',s)).strip()
def main():
 candidates=[('iced_matcha','Creamy Matcha Latte.jpg'),('hot_matcha','Hot Matcha Latte.jpg'),('hot_milk_coffee','Cappuccino at Sightglass Coffee.jpg'),('iced_milk_coffee','Iced latte.jpg'),('iced_black_coffee','Iced Americano.jpg'),('black_coffee','Espresso.jpg')]
 records=[]
 for cls,title in candidates:
  params={'action':'query','format':'json','titles':'File:'+title,'prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':'640'}
  data=json.loads(get('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params)))
  page=next(iter(data['query']['pages'].values()))
  if 'imageinfo' not in page:print('Missing:',title,flush=True);continue
  info=page['imageinfo'][0];meta=info['extmetadata'];license=plain(meta.get('LicenseShortName',{}).get('value',''))
  if not any(k in license.lower() for k in ['cc0','cc by','public domain']):print('Skipped license:',title,license,flush=True);continue
  url=info.get('thumburl',info['url']);blob=get(url);name=cls+'.jpg';(OUT/name).write_bytes(blob)
  records.append({'id':cls+'-example','familyId':cls,'image':'./assets/references/'+name,'sourceTitle':title,'author':('Ericd; cropped version by Camembert' if title=='Espresso.jpg' else plain(meta.get('Artist',{}).get('value','Unknown'))),'license':license,'licenseUrl':meta.get('LicenseUrl',{}).get('value','https://commons.wikimedia.org/wiki/Commons:Licensing'),'sourcePage':info['descriptionurl'],'originalUrl':info['url'],'downloadUrl':url,'sha256':hashlib.sha256(blob).hexdigest(),'changes':'Downloaded Wikimedia thumbnail (or unscaled small original); displayed with a cropped preview. Source photograph retains its listed license.','verifiedStoriesPhoto':False})
  print('Downloaded:',title,license,len(blob),flush=True)
 (OUT/'manifest.json').write_text(json.dumps({'kind':'optional_external_reference_gallery','notTrainingData':True,'notStoriesProductPhotos':True,'references':records},indent=2))
 if len(records)<3:raise RuntimeError('Need at least three distinct reference families; inspect missing entries.')
if __name__=='__main__':main()
