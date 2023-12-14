import http.cookiejar as cookielib


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
