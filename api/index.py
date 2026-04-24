from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
from PIL import Image, ImageFilter, ImageEnhance
import vtracer
import tempfile
import os
import io

app = FastAPI()

def preprocess_image(input_path: str, output_path: str):
    """
    Preprocess the image before vectorization for smoother output:
    - Upscale 2x (more detail for vtracer to work with)
    - Sharpen edges
    - Boost contrast slightly
    - Reduce noise with a smooth filter
    """
    img = Image.open(input_path).convert("RGBA")

    # 1. Upscale 2x for better detail
    new_size = (img.width * 2, img.height * 2)
    img = img.resize(new_size, Image.LANCZOS)

    # 2. Convert to RGB (vtracer needs PNG without alpha issues)
    background = Image.new("RGB", img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[3])  # use alpha as mask
    img = background

    # 3. Slight blur to reduce noise before tracing
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    # 4. Boost contrast for cleaner color boundaries
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)

    # 5. Sharpen edges so vtracer picks up clean paths
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
        # Step 1: Preprocess image
        preprocess_image(tmp_path, preprocessed_path)

        # Step 2: Vectorize with optimized settings
        vtracer.convert_image_to_svg_py(
            preprocessed_path,
            output_path,
            colormode="color",
            hierarchical="stacked",
            mode="spline",          # smoothest curve mode
            filter_speckle=8,       # removes small noise artifacts
            color_precision=8,      # high color accuracy
            layer_difference=16,    # color layer sensitivity
            corner_threshold=90,    # higher = fewer sharp corners
            length_threshold=2.0,   # lower = more detail retained
            max_iterations=10,
            splice_threshold=90,    # higher = smoother curve joins
            path_precision=8        # high path precision
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
