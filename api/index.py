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
        # This is the standard call for the vtracer-python library
        vtracer.vtracer(tmp_path, output_path)
        
        with open(output_path, "r") as f:
            svg_code = f.read()
        return Response(content=svg_code, media_type="image/svg+xml")
    
    except Exception as e:
        # If the direct call fails, try the convert_to_svg method
        try:
            vtracer.convert_to_svg(tmp_path, output_path)
            with open(output_path, "r") as f:
                svg_code = f.read()
            return Response(content=svg_code, media_type="image/svg+xml")
        except:
            return Response(content=f"Engine Error: {str(e)}", status_code=500)
    
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)
        if os.path.exists(output_path): os.remove(output_path)

app = app