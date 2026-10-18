"""Build Studio-insertable .rbxmx model files from src/.

Usage: python3 build_rbxmx.py   ->  writes dist/*.rbxmx
In Studio: right-click the target service > Insert from File... > pick the file.
"""

import itertools
import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "dist")

_ref = itertools.count()


def cdata(text):
    return "<![CDATA[" + text.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def item(cls, name, source=None, children=(), indent=1):
    pad = "\t" * indent
    lines = [f'{pad}<Item class="{cls}" referent="RBX{next(_ref)}">', f"{pad}\t<Properties>"]
    lines.append(f'{pad}\t\t<string name="Name">{escape(name)}</string>')
    if source is not None:
        lines.append(f'{pad}\t\t<ProtectedString name="Source">{cdata(source)}</ProtectedString>')
    lines.append(f"{pad}\t</Properties>")
    for child in children:
        lines.append(child(indent + 1))
    lines.append(f"{pad}</Item>")
    return "\n".join(lines)


def script_node(path):
    filename = os.path.basename(path)
    with open(path, encoding="utf-8") as f:
        source = f.read()
    if filename.endswith(".server.lua"):
        cls, name = "Script", filename[: -len(".server.lua")]
    elif filename.endswith(".client.lua"):
        cls, name = "LocalScript", filename[: -len(".client.lua")]
    else:
        cls, name = "ModuleScript", filename[: -len(".lua")]
    return lambda indent: item(cls, name, source, (), indent)


def folder_node(path):
    children = [node_for(os.path.join(path, n)) for n in sorted(os.listdir(path))]
    return lambda indent: item("Folder", os.path.basename(path), None, children, indent)


def node_for(path):
    return folder_node(path) if os.path.isdir(path) else script_node(path)


def write_model(filename, roots):
    body = "\n".join(root(1) for root in roots)
    xml = (
        '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
        f"{body}\n</roblox>\n"
    )
    out = os.path.join(DIST, filename)
    with open(out, "w", encoding="utf-8") as f:
        f.write(xml)
    print("wrote", os.path.relpath(out, ROOT))


def main():
    os.makedirs(DIST, exist_ok=True)
    write_model(
        "1_ReplicatedStorage.rbxmx",
        [node_for(os.path.join(SRC, "ReplicatedStorage", "Combat"))],
    )
    write_model(
        "2_ServerScriptService.rbxmx",
        [node_for(os.path.join(SRC, "ServerScriptService", "Combat"))],
    )
    write_model(
        "3_StarterPlayerScripts.rbxmx",
        [node_for(os.path.join(SRC, "StarterPlayerScripts", "CombatClient.client.lua"))],
    )


if __name__ == "__main__":
    main()
