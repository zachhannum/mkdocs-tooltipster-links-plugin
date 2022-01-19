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


def tooltip(md_link_path, link, soup):
    input_file = codecs.open(str(md_link_path), mode="r", encoding="utf-8")
    text = input_file.read()
    contents = frontmatter.loads(text).content
    # remove links
    contents = re.sub("!?((\[{2}(.*)\]{2})|\[\]\((.*)\))", "", contents)
    html = markdown.markdown(contents)
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
        md_link_path = str(md_link_path).replace(f"{os.sep}.md",f"{os.sep}index.md")
    else:
        md_link_path = str(md_link_path).replace(f"{os.sep}.md", "")
    file = [
        x for x in all_docs if Path(x) == Path(md_link_path)
    ]
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
        md_link_path=""
        all_docs = [
            x
            for x in iglob(str(docs) + os.sep + "**", recursive=True)
            if x.endswith(".md")
        ]
        for link in soup.findAll(
            "a",
            {"class": None},
            href=lambda href: href is not None and not href.startswith("http") and not 'www' in href,
        ):
            if len(link['href']) > 0:
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

            if md_link_path != "" and len(link['href']) > 0:
                md_link_path = re.sub("#(.*)\.md", ".md", str(md_link_path))
                md_link_path = Path(md_link_path)

                if os.path.isfile(md_link_path):
                    soup = tooltip(md_link_path, link, soup)
                else:
                    link_found = search_doc(md_link_path, all_docs)
                    if link_found != 0:
                        soup = tooltip(link_found, link, soup)

        souped_html = soup.prettify(soup.original_encoding)
        return souped_html
