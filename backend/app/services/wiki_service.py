import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class WikiService:
    def __init__(self):
        # Lazy initialization
        self.wiki = None
        self.initialized = False
        self._init_wiki()
        
    def _init_wiki(self):
        """Initialize the Wikipedia API if not already initialized."""
        if self.initialized:
            return
            
        try:
            import wikipediaapi
            # User agent is required by Wikipedia API policy
            self.wiki = wikipediaapi.Wikipedia(
                user_agent='PoliticalPulse (harshvardhan.khamkar@example.com)',
                language='en',
                extract_format=wikipediaapi.ExtractFormat.WIKI
            )
            self.initialized = True
            logger.info("Wikipedia API initialized successfully")
        except ImportError:
            logger.error("wikipedia-api package is missing. Install: pip install Wikipedia-API")
            self.initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize Wikipedia API: {e}")
            self.initialized = False

    def get_party_info(self, party_name: str) -> Dict[str, Any]:
        """
        Fetch party information from Wikipedia.
        Includes summary, history, and potentially other details.
        """
        self._init_wiki()
        
        if not self.initialized or not self.wiki:
            logger.warning(f"Wikipedia API not initialized, cannot fetch info for: {party_name}")
            return {}
            
        try:
            # Try full name first
            page = self.wiki.page(party_name)
            
            # If not found or very short, try searching or adding "political party"
            if not page.exists() or len(page.summary) < 50:
                 page = self.wiki.page(f"{party_name} (political party)")
                 
            if not page.exists():
                logger.warning(f"Wikipedia page not found for: {party_name}")
                return {}

            info = {
                "name": page.title,
                "overview": page.summary,
                "history": self._get_section_text(page, "history"),
                "ideology": self._extract_ideology(page),
                "founded_year": self._extract_founded_year(page)
            }
            
            return info
        except Exception as e:
            logger.error(f"Error fetching Wikipedia data for {party_name}: {e}")
            return {}

    def _get_section_text(self, page, section_title: str) -> Optional[str]:
        """Recursively search for a section and return its text."""
        for section in page.sections:
            if section.title.lower() == section_title.lower():
                return section.text
            # Check subsections
            for sub in section.sections:
                if sub.title.lower() == section_title.lower():
                    return sub.text
        return None

    def _extract_ideology(self, page) -> Optional[str]:
        """
        Simple extraction of ideology. 
        Since we don't have a clean infobox parser, we'll try to find it in the summary 
        or look for an 'Ideology' section.
        """
        # 1. Check for an "Ideology" section
        ideology_text = self._get_section_text(page, "Ideology")
        if ideology_text:
            # Return first few sentences
            return ideology_text.split('.')[0] + '.'
            
        # 2. Heuristic: Look for common ideologies in the summary
        ideologies = ["Right-wing", "Left-wing", "Centrist", "Nationalism", "Socialism", "Liberalism", "Conservatism"]
        found = []
        for idl in ideologies:
            if idl.lower() in page.summary.lower():
                found.append(idl)
        
        if found:
            return ", ".join(found[:3])
            
        return None

    def _extract_founded_year(self, page) -> Optional[int]:
        """Heuristically extract founded year from summary."""
        import re
        # Look for "founded in XXXX" or "formed in XXXX" or "established on ... XXXX"
        match = re.search(r'(?:founded|formed|established|created)\s+(?:in|on|at)?\s+.*?([12][0-9]{3})', page.summary)
        if match:
            return int(match.group(1))
        return None

# Global instance
wiki_service = WikiService()
