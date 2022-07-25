import codecs
import os
import re
from glob import iglob
from pathlib import Path
from typing import Dict, Union, List, Tuple
from urllib.parse import unquote, quote
import frontmatter
import markdown
import ast
from bs4 import BeautifulSoup
from bs4.element import Tag
from mkdocs.config import config_options
from mkdocs.config.base import Config
from mkdocs.structure.pages import Page
from mkdocs.plugins import BasePlugin
from mdx_wikilink_plus.mdx_wikilink_plus import WikiLinkPlusExtension
from mkdocs_callouts.plugin import CalloutsPlugin
from custom_attributes.plugin import convert_text_attributes

def mini_ez_links(urlo, base, end, url_whitespace, url_case):
    base, url_blog, md_link_path = base
    url_blog_path = [x for x in url_blog.split('/') if len(x) > 0]
    url_blog_path = url_blog_path[len(url_blog_path) - 1]
    internal_link = Path(md_link_path, urlo[2]).resolve()
    if os.path.isfile(internal_link):
        internal_link = str(internal_link).replace(base, '')
    else:  # fallback to searching
        if urlo[2].endswith('.md'):
            internal_link = str(search_file_in_documentation(
                Path(urlo[2]).resolve(), Path(md_link_path).parent))
        if not os.path.isfile(internal_link):  # manual search
            file_name = urlo[2].replace('index', '')
            file_name = file_name.replace('../', '')
            file_name = file_name.replace('./', '')

            all_docs = [
                re.sub(rf"(.*)({url_blog_path})?/docs/*", '', x.replace('\\', '/')).replace(
                    '.md', ''
                )
                for x in iglob(str(base) + os.sep + '**', recursive=True)
                if os.path.isfile(x)
            ]
            file_found = [
                '/' + x for x in all_docs if os.path.basename(x) == file_name or x == file_name
            ]
            if file_found:
                internal_link = file_found[0]
            else:
                return file_name
    file_path = internal_link.replace(base, '')
    url = file_path.replace('\\', '/').replace('.md', '')
    url = url.replace('//', '/')
    url = url_blog[:-1] + quote(url)
    if not url.startswith(('https:/', 'http:/')):
        url = 'https://' + url
    if not url.endswith('/') and not url.endswith(('png', 'jpg', 'jpeg', 'gif', 'webm')):
        url = url + '/'
    return url


def strip_comments(markdown):
    file_content = markdown.split('\n')
    markdown = ''
    for line in file_content:
        if not re.search(r'%%(.*)%%', line) or not line.startswith('%%') or not line.endswith('%%'):
            markdown += line + '\n'
    markdown = re.sub(r'%%(.*)%%', '', markdown, flags=re.DOTALL)
    return markdown

def search_in_file(citation_part: str, contents: str):
    """
    Search a part in the file
    Args:
        citation_part: The part to find
        contents: The file contents
    Returns: the part found
    """
    data = contents.split('\n')
    if '#' not in citation_part:
        # All text citation
        return contents
    elif '#' in citation_part and not '^' in citation_part:
        # cite from title
        sub_section = []
        citation_part = citation_part.replace('-', ' ').replace('#', '# ').upper()
        heading = 0
        for i in data:
            if citation_part in i.upper() and i.startswith('#'):
                heading = i.count('#') * (-1)
                sub_section.append([i])
            elif heading != 0:
                inverse = i.count('#') * (-1)
                if inverse == 0 or heading > inverse:
                    sub_section.append([i])
                elif inverse >= heading:
                    break
        sub_section = [x for y in sub_section for x in y]

        sub_section = '\n'.join(sub_section)
        return sub_section
    elif '#^' in citation_part:
        # cite from block
        citation_part = citation_part.replace('#', '').upper()
        for i in data:
            if citation_part in i.upper():
                return i.replace(citation_part, '')
    return []

def tooltip(md_link_path: Path, link:Tag, soup: BeautifulSoup, config: Config, plugin_config: Dict):
    '''
    Create a tooltip for the link
    '''
    docs = config["docs_dir"]
    url = config["site_url"]
    callouts = plugin_config["callout"]
    custom_attr = plugin_config["custom_attr"]
    max_char = plugin_config["max_char"]
    cut_contents = plugin_config["cut_contents"]

    md_config = {
        "mdx_wikilink_plus": {
            "base_url": (docs, url, md_link_path),
            "build_url": mini_ez_links,
            "image_class": "wikilink",
        }
    }
    input_file = codecs.open(str(md_link_path), mode="r", encoding="utf-8")
    text = input_file.read()
    contents = frontmatter.loads(text).content
    citation = get_citation_part(link)
    contents = search_in_file(citation, contents)
    if callouts:
        contents = CalloutsPlugin().on_page_markdown(contents, None, None, None)
    if len(custom_attr) > 0:
        config_attr = {
            'file': custom_attr,
            'docs_dir': docs
        }
        contents = convert_text_attributes(contents, config_attr)
    contents = strip_comments(contents)
    if max_char > 1 and len(contents) > max_char:
        contents = contents[:int(max_char)] + cut_contents
    html = markdown.markdown(
        contents,
        extensions=[
            "nl2br",
            "footnotes",
            "attr_list",
            "mdx_breakless_lists",
            "smarty",
            "sane_lists",
            "tables",
            "admonition",
            WikiLinkPlusExtension(md_config["mdx_wikilink_plus"]),
        ],
    )
    link_soup = BeautifulSoup(html, "html.parser")
    link_soup=BeautifulSoup(
            str(link_soup).replace(
                    '!<img class="wikilink', '<img class="wikilink'
                ), "html.parser")
    preview = link_soup.findAll(["p", "li"])
    if link.contents:
        tooltip_id = link.contents[0].strip().replace(" ", "") + "_tooltip_id"
        tooltip_id = re.sub(r"\W+", "", tooltip_id)
        link["class"] = link.get("class", []) + ["link-tooltip"]
        link["data-tooltip-content"] = "#" + tooltip_id
        tooltip_template = soup.new_tag("div")
        tooltip_template["class"] = ["tooltip_templates"]
        tooltip_content = soup.new_tag("div", id=tooltip_id)
        tooltip_template.append(tooltip_content)
        preview = '\n'.join([str(i) for i in list(preview)])
        preview = BeautifulSoup(preview, "html.parser")
        if preview:
            tooltip_content.append(preview)
        soup.body.append(tooltip_template)
    return soup

