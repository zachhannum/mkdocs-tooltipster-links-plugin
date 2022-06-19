import codecs
import os
import re
from glob import iglob
from pathlib import Path
from urllib.parse import unquote
import frontmatter
import markdown
from bs4 import BeautifulSoup
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mdx_wikilink_plus.mdx_wikilink_plus import WikiLinkPlusExtension


def mini_ez_links(urlo, base, end, url_whitespace, url_case):
    base, url_blog = base
    url_blog_path = [x for x in url_blog.split("/") if len(x) > 0]
    url_blog_path = url_blog_path[len(url_blog_path) - 1]
    all_docs = [
        re.sub(rf"(.*){url_blog_path}/docs/*", "", x.replace("\\", "/")).replace(
            ".md", ""
        )
        for x in iglob(str(base) + os.sep + "**", recursive=True)
        if os.path.isfile(x)
    ]
    file_name = urlo[2].replace("index", "")
    file_found = [
        "/" + x for x in all_docs if os.path.basename(x) == file_name or x == file_name
    ]
    if file_found:
        file_path = file_found[0].replace(base, "")
        url = file_path.replace("\\", "/").replace(".md", "")
        url = url.replace("//", "/")
        url = "/" + url_blog_path + url
    else:
        url = file_name
    return url


def tooltip(md_link_path, link, soup, config):
    docs = config["docs_dir"]
    url = config["site_url"]
    md_config = {
        "mdx_wikilink_plus": {
            "base_url": (docs, url),
            "build_url": mini_ez_links,
            "image_class": "wikilink",
        }
    }
    input_file = codecs.open(str(md_link_path), mode="r", encoding="utf-8")
    text = input_file.read()
    contents = frontmatter.loads(text).content
    # remove links
    contents = re.sub("!", "", contents)
    contents = re.sub("\.(png|jpeg|jpg|webm|gif)", "", contents)
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
    header = link_soup.find("h1")
    preview = link_soup.find("p")
    if link.contents:
        tooltip_id = link.contents[0].strip().replace(" ", "") + "_tooltip_id"
        tooltip_id = re.sub(r"\W+", "", tooltip_id)
        link["class"] = link.get("class", []) + ["link-tooltip"]
        link["data-tooltip-content"] = "#" + tooltip_id
        tooltip_template = soup.new_tag("div")
        tooltip_template["class"] = ["tooltip_templates"]
        tooltip_content = soup.new_tag("div", id=tooltip_id)
        tooltip_template.append(tooltip_content)
        if header:
            tooltip_content.append(header)
        if preview:
            tooltip_content.append(preview)
        soup.body.append(tooltip_template)
    return soup


def search_doc(md_link_path, all_docs):

    if os.path.basename(md_link_path) == ".md":
        md_link_path = str(md_link_path).replace(f"{os.sep}.md", f"{os.sep}index.md")
    else:
        md_link_path = str(md_link_path).replace(f"{os.sep}.md", "")
    file = [x for x in all_docs if Path(x) == Path(md_link_path)]
    if len(file) > 0:
        return file[0]
    return 0


class TooltipsterLinks(BasePlugin):

    config_scheme = (("param", config_options.Type(str, default="")),)

    def __init__(self):
        self.enabled = True
        self.total_time = 0

    def on_post_page(self, output_content, page, config):
        soup = BeautifulSoup(output_content, "html.parser")
        docs = Path(config["docs_dir"])
        md_link_path = ""
        all_docs = [
            x
            for x in iglob(str(docs) + os.sep + "**", recursive=True)
            if x.endswith(".md")
        ]
        for link in soup.findAll(
            "a",
            {"class": None},
            href=lambda href: href is not None
            and not href.startswith("http")
            and not "www" in href,
        ):
            if len(link["href"]) > 0:
                if link["href"][0] == ".":
                    md_src_path = link["href"][3:-1] + ".md"
                    md_src_path = md_src_path.replace(".m.md", ".md")
                    md_link_path = os.path.join(
                        os.path.dirname(page.file.abs_src_path), md_src_path
                    )
                    md_link_path = Path(unquote(md_link_path)).resolve()

                elif link["href"][0] == "/":
                    md_src_path = link["href"][1:] + ".md"
                    md_link_path = os.path.join(config["docs_dir"], md_src_path)
                    md_link_path = Path(unquote(md_link_path)).resolve()

                elif link["href"][0] != "#":
                    md_src_path = link["href"][:-1] + ".md"
                    md_link_path = os.path.join(
                        os.path.dirname(page.file.abs_src_path), md_src_path
                    )
                    md_link_path = Path(unquote(md_link_path)).resolve()
            else:
                md_src_path = link["href"][:-1] + ".md"
                md_link_path = os.path.join(
                    os.path.dirname(page.file.abs_src_path), md_src_path
                )
                md_link_path = Path(unquote(md_link_path)).resolve()

            if md_link_path != "" and len(link["href"]) > 0:
                md_link_path = re.sub("#(.*)\.md", ".md", str(md_link_path))
                md_link_path = Path(md_link_path)

                if os.path.isfile(md_link_path):
                    soup = tooltip(md_link_path, link, soup, config)
                else:
                    link_found = search_doc(md_link_path, all_docs)
                    if link_found != 0:
                        soup = tooltip(link_found, link, soup, config)
        return soup.original_encoding
