"""Export an app copy with NO external reference-photo files and the mode disabled."""
from pathlib import Path
import argparse,shutil,json,hashlib
R=Path(__file__).resolve().parents[1]
def main(out):
 target=Path(out).resolve()
 if target.exists():raise FileExistsError(f'Choose a new output directory: {target}')
 shutil.copytree(R/'drink-lens/dist',target,ignore=lambda path,names:['references'] if Path(path).name=='assets' else [])
 p=target/'index.html';s=p.read_text().replace('<head>','<head><meta name="drink-lens-references" content="off">',1);p.write_text(s)
 assert not (target/'assets/references').exists()
 archive=shutil.make_archive(str(target),'zip',root_dir=target)
 print(f'Wrote photo-free app: {target}\nArchive: {archive}')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',default=str(R/'artifacts/drink-lens-descriptions-only'));main(p.parse_args().out)
