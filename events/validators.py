from django.core.exceptions import ValidationError


MAX_EVENT_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_EVENT_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


def validate_event_image_size(image):
    if image.size > MAX_EVENT_IMAGE_SIZE:
        raise ValidationError("The event image must not exceed 5 MB.")
