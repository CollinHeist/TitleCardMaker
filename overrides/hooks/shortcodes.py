from __future__ import annotations

import posixpath
import re

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page
from re import Match

# -----------------------------------------------------------------------------
# Hooks
# -----------------------------------------------------------------------------

def on_page_markdown(
    markdown: str, *, page: Page, config: MkDocsConfig, files: Files
):

    # Replace callback
    def replace(match: Match):
        type, args = match.groups()
        args = args.strip()
        if type == "version":
            return _badge_for_version(args, page, files)
        if type == "flag":
            return flag(args, page, files)
        if type == "option":
            return option(args)
        if type == "setting":
            return setting(args)
        if type == "feature":
            return _badge_for_feature(args, page, files)
        if type == "default":
            if args == "none":
                return _badge_for_default_none(page, files)
            return _badge_for_default(args, page, files)
        if type == 'overwritable':
            return _badge_for_overwritable(args, page, files)

        # Otherwise, raise an error
        raise RuntimeError(f"Unknown shortcode: {type}")

    # Find and replace all external asset URLs in current page
    return re.sub(
        r"<!-- md:(\w+)(.*?) -->",
        replace, markdown, flags = re.I | re.M
    )

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

# Create a flag of a specific type
def flag(args: str, page: Page, files: Files) -> str:
    type, *_ = args.split(" ", 1)
    if type == "experimental": 
        return _badge_for_experimental(page, files)
    if type == "required":
        return _badge_for_required(page, files)
    if type == "customization":
        return _badge_for_customization(page, files)

    raise RuntimeError(f"Unknown type: {type}")

# Create a linkable option
def option(type: str):
    _, *_, name = re.split(r"[.:]", type)
    return f"[`{name}`](#+{type}){{ #+{type} }}\n\n"

# Create a linkable setting - @todo append them to the bottom of the page
def setting(type: str):
    _, *_, name = re.split(r"[.*]", type)
    return f"`{name}` {{ #{type} }}\n\n[{type}]: #{type}\n\n"

# -----------------------------------------------------------------------------

# Resolve path of file relative to given page - the posixpath always includes
# one additional level of `..` which we need to remove
def _resolve_path(path: str, page: Page, files: Files):
    path, anchor, *_ = f"{path}#".split("#")
    path = _resolve(files.get_file_from_path(path), page)
    return "#".join([path, anchor]) if anchor else path

# Resolve path of file relative to given page - the posixpath always includes
# one additional level of `..` which we need to remove
def _resolve(file: File, page: Page):
    # if file is None or page.file is None:
    #     return '/'
    path = posixpath.relpath(file.src_uri, page.file.src_uri)
    return posixpath.sep.join(path.split(posixpath.sep)[1:])

# -----------------------------------------------------------------------------

# Create badge
def _badge(icon: str, text: str = "", type: str = ""):
    classes = f"mdx-badge mdx-badge--{type}" if type else "mdx-badge"
    return "".join([
        f"<span class=\"{classes}\">",
        *([f"<span class=\"mdx-badge__icon\">{icon}</span>"] if icon else []),
        *([f"<span class=\"mdx-badge__text\">{text}</span>"] if text else []),
        f"</span>",
    ])

# Create badge for version
def _badge_for_version(text: str, page: Page, files: Files):
    spec = text
    path = f"development/changelog.md#{spec}"

    # Return badge
    icon = "material-tag-outline"
    return _badge(
        icon = f"[:{icon}:]('Minimum version')",
        text = f"[{text}]({_resolve_path(path, page, files)})" if spec else ""
    )

# Create badge for feature
def _badge_for_feature(text: str, page: Page, files: Files):
    icon = "material-toggle-switch"
    return _badge(
        icon = f"[:{icon}:]('Optional feature')",
        text = text
    )

# Create badge for default value
def _badge_for_default(text: str, page: Page, files: Files):
    icon = "material-water"
    return _badge(
        icon = f"[:{icon}:]('Default value')",
        text = text
    )

# Create badge for empty default value
def _badge_for_default_none(page: Page, files: Files):
    icon = "material-water-outline"
    return _badge(
        icon = f"[:{icon}:]('Default value is empty')"
    )

# Create badge for required value flag
def _badge_for_required(page: Page, files: Files):
    icon = "material-alert"
    return _badge(
        icon = f"[:{icon}:]('Required value')"
    )

# Create badge for customization flag
def _badge_for_customization(page: Page, files: Files):
    icon = "material-brush-variant"
    return _badge(
        icon = f"[:{icon}:]('Customization')"
    )

# Create badge for experimental flag
def _badge_for_experimental(page: Page, files: Files):
    icon = "material-flask-outline"
    return _badge(
        icon = f"[:{icon}:]('Experimental')"
    )

# Create badge for overwritable
def _badge_for_overwritable(text: str, page: Page, files: Files) -> str:
    icon = 'material-file-replace-outline'
    return _badge(
        icon=f"[:{icon}:]('Overwritable')",
        text=text,
    )
