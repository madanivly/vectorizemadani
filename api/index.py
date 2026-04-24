from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
import vtracer
import tempfile
import os

app = FastAPI()

@app.post("/api/vectorize")
async def vectorize(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    output_path = tmp_path + ".svg"
    
    try:
        # THE "STUBBORN LIBRARY" FIX:
        # We call vtracer.vtracer as the function itself.
        vtracer.vtracer(
            tmp_path, 
            output_path,
            mode='spline',
            clustering_mode='k-means'
        )
        
        with open(output_path, "r") as f:
            svg_code = f.read()
            
        return Response(content=svg_code, media_type="image/svg+xml")
    
    except Exception as e:
        return Response(content=f"Library structure error: {str(e)}", status_code=500)
    
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)
        if os.path.exists(output_path): os.remove(output_path)

app = app
