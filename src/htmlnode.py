class HTMLNode():
    def __init__(self, tag=None, value=None, children=None, props=None):
        self.tag = tag
        self.value = value
        self.children = children
        self.props = props

    def to_html(self):
        raise NotImplementedError("Method 'to_html' is not implemented for class 'HTMLNode'.")
    
    def props_to_html(self):
        if not self.props:
             return ""
        props = ""
        for k, v in self.props.items():
            props += f' {k}="{v}"'
        return props

    def __repr__(self):
            return f"""HTMLNODE(
            tag: {self.tag},
            value: {self.value},
            children: {self.children},
            props: {self.props}
)"""