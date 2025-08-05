from textnode import *
from htmlnode import *
from leafnode import *
from parentnode import *
import re
import os
import shutil
from enum import Enum

def text_node_to_html_node(text_node: TextNode):
    match text_node.text_type:
        case TextType.TEXT:
            return (
                LeafNode(None, text_node.text)
            )
        case TextType.BOLD:
            return (
                LeafNode("b", text_node.text)
            )
        case TextType.ITALIC:
            return (
                LeafNode("i", text_node.text)
            )
        case TextType.CODE:
            return (
                LeafNode("code", text_node.text)
            )
        case TextType.LINK:
            return (
                LeafNode("a", text_node.text, {"href": text_node.url})
            )
        case TextType.IMAGE:
            return (
                LeafNode("img", "", {"src": text_node.url, "alt": text_node.text})
            )    
        case _:
            raise Exception("Invalid TextType")
        
def split_nodes_delimiter(old_nodes, delimiter, text_type):
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        split_nodes = []
        tmp = node.text.split(delimiter)
        if len(tmp) % 2 == 0:
            raise Exception(f"No matching delimiter ({delimiter}) found. Invalid markdown.")
        for i in range(0, len(tmp)):
            if tmp[i] == "":
                continue
            if i % 2 == 0:
                split_nodes.append(TextNode(tmp[i], TextType.TEXT))
            else:
                split_nodes.append(TextNode(tmp[i], text_type))
        new_nodes.extend(split_nodes)
    return new_nodes

def extract_markdown_images(text):
    matches = re.findall(r"!\[([^\[\]]*)\]\(([^\(\)]*)\)", text)
    return matches

def extract_markdown_links(text):
    matches = re.findall(r"(?<!!)\[([^\[\]]*)\]\(([^\(\)]*)\)", text)
    return matches

def split_nodes_image(old_nodes):
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        node_text = node.text
        imgs = extract_markdown_images(node_text)
        if not imgs:
            new_nodes.append(node)
            continue
        for img in imgs:
            tmp = node_text.split(f"![{img[0]}]({img[1]})", 1)
            if len(tmp) != 2:
                raise ValueError("Issue with image section. Invalid markdown")
            if tmp[0]:
                new_nodes.append(TextNode(tmp[0], TextType.TEXT))
            new_nodes.append(TextNode(img[0], TextType.IMAGE, img[1]))
            node_text = tmp[1]
        if node_text:
            new_nodes.append(TextNode(node_text, TextType.TEXT))
    return new_nodes

def split_nodes_link(old_nodes):
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        node_text = node.text
        links = extract_markdown_links(node_text)
        if not links:
            new_nodes.append(node)
            continue
        for link in links:
            tmp = node_text.split(f"[{link[0]}]({link[1]})", 1)
            if len(tmp) != 2:
                raise ValueError("Issue with link section. Invalid markdown")
            if tmp[0]:
                new_nodes.append(TextNode(tmp[0], TextType.TEXT))
            new_nodes.append(TextNode(link[0], TextType.LINK, link[1]))
            node_text = tmp[1]
        if node_text:
            new_nodes.append(TextNode(node_text, TextType.TEXT))
    return new_nodes

def text_to_textnodes(text):
    nodes = [TextNode(text, TextType.TEXT)]
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    return nodes

def markdown_to_blocks(markdown):
    return [line.strip() for line in markdown.split("\n\n") if line]

