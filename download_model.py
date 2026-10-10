"""Explicitly download Google's pretrained model; never runs on import."""
from pathlib import Path
import hashlib,json,urllib.request

URL='https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task'

if __name__=='__main__':
    folder=Path('models');folder.mkdir(exist_ok=True);path=folder/'hand_landmarker.task'
    temp=path.with_suffix('.download')
    try:
        with urllib.request.urlopen(URL,timeout=60) as response,temp.open('wb') as target:
            while chunk:=response.read(1024*1024):target.write(chunk)
        if temp.stat().st_size<100_000:raise RuntimeError('Downloaded file is unexpectedly small')
        temp.replace(path)
        metadata={'source':URL,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'note':'Pretrained Google MediaPipe model; not trained by this project.'}
        (folder/'model-source.json').write_text(json.dumps(metadata,indent=2))
        print('Saved',path)
    finally:temp.unlink(missing_ok=True)
