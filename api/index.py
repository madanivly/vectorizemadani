from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
import vtracer
import tempfile
import os

app = FastAPI()

@app.post("/api/vectorize")
async def vectorize(file: UploadFile = File(...)):
    # Vercel only allows writing to the /tmp folder
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    output_path = tmp_path + ".svg"
    
    try:
        # THE FINAL FIX: 
        # This checks if we need to call vtracer.vtracer or just vtracer
        if callable(getattr(vtracer, 'vtracer', None)):
            vtracer.vtracer(tmp_path, output_path)
        elif hasattr(vtracer, 'convert_image_to_svg'):
            vtracer.convert_image_to_svg(tmp_path, output_path)
        else:
            # Fallback for the Rust-based direct wrapper
            vtracer.convert(tmp_path, output_path)
        
        with open(output_path, "r") as f:
            svg_code = f.read()
            
        return Response(content=svg_code, media_type="image/svg+xml")
    
    except Exception as e:
        return Response(content=f"Backend Error: {str(e)}", status_code=500)
    
    finally:
        # Clean up files
        if os.path.exists(tmp_path): os.remove(tmp_path)
        if os.path.exists(output_path): os.remove(output_path)

app = app
