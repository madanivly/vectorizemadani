from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
import vtracer
import tempfile
import os

app = FastAPI()

@app.post("/api/vectorize")
async def vectorize(file: UploadFile = File(...)):
    # Vercel only allows writing to the /tmp directory
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    # Define output path in the same /tmp directory
    output_path = tmp_path + ".svg"
    
    try:
        # Run the vectorization
        vtracer.convert(tmp_path, output_path)
        
        with open(output_path, "r") as f:
            svg_code = f.read()
            
        return Response(content=svg_code, media_type="image/svg+xml")
    
    except Exception as e:
        return Response(content=f"Error: {str(e)}", status_code=500)
    
    finally:
        # Always clean up files to avoid filling up server memory
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if os.path.exists(output_path):
            os.remove(output_path)