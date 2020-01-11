import os
import sys
from timeit import default_timer as timer
from datetime import datetime, timedelta
import re

from mkdocs import utils as mkdocs_utils
from mkdocs.config import config_options, Config
from mkdocs.plugins import BasePlugin

from bs4 import BeautifulSoup
import markdown
import codecs

class TooltipsterLinks(BasePlugin):

    config_scheme = (
        ('param', config_options.Type(mkdocs_utils.string_types, default='')),
    )

    def __init__(self):
        self.enabled = True
        self.total_time = 0

    def on_post_page(self, output_content, page, config):
        soup = BeautifulSoup(output_content, 'html.parser')
        
        for link in soup.findAll("a", {"class" : None}, href=lambda href: href is not None and not href.startswith('http') ):
            if link['href'][0] == ".":
                md_src_path = link['href'][3:-1] + ".md"
            else:
                md_src_path = link['href'][:-1] + ".md"
            md_link_path = os.path.join(os.path.dirname(page.file.abs_src_path), md_src_path )
            if os.path.isfile(md_link_path):

                # This block is getting the markdown from the link, converting to html
                # and getting the header and first paragraph block to use in the tooltip
                input_file = codecs.open(md_link_path, mode="r", encoding="utf-8")
                text = input_file.read()
                html = markdown.markdown(text)
                link_soup = BeautifulSoup(html, 'html.parser')
                header = link_soup.find("h1") 
                preview = link_soup.find("p")

                # This block is constructing the tooltip
                #TODO: possibly add numbering so that tooltips for the same link are unique
                tooltip_id = link.contents[0].strip().replace(" ", "") + '_tooltip_id'
                tooltip_id = re.sub(r'\W+', '', tooltip_id)
                link['class'] = link.get('class', []) + ['link-tooltip']
                link['data-tooltip-content'] = '#' + tooltip_id
                tooltip_template = soup.new_tag('div')
                tooltip_template['class'] = ['tooltip_templates']
                tooltip_content = soup.new_tag('div', id=tooltip_id)
                tooltip_template.append(tooltip_content)
                if header:
                		tooltip_content.append(header)
                if preview:
                		tooltip_content.append(preview)
                soup.body.append(tooltip_template)

        souped_html = soup.prettify(soup.original_encoding)
        return souped_html 

