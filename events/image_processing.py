from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.utils.text import slugify
from PIL import Image, ImageOps


MAX_EVENT_IMAGE_DIMENSIONS = (1600, 900)
EVENT_IMAGE_QUALITY = 82


def optimize_event_image(uploaded_image):
    """Return a metadata-free 16:9 JPEG suitable for event cards."""
    uploaded_image.seek(0)
    with Image.open(uploaded_image) as source:
        image = ImageOps.exif_transpose(source)
        has_transparency = image.mode in {"RGBA", "LA"} or (
            image.mode == "P" and "transparency" in image.info
        )
        if has_transparency:
            image_with_alpha = image.convert("RGBA")
            background = Image.new("RGB", image_with_alpha.size, "white")
            background.paste(
                image_with_alpha,
                mask=image_with_alpha.getchannel("A"),
            )
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")

        target_width = min(MAX_EVENT_IMAGE_DIMENSIONS[0], image.width)
        target_height = round(target_width * 9 / 16)
        if target_height > image.height:
            target_height = min(MAX_EVENT_IMAGE_DIMENSIONS[1], image.height)
            target_width = round(target_height * 16 / 9)

        image = ImageOps.fit(
            image,
            (target_width, target_height),
            method=Image.Resampling.LANCZOS,
        )
        output = BytesIO()
        image.save(
            output,
            format="JPEG",
            quality=EVENT_IMAGE_QUALITY,
            optimize=True,
            progressive=True,
        )

    stem = slugify(Path(uploaded_image.name).stem) or "event-image"
    return ContentFile(output.getvalue(), name=f"{stem}.jpg")
