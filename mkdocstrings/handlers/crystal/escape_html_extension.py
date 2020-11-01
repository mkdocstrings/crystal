from markdown import Markdown
from markdown.extensions import Extension


class EscapeHtmlExtension(Extension):
    def extendMarkdown(self, md: Markdown):
        del md.preprocessors["html_block"]
        del md.inlinePatterns["html"]
