import numpy as np
import subprocess
from time import sleep 
from time import time
from PIL import Image, ImageDraw, ImageFont
import os
import math

# This class is for drawing something to streaming movie
class Frame:
    def __init__(me,create=True):
        me.sx = 0
        me.sy = 0
        me.dx = 640
        me.dy = 360
        if create:
            me.create_buffer()
    
    def create_buffer(me):
        px = np.arange(me.dx,dtype=np.float32)
        py = np.arange(me.dy,dtype=np.float32)
        me.px, me.py = np.meshgrid( px, py )
        me.x = np.zeros([me.dy,me.dx,3] , dtype=np.uint8)
        
    
    def request_center (me, cx, cy, cr):
        assert me.sx == 0 and me.sy == 0
        
        sx = int(math.floor( cx - cr ))
        sy = int(math.floor( cy - cr ))
        ex = int(math.ceil( cx + cr ))
        ey = int(math.ceil( cy + cr ))
        sx = max(0,sx)
        sy = max(0,sy)
        ex = min(me.dx,ex)
        ey = min(me.dy,ey)
        
        frame = Frame(False)
        frame.sx = sx
        frame.sy = sy
        frame.dx = ex-sx
        frame.dy = ey-sy
        frame.x = me.x[sy:ey,sx:ex,:]
        frame.px = me.px[sy:ey,sx:ex]
        frame.py = me.py[sy:ey,sx:ex]
        
        return frame,sx,sy,ex,ey
    
    def draw_circle(me, cx, cy, cr):
        frame,sx,sy,ex,ey = me.request_center( cx, cy, cr+5)
        r = np.sqrt( np.square(frame.px - cx) + np.square(frame.py - cy) )
        c = np.clip( -.5*(r - cr) + .5,0.,1.)
        frame.x[:,:,:] = np.maximum( frame.x[:,:,:], ( c *255).astype(np.uint8)[:,:,np.newaxis] )

# The most corner-cutting server
proc_serv = subprocess.Popen("python -m http.server 8000".split(" "),shell=False)

# Remove older trash files
for file in os.listdir():
    tag = file.split(".")[-1]
    if ( tag == "ts" or tag == "m3u8" ):
        os.remove( file )


head_tmp="""#EXTM3U
#EXT-X-VERSION:3mo
#EXT-X-MEDIA-SEQUENCE:{0}
#EXT-X-TARGETDURATION:2
"""

cmd = "ffmpeg -f rawvideo -framerate 30 -pix_fmt rgb24 -s 640x360 -i - -c:v libx264 -x264-params keyint=10:scenecut=0 -threads 0 -c:a copy -pix_fmt yuv420p -f segment -segment_format mpegts -segment_time 1 -segment_list lst.m3u8 out_%03d.ts"
fps = 30

proc = subprocess.Popen(cmd, stdin= subprocess.PIPE,shell=True)

serr = proc.stderr
sout = proc.stdout
sin = proc.stdin

start_time = time()

N = 10
pos = np.zeros([N,2],dtype=np.float32)
vel = np.zeros([N,2],dtype=np.float32)

pos[:,:] = np.random.rand(N,2) * 2. -1
vel[:,:] = np.random.rand(N,2) * 2. -1
vel -= np.mean( vel , axis= 0, keepdims = True)
pos *= .5
vel *= .5

for i in range(100000000000): # it is same as infinity loop
    
    t = i/fps
    dt = 1/fps
    
    acc = np.zeros_like(pos)    
    acc = -pos * .1
    vel += dt * acc
    pos += dt * vel
    
    frame = Frame()

    for n in range(N):
        frame.draw_circle( (.5*pos[n,0]+.5)*360 + 140, (.5*pos[n,1]+.5)*360 , 5)
    
    
    sin.write( frame.x.tobytes() )
    sin.flush()
        
    while ( True ):
        dur = time() - start_time
        if ( dur*fps > i ):
            break
        sleep(0.1)
        
    if (i%fps == 0 and (i//fps)>5):
        print (end="#") # check well working :)
        
        # READ and Update m3u8 file
        with open("lst.m3u8","r") as f:
            lines = f.readlines()
        med_seq = int(lines[-9].split(".")[0].split("_")[1])
        head = head_tmp.format(med_seq)
        tail = lines[-10:]
        
        with open("cap.m3u8","w",encoding="utf-8") as f:
            f.writelines( head )
            f.writelines( tail )
            
        # Remove older mpeg-ts files ( otherwise disk becomes full ... :(
        for file in os.listdir():
            if ( file.split(".")[-1] != "ts" ):
                continue
            filetime = os.path.getmtime(file)
            if ( time() - filetime > 30 ): ## file is older than 30 seconds
                os.remove( file )


sin.close()
proc.wait()

