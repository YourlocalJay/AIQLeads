from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from app.services.logging import logger
from ..exceptions import CaptchaError


class CaptchaExtractor:
    """
    Extract and handle CAPTCHA challenges
    """

    CAPTCHA_PATTERNS = {
        "recaptcha": {
            "img_class": "rc-image-tile-wrapper",
            "iframe_name": "a-",
            "checkbox_id": "recaptcha-anchor",
        },
        "hcaptcha": {
            "img_class": "hcaptcha-challenge-image",
            "checkbox_class": "h-captcha",
            "challenge_frame": "hcaptcha-challenge-frame",
        },
        "custom": {
            "img_classes": ["captcha", "verification-image", "challenge-image"],
            "form_ids": ["captcha-form", "verification-form"],
        },
    }

    @staticmethod
    async def extract_captcha_image(response) -> Optional[str]:
        """
        Extract CAPTCHA image URL from response

        Args:
            response: HTTP response (string or response object)

        Returns:
            Optional[str]: CAPTCHA image URL if found

        Raises:
            CaptchaError: If CAPTCHA extraction fails
        """
        try:
            # Handle different response types
            if isinstance(response, str):
                html_content = response
            else:
                html_content = (
                    response.text
                    if hasattr(response, "text")
                    else await response.content()
                )

            soup = BeautifulSoup(html_content, "html.parser")

            # Check for reCAPTCHA
            recaptcha_img = soup.find(
                "img",
                {"class": CaptchaExtractor.CAPTCHA_PATTERNS["recaptcha"]["img_class"]},
            )
            if recaptcha_img and "src" in recaptcha_img.attrs:
                return recaptcha_img["src"]

            # Check for hCaptcha
            hcaptcha_img = soup.find(
                "img",
                {"class": CaptchaExtractor.CAPTCHA_PATTERNS["hcaptcha"]["img_class"]},
            )
            if hcaptcha_img and "src" in hcaptcha_img.attrs:
                return hcaptcha_img["src"]

            # Check for custom CAPTCHAs
            for class_name in CaptchaExtractor.CAPTCHA_PATTERNS["custom"][
                "img_classes"
            ]:
                img = soup.find("img", {"class": class_name})
                if img and "src" in img.attrs:
                    return img["src"]

        except Exception as e:
            error_msg = f"CAPTCHA extraction failed: {e}"
            logger.error(error_msg)
            raise CaptchaError(error_msg)

        return None

    @staticmethod
    def detect_captcha_type(html_content: str) -> Optional[Dict[str, Any]]:
        """
        Detect type of CAPTCHA present in HTML

        Args:
            html_content: HTML content to analyze

        Returns:
            Optional[Dict[str, Any]]: CAPTCHA details if found
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Check for reCAPTCHA
        if soup.find("div", {"class": "g-recaptcha"}) or soup.find(
            "iframe", {"title": lambda x: x and "reCAPTCHA" in x}
        ):
            return {
                "type": "recaptcha",
                "version": "v2" if soup.find("div", {"class": "g-recaptcha"}) else "v3",
            }

        # Check for hCaptcha
        if soup.find("div", {"class": "h-captcha"}) or soup.find(
            "iframe", {"data-hcaptcha-widget-id": True}
        ):
            return {
                "type": "hcaptcha",
                "challenge_frame": soup.find(
                    "iframe",
                    {
                        "name": CaptchaExtractor.CAPTCHA_PATTERNS["hcaptcha"][
                            "challenge_frame"
                        ]
                    },
                )
                is not None,
            }

        # Check for custom CAPTCHA
        for form_id in CaptchaExtractor.CAPTCHA_PATTERNS["custom"]["form_ids"]:
            if soup.find("form", {"id": form_id}):
                return {
                    "type": "custom",
                    "form_id": form_id,
                    "has_image": any(
                        soup.find("img", {"class": cls})
                        for cls in CaptchaExtractor.CAPTCHA_PATTERNS["custom"][
                            "img_classes"
                        ]
                    ),
                }

        return None

    @staticmethod
    async def is_captcha_page(response) -> bool:
        """
        Check if page contains a CAPTCHA

        Args:
            response: HTTP response

        Returns:
            bool: Whether page contains CAPTCHA
        """
        try:
            html_content = (
                response.text if hasattr(response, "text") else await response.content()
            )
            captcha_type = CaptchaExtractor.detect_captcha_type(html_content)
            return captcha_type is not None
        except Exception as e:
            logger.error(f"CAPTCHA detection failed: {e}")
            return False

    @staticmethod
    def get_bypass_headers() -> Dict[str, str]:
        """
        Get headers that may help bypass CAPTCHA

        Returns:
            Dict[str, str]: Anti-CAPTCHA headers
        """
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }
