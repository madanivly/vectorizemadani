from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
import vtracer
import tempfile
import os

app = FastAPI()

@app.post("/api/vectorize")
async def vectorize(file: UploadFile = File(...)):
    # Save uploaded file to a temporary spot
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    output_path = tmp_path.replace(".png", ".svg")
    
    # Run the tracing engine
    vtracer.convert_image_to_svg(tmp_path, output_path)
    
    with open(output_path, "r") as f:
        svg_code = f.read()
    
    # Clean up files
    os.remove(tmp_path)
    os.remove(output_path)
    
    return Response(content=svg_code, media_type="image/svg+xml")