# The most corner-cutting working http-live-streaming (HLS) programs
I want easy-to-use and smallest package to stream movie which is made by python ( like numpy, PIL, ... ).
So I Made it.

## How-to-use
only run `python stream.py`.
While `stream.py` running, you can access a page on `localhost:8000`. 
The page shows real-time generated streaming movie. :)

## Requirement
- ffmpeg ( install and PATH it )
- numpy ( python package )
- PIL ( python package)

## Customize
`sin.write( frame.x.tobytes() )` writes (created) image buffer to ffmpeg.
So you can cutomize generated contents to change this buffers.
( This codes writes rgb24 image !)

