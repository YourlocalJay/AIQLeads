from bs4 import BeautifulSoup

class CaptchaExtractor:
    """Extracts CAPTCHA image links from scraped HTML content."""

    CAPTCHA_CLASSES = ["rc-image-tile-wrapper", "hcaptcha-challenge-image", "captcha", "challenge-image"]

    @staticmethod
    async def extract_captcha_image(response) -> Optional[str]:
        """Extracts CAPTCHA image source from HTML response."""
        try:
            soup = BeautifulSoup(await response.text(), "html.parser")
            for class_name in CaptchaExtractor.CAPTCHA_CLASSES:
                img = soup.find("img", {"class": class_name})
                if img and "src" in img.attrs:
                    return img["src"]
        except Exception:
            return None
