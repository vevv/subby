from __future__ import annotations

import lxml.etree


def load_xml(data: str | bytes) -> lxml.etree._ElementTree:
    # lxml only accepts non-ascii as bytes
    if isinstance(data, str):
        data = data.encode()

    tree = lxml.etree.fromstring(data, lxml.etree.XMLParser(recover=True))
    if tree is None:
        raise lxml.etree.XMLSyntaxError('Could not parse XML document', 0, 1, 1)

    # Strip namespace URIs and prefixes for easier parsing
    # str.split is faster than lxml.etree.QName(tag).localname
    for element in tree.iter():
        tag = element.tag
        if isinstance(tag, str) and '}' in tag:
            element.tag = tag.split('}', 1)[1]

        attrib = element.attrib
        if not attrib:
            continue
        new_attrib = {
            (key.split('}', 1)[1] if '}' in key else key.rsplit(':', 1)[-1]): val
            for key, val in attrib.items()
        }
        attrib.clear()
        attrib.update(new_attrib)

    return tree

