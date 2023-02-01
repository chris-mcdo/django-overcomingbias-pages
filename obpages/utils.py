import bs4
import slugify


def to_slug(text, max_length):
    return slugify.slugify(text, max_length=max_length)


def escape_single_quotes(text: str):
    return text.replace("\\", "\\\\").replace("'", "\\'")


def html_to_plaintext(text: str):
    return bs4.BeautifulSoup(text, "lxml").get_text()
