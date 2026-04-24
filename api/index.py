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
        # THE RAW FIX:
        # We are bypassing the module wrappers and calling the engine directly.
        vtracer.vtracer.convert_image_to_svg(tmp_path, output_path)
        
        with open(output_path, "r") as f:
            svg_code = f.read()
            
        return Response(content=svg_code, media_type="image/svg+xml")
    
    except Exception as e:
        # If that fails, try the absolute simplest call possible
        try:
            vtracer.convert_image_to_svg(tmp_path, output_path)
            with open(output_path, "r") as f:
                svg_code = f.read()
            return Response(content=svg_code, media_type="image/svg+xml")
        except Exception as e2:
            return Response(content=f"Final Engine Check: {str(e)} | {str(e2)}", status_code=500)
    
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)
        if os.path.exists(output_path): os.remove(output_path)

app = app