def create_link(link):
    """
    Fix the ends of a file link with adding .md if not present
    """
    if link.endswith('/'):
        return link[:-1] + '.md'
    else:
        return link + '.md'

def search_file_in_documentation(link: Union[Path, str], config_dir: Path) -> Union[Path,int]:
    """
    Search a file in the documentation
    Returns: 
        The file path if found
        0 otherwise
    """
    file_name = os.path.basename(link)
    if not file_name.endswith('.md'):
        file_name = file_name + '.md'
    for p in config_dir.rglob(f"*{file_name}"):
        return p
    return 0

def get_citation_part(link: Tag) -> Union[str,List[str],None]:
    """
    Get the citation part of a link if # in the href
    """
    if '#' in link.get('href', ''):
        citation_part = re.sub('^(.*)#', '#', link['href'])
    else:
        citation_part = link.get('href', '')
    return citation_part

def href_relative_link(link, page, docs):
    md_src = create_link(unquote(link['href']))
    md_link_path = Path(os.path.dirname(page.file.abs_src_path), md_src).resolve()
    if link["href"].startswith("./#"):
        md_link_path = page.file.abs_src_path
    if not os.path.isfile(md_link_path):
        md_link_path = search_file_in_documentation(md_link_path, docs)
    return md_link_path

def href_resolve(link, config):
    md_src_path = create_link(unquote(link['href']))
    md_link_path = os.path.join(
        config['docs_dir'], md_src_path)
    md_link_path = Path(unquote(md_link_path)).resolve()
    return md_link_path

def href_header(link, page):
    md_src_path = create_link(unquote(link['href']))
    md_link_path = os.path.join(
        os.path.dirname(page.file.abs_src_path), md_src_path
    )
    md_link_path = Path(unquote(md_link_path)).resolve()
    return md_link_path

def href_unquote(link, page):
    md_src_path = create_link(unquote(link['href']))
    md_link_path = os.path.join(
        os.path.dirname(page.file.abs_src_path), md_src_path
    )
    md_link_path = Path(unquote(md_link_path)).resolve()
    return md_link_path

def convert_text_to_tooltip(link, md_link_path, config, plugin_config, soup, docs):
    if md_link_path != "" and len(link["href"]) > 0:
        md_link_path = re.sub("#(.*)\.md", ".md", str(md_link_path))
        md_link_path = Path(md_link_path)
        if os.path.isfile(md_link_path):
            return tooltip(md_link_path, link, soup, config,plugin_config)
        else:
            link_found = search_file_in_documentation(md_link_path, docs)
            if link_found != 0:
                return tooltip(link_found, link, soup, config, plugin_config)
    return soup

class TooltipsterLinks(BasePlugin):
    config_scheme = (
        ('callouts', config_options.Type(bool, default=False)),
        ('custom-attributes', config_options.Type(str, default='')),
        ('max-characters', config_options.Type(int, default=400)),
        ('truncate-character', config_options.Type(str, default='...')),
    )

    def __init__(self):
        self.enabled = True
        self.total_time = 0

    def on_post_page(self, output_content: str, page: Page, config: Config):        
        soup = BeautifulSoup(output_content, "html.parser")
        docs = Path(config["docs_dir"])
        md_link_path = ""
        callout = self.config['callouts']
        plugin_config = {"custom_attr": self.config['custom-attributes'],
            "max_char": int(self.config['max-characters']),
            "cut_contents": self.config['truncate-character'],
            "callout": callout}
        for link in soup.findAll(
            "a",
            {"class": None},
            href=lambda href: href is not None
            and not href.startswith("http")
            and not "www" in href,
        ):
            if len(link["href"]) > 0:
                if link["href"][0] == ".":
                    md_link_path = href_relative_link(link, page, docs)
                elif link["href"][0] == "/":
                   md_link_path=href_resolve(link, config)
                elif link["href"][0] != "#":
                    md_link_path=href_header(link, page)
            else:
                md_link_path = href_unquote(link, page)
            soup = convert_text_to_tooltip(link, md_link_path, config, plugin_config, soup, docs)
        return str(soup)
