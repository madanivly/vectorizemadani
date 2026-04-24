from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response, HTMLResponse
from PIL import Image, ImageFilter, ImageEnhance
import vtracer
import tempfile
import os

app = FastAPI()

HTML = open(os.path.join(os.path.dirname(__file__), "index.html")).read()

@app.get("/")
async def root():
    return HTMLResponse(content=HTML)

def preprocess_image(input_path: str, output_path: str):
    img = Image.open(input_path).convert("RGBA")

    # 1. Upscale 2x for better detail
    new_size = (img.width * 2, img.height * 2)
    img = img.resize(new_size, Image.LANCZOS)

    # 2. Flatten alpha onto white background
    background = Image.new("RGB", img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[3])
    img = background

    # 3. Slight blur to reduce pixel noise
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    # 4. Boost contrast for cleaner color boundaries
    img = ImageEnhance.Contrast(img).enhance(1.3)

    # 5. Sharpen edges for cleaner path detection
    img = img.filter(ImageFilter.SHARPEN)

    img.save(output_path, format="PNG")


@app.post("/api/vectorize")
async def vectorize(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    preprocessed_path = tmp_path + "_processed.png"
    output_path = tmp_path + ".svg"

    try:
        preprocess_image(tmp_path, preprocessed_path)

        vtracer.convert_image_to_svg_py(
            preprocessed_path,
            output_path,
            colormode="color",
            hierarchical="stacked",
            mode="spline",
            filter_speckle=8,
            color_precision=8,
            layer_difference=16,
            corner_threshold=90,
            length_threshold=2.0,
            max_iterations=10,
            splice_threshold=90,
            path_precision=8
        )

        with open(output_path, "r") as f:
            svg_code = f.read()

        return Response(content=svg_code, media_type="image/svg+xml")

    except Exception as e:
        return Response(content=f"Error: {str(e)}", status_code=500)

    finally:
        for path in [tmp_path, preprocessed_path, output_path]:
            if os.path.exists(path):
                os.remove(path)