class BlockType(Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    CODE = "code"
    QUOTE = "quote"
    UNORDERED_LIST = "unordered_list"
    ORDERED_LIST = "ordered_list"

def block_to_block_type(markdown):
    # Check if the beginning of the block begins with 1 - 6 #'s followed by a space.
    # I used re.match() here becuase I wasn't aware you could give str.startswith() multiple arguments...
    if re.match(r"(#{1,6} )", markdown) :
        return BlockType.HEADING
    elif markdown.startswith("```") and markdown.endswith("```"):
        return BlockType.CODE
    else:
        lines = markdown.split("\n")
        quote = True
        unordered_list = True
        ordered_list = True
        for i in range(0, len(lines)):
            if quote or unordered_list or ordered_list:
                if not lines[i].startswith(">"):
                    quote = False
                if not lines[i].startswith("- "):
                    unordered_list = False
                if not lines[i].startswith(f"{i + 1}. "):
                    ordered_list = False
        if quote:
            return BlockType.QUOTE
        elif unordered_list:
            return BlockType.UNORDERED_LIST
        elif ordered_list:
            return BlockType.ORDERED_LIST
        else:
            return BlockType.PARAGRAPH
        
def get_children_from_text(text):
    nodes = text_to_textnodes(text)
    children = []
    for node in nodes:
        html_node = text_node_to_html_node(node)
        children.append(html_node)
    return children

def paragraph_html(block):
    lines = block.split("\n")
    text = " ".join(lines)
    children = get_children_from_text(text)
    return ParentNode("p", children)

def heading_html(block):
    parts = block.split(maxsplit=1)
    num_h = len(parts[0])
    if num_h >= len(block):
        raise ValueError(f"Heading level {num_h} invalid")
    text = parts[1]
    children = get_children_from_text(text)
    return ParentNode(f"h{num_h}", children)

def code_html(block):
    if not block.startswith("```") or not block.endswith("```"):
        raise ValueError("Code block invalid")
    text = block[4:-3]
    node = TextNode(text, TextType.TEXT)
    child = text_node_to_html_node(node)
    code = ParentNode("code", [child])
    return ParentNode("pre", [code])

def quote_html(block):
    lines = block.split("\n")
    new_lines = []
    for line in lines:
        if not line.startswith(">"):
            raise ValueError("Quote block invalid")
        new_lines.append(line[1:].strip())
    quote = " ".join(new_lines)
    children = get_children_from_text(quote)
    return ParentNode("blockquote", children)

def ulist_html(block):
    list_items = block.split("\n")
    html = []
    for item in list_items:
        item_text = item[2:]
        children = get_children_from_text(item_text)
        html.append(ParentNode("li", children))
    return ParentNode("ul", html)

def olist_html(block):
    list_items = block.split("\n")
    html = []
    for item in list_items:
        item_text = item[3:]
        children = get_children_from_text(item_text)
        html.append(ParentNode("li", children))
    return ParentNode("ol", html)

def block_to_html(block):
    block_type = block_to_block_type(block)
    match block_type:
        case BlockType.PARAGRAPH:
            return paragraph_html(block)
        case BlockType.HEADING:
            return heading_html(block)
        case BlockType.CODE:
            return code_html(block)
        case BlockType.QUOTE:
            return quote_html(block)
        case BlockType.UNORDERED_LIST:
            return ulist_html(block)
        case BlockType.ORDERED_LIST:
            return olist_html(block)
        case _:
            raise Exception("Invalid block type")
            
def markdown_to_html(markdown):
    children = []
    blocks = markdown_to_blocks(markdown)
    for block in blocks:
        html_node = block_to_html(block)
        children.append(html_node)
    return ParentNode("div", children, None)

def rcopy(fpath_src, fpath_dst):
    abs_src = os.path.abspath(fpath_src)
    abs_dst = os.path.abspath(fpath_dst)
    if not os.path.exists(abs_dst):
        os.mkdir(abs_dst)
    for filename in os.listdir(abs_src):
        new_src = os.path.abspath(os.path.join(abs_src, filename))
        new_dst = os.path.abspath(os.path.join(abs_dst, filename))
        if os.path.isfile(new_src):
            shutil.copy(new_src, new_dst)
        else:
            rcopy(new_src, new_dst)

def extract_title(markdown):
    if not markdown.startswith("# "):
        raise Exception("No header found. Invalid markdown.")
    else:
        header = markdown.split("\n")[0][2:]
        return header
    
def generate_page(from_path, template_path, dest_path):
    print(f"Generating page from {from_path} to {dest_path} using {template_path}...\n")
    with open(from_path, "r") as f:
        markdown = f.read()
    with open(template_path, "r") as f:
        template = f.read()
    html = markdown_to_html(markdown).to_html()
    title = extract_title(markdown)
    template = template.replace(r"{{ Title }}", title).replace(r"{{ Content }}", html)
    dest_dir = os.path.dirname(dest_path)
    if dest_dir != "":
        os.makedirs(dest_dir, exist_ok=True)
    with open(dest_path, "w") as f:
        f.write(template)

def r_generate_page(from_dir, template_path, dest_dir):
    abs_src = os.path.abspath(from_dir)
    abs_dst = os.path.abspath(dest_dir)
    if not os.path.exists(abs_dst):
        os.mkdir(abs_dst)
    for filename in os.listdir(abs_src):
        new_src = os.path.abspath(os.path.join(abs_src, filename))
        new_dst = os.path.abspath(os.path.join(abs_dst, filename))
        if os.path.isfile(new_src):
            generate_page(new_src, template_path, new_dst.replace("md", "html"))
        else:
            r_generate_page(new_src, template_path, new_dst)