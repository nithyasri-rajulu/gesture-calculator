"""Camera calculator, mouse fallback and deterministic interaction replay."""
import argparse
import json
import time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from calculator import Calculator, PinchGate

ROWS = [['C','(',')','DEL'],['7','8','9','/'],['4','5','6','*'],['1','2','3','-'],['0','.','=','+']]
KEYS = [(k, (825+c*99, 204+r*88, 91, 79)) for r,row in enumerate(ROWS) for c,k in enumerate(row)]

def key_at(x,y):
    return next((k for k,(a,b,w,h) in KEYS if a<=x<a+w and b<=y<b+h),None)

def render(calc, background=None, pointer=None, label='GESTURE CALCULATOR', selected=None):
    frame = np.full((720,1280,3),(31,38,33),np.uint8) if background is None else background.copy()
    overlay=frame.copy();cv2.rectangle(overlay,(802,0),(1279,719),(31,38,33),-1)
    frame=cv2.addWeighted(overlay,.94,frame,.06,0)
    cv2.putText(frame,label,(38,52),cv2.FONT_HERSHEY_SIMPLEX,.76,(183,217,201),2)
    cv2.putText(frame,'Point with index finger. Release, then pinch to select.',(38,685),cv2.FONT_HERSHEY_SIMPLEX,.56,(223,230,218),1)
    cv2.rectangle(frame,(824,66),(1215,176),(233,239,224),-1)
    expression=calc.expression or '0'
    shown=expression if len(expression)<=24 else '...'+expression[-21:]
    scale=min(.88,350/max(1,cv2.getTextSize(shown,cv2.FONT_HERSHEY_SIMPLEX,1,2)[0][0]))
    cv2.putText(frame,shown,(840,125),cv2.FONT_HERSHEY_SIMPLEX,scale,(32,48,35),2)
    if calc.error:cv2.putText(frame,'Check expression',(843,156),cv2.FONT_HERSHEY_SIMPLEX,.45,(40,45,185),1)
    for key,(x,y,w,h) in KEYS:
        color=(85,139,206) if key==selected else ((82,102,77) if key in '+-*/=' else (55,66,56))
        cv2.rectangle(frame,(x,y),(x+w,y+h),color,-1)
        tw=cv2.getTextSize(key,cv2.FONT_HERSHEY_SIMPLEX,.72,2)[0][0]
        cv2.putText(frame,key,(x+(w-tw)//2,y+49),cv2.FONT_HERSHEY_SIMPLEX,.72,(239,243,234),2)
    if pointer:cv2.circle(frame,tuple(map(int,pointer)),13,(95,200,240),2)
    return frame

def demo(output):
    output.mkdir(parents=True,exist_ok=True)
    calc,gate=Calculator(),PinchGate();events=[];frames=[];t=0.
    # Scripted cursor replay tests the interaction layer, not hand detection.
    for key in ['1','2','+','8','=']:
        x,y,w,h=next(box for k,box in KEYS if k==key);pos=(x+w/2,y+h/2)
        for ratio in [.9]*5+[.2]*6+[.9]*3:
            event=gate.update(key,ratio,t)
            if event:calc.press(event);events.append({'time_s':round(t,2),'key':event,'expression':calc.expression})
            frame=render(calc,pointer=pos,selected=key,label='SCRIPTED REPLAY / NO CAMERA INFERENCE')
            cv2.putText(frame,'12 + 8 = 20',(90,275),cv2.FONT_HERSHEY_SIMPLEX,1.4,(204,223,205),2)
            cv2.putText(frame,'Pinch hysteresis / one activation per gesture',(90,324),cv2.FONT_HERSHEY_SIMPLEX,.65,(178,198,179),1)
            frames.append(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).resize((960,540)));t+=.06
    frames[0].save(output/'demo.gif',save_all=True,append_images=frames[1:],duration=60,loop=0)
    cv2.imwrite(str(output/'preview.png'),frame)
    result={'validation':'scripted interaction replay, not hand-detector validation','events':events,'final_result':calc.expression,'expected_result':'20','passed':calc.expression=='20' and len(events)==5}
    (output/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

def live(args):
    model=None
    if not args.mouse:
        if not args.model or not Path(args.model).is_file():
            raise SystemExit('Provide --model path/to/hand_landmarker.task (see README), or use --mouse.')
        try:import mediapipe as mp
        except ImportError:raise SystemExit('Install requirements-camera.txt for MediaPipe and camera display.')
        options=mp.tasks.vision.HandLandmarkerOptions(base_options=mp.tasks.BaseOptions(model_asset_path=args.model),running_mode=mp.tasks.vision.RunningMode.VIDEO,num_hands=1)
        try:
            model=mp.tasks.vision.HandLandmarker.create_from_options(options)
        except (OSError, RuntimeError) as exc:
            raise SystemExit(f'Cannot load the hand model: {exc}. Check the model and Linux graphics libraries; see README.') from exc
    camera=cv2.VideoCapture(args.camera) if not args.mouse else None
    if camera and not camera.isOpened():
        if model:model.close()
        camera.release();raise SystemExit('Camera cannot be opened. Try --camera 1 or --mouse; Windows Python is simplest for webcam access.')
    calc,gate=Calculator(),PinchGate();mouse=[None];last_ms=-1
    try:
        cv2.namedWindow('Gesture calculator')
        if args.mouse:
            def click(event,x,y,flags,param):
                mouse[0]=(x,y)
                if event==cv2.EVENT_LBUTTONDOWN and (key:=key_at(x,y)):calc.press(key)
            cv2.setMouseCallback('Gesture calculator',click)
        while True:
            pointer=mouse[0];selected=None;background=None
            if camera:
                ok,frame=camera.read()
                if not ok:break
                background=cv2.flip(cv2.resize(frame,(1280,720)),1)
                rgb=cv2.cvtColor(background,cv2.COLOR_BGR2RGB)
                timestamp=max(last_ms+1,int(time.monotonic()*1000));last_ms=timestamp
                result=model.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb),timestamp)
                if result.hand_landmarks:
                    hand=result.hand_landmarks[0]
                    points=np.array([(p.x*1280,p.y*720) for p in hand]);pointer=points[8]
                    palm=np.linalg.norm(points[5]-points[17]);ratio=np.linalg.norm(points[4]-points[8])/max(palm,1)
                    selected=key_at(*pointer)
                    event=gate.update(selected,ratio,time.monotonic())
                    if event:calc.press(event)
                    for x,y in points:cv2.circle(background,(int(x),int(y)),4,(100,220,190),-1)
                else:gate.update(None,None,time.monotonic())
            cv2.imshow('Gesture calculator',render(calc,background,tuple(pointer) if pointer is not None else None,'MOUSE MODE' if args.mouse else 'GESTURE CALCULATOR',selected))
            if cv2.waitKey(1)&255 in [27,ord('q')]:break
    finally:
        if camera:camera.release()
        if model:model.close()
        cv2.destroyAllWindows()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--demo',action='store_true');p.add_argument('--output',type=Path,default=Path('outputs'));p.add_argument('--mouse',action='store_true');p.add_argument('--model');p.add_argument('--camera',type=int,default=0);a=p.parse_args()
    demo(a.output) if a.demo else live(a)
