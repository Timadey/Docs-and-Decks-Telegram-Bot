import re

def escape_markdown(text):
        """Escapes special characters in Markdown text to avoid parsing errors."""
        return re.sub(r'([_*[\]()~`>#+-=|{}.!])', r'\\\1', text)