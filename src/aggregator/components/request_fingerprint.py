import random
from typing import Dict
from urllib.parse import urlparse

class RequestFingerprinter:
    """
    Generates randomized request headers to avoid detection
    """
    
    # Common user agents
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]

    # Common language preferences
    ACCEPT_LANGUAGES = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.8",
        "en-CA,en;q=0.7",
        "en-AU,en;q=0.6",
        "en;q=0.5",
    ]
    
    # Common platforms
    PLATFORMS = [
        "Windows NT 10.0; Win64; x64",
        "Macintosh; Intel Mac OS X 10_15_7",
        "X11; Linux x86_64",
        "Windows NT 10.0; WOW64",
        "iPhone; CPU iPhone OS 17_2 like Mac OS X",
    ]

    @classmethod
    def generate_headers(cls, base_url: str) -> Dict[str, str]:
        """
        Generate randomized request headers
        
        Args:
            base_url: Base URL for referer
        
        Returns:
            Dict[str, str]: Randomized headers
        """
        platform = random.choice(cls.PLATFORMS)
        user_agent = random.choice(cls.USER_AGENTS)
        
        headers = {
            "User-Agent": user_agent,
            "Accept-Language": random.choice(cls.ACCEPT_LANGUAGES),
            "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "DNT": "1",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Sec-Ch-Ua": f'"{user_agent.split("/")[0]}"',
            "Sec-Ch-Ua-Platform": f'"{platform.split(";")[0]}"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Upgrade-Insecure-Requests": "1",
        }
        
        # Add referer only if base URL is provided
        if base_url:
            headers["Referer"] = f"https://{urlparse(base_url).netloc}"
            
        return headers

    @classmethod
    def generate_mobile_headers(cls) -> Dict[str, str]:
        """
        Generate headers for mobile device emulation
        
        Returns:
            Dict[str, str]: Mobile-specific headers
        """
        mobile_ua = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        )
        
        return {
            "User-Agent": mobile_ua,
            "Accept-Language": random.choice(cls.ACCEPT_LANGUAGES),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "DNT": "1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Sec-Ch-Ua": '"Safari";v="17.0"',
            "Sec-Ch-Ua-Platform": '"iOS"',
            "Sec-Ch-Ua-Mobile": "?1",
            "Upgrade-Insecure-Requests": "1",
        }