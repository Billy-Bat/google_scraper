import http.cookiejar as cookielib
from PIL import Image
from io import BytesIO


def to_cookielib_cookie(selenium_cookie):
    return cookielib.Cookie(
        version=0,
        name=selenium_cookie["name"],
        value=selenium_cookie["value"],
        port="80",
        port_specified=False,
        domain=selenium_cookie["domain"],
        domain_specified=True,
        domain_initial_dot=False,
        path=selenium_cookie["path"],
        path_specified=True,
        secure=selenium_cookie["secure"],
        expires=selenium_cookie["expiry"],
        discard=False,
        comment=None,
        comment_url=None,
        rest=None,
        rfc2109=False,
    )


def put_cookies_in_jar(selenium_cookies, cookie_jar):
    for cookie in selenium_cookies:
        cookie_jar.set_cookie(to_cookielib_cookie(cookie))


def get_img_from_bytes(input_bytes: bytes) -> Image:
    return Image.open(BytesIO(input_bytes))


def resize_img(img: Image, max_size: int = 810_000) -> Image:
    """
    resize an image given a max number of pixels in the img
    """
    if img.size[0] * img.size[1] > max_size:
        ratio = max_size / (img.size[0] * img.size[1])
        new_width = int(img.size[0] * ratio)
        new_height = int(img.size[1] * ratio)
        img = img.resize((new_width, new_height))

    return img
