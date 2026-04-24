from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
import vtracer
import tempfile
import os

app = FastAPI()

@app.post("/api/vectorize")
async def vectorize(file: UploadFile = File(...)):
    # Vercel only allows writing to /tmp
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    output_path = tmp_path + ".svg"
    
    try:
        # THE FIX: In some versions, you call vtracer.vtracer.convert
        # In others, it's just vtracer.convert_to_svg. 
        # This logic handles both.
        if hasattr(vtracer, 'convert_image_to_svg'):
            vtracer.convert_image_to_svg(tmp_path, output_path)
        else:
            # This is the "module is not callable" fix
            vtracer.vtracer.convert_image_to_svg(tmp_path, output_path)
        
        with open(output_path, "r") as f:
            svg_code = f.read()
            
        return Response(content=svg_code, media_type="image/svg+xml")
    
    except Exception as e:
        return Response(content=f"Error: {str(e)}", status_code=500)
    
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)
        if os.path.exists(output_path): os.remove(output_path)

app = app