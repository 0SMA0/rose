from tree_sitter import Parser, Language
import tree_sitter_java as ts_java

# ****** CONSTANTS ****** #

CONTAINER_TYPES = {
    'class_declaration': 'class',
    'enum_declaration': 'enum',
    'interface_declaration': 'interface'
}

KNOWN_THIRD_PARTY_PREFIXES = (
    'org.apache',
    'org.springframework',
    'org.hibernate',
    'com.google',
    'com.fasterxml',
    'io.netty',
    'org.slf4j',
    'ch.qos',
    'org.junit',
    'org.mockito',
)

JAVA_DEPRECATED = {
    "raw_JDBC": ["DriverManager.getConnection", "java.sql.Connection", "java.sql.Statement", "java.sql.DriverManager"],
    "deprecated_date_api": ["java.util.Date", "java.util.Calendar", "new Date()"],
    "old_collections": ["java.util.Vector", "java.util.Hashtable", "java.util.Stack"],
    "thread_unsafe": ["StringBuffer", "synchronized(this)"]
}

FRAMEWORK_PATTERNS = {
    "ejb_annotations": ["@Stateless", "@Stateful", "@MessageDriven", "javax.ejb"],
    "legacy_web_framework": ["org.apache.struts", "javax.servlet.http.HttpServlet"],
    "spring_legacy": ["@Autowired on field"],
    "hibernate_legacy": ["session.createSQLQuery", "HibernateUtil"]
}

# ****** CONSTANTS END ****** #


class JavaParser:
    def __init__(self, source: bytes):
        _parser = Parser(Language(ts_java.language()))
        self.source = source
        self.tree = _parser.parse(source)
        self.root_node = self.tree.root_node

    def _text(self, node):
        return self.source[node.start_byte : node.end_byte].decode('utf-8')

    # ****** TREE DEBUG ****** #

    def print_tree(self, node=None, indent=0):
        if node is None:
            node = self.root_node
        print(" " * indent + f"({node.type})")
        for child in node.children:
            self.print_tree(child, indent + 1)

    # ****** METHOD ****** #

    def find_all_methods_nodes(self, node):
        methods = []
        if node.type == 'method_declaration':
            methods.append(node)
        for child in node.children:
            methods.extend(self.find_all_methods_nodes(child))
        return methods

    def extract_modifiers(self, node):  # used by both methods and fields
        modifier_node = node.child_by_field_name('modifiers')
        if modifier_node:
            return self._text(modifier_node)

    def extract_return_type(self, node):  # used by both methods and fields
        rt_node = node.child_by_field_name('type')
        if rt_node:
            return self._text(rt_node)

    def extract_method_name(self, method_node):
        name_node = method_node.child_by_field_name('name')
        if name_node:
            return self._text(name_node)

    def extract_method_parameters(self, method_node):
        parameters_node = method_node.child_by_field_name('parameters')
        if parameters_node:
            return self._text(parameters_node)

    def extract_method_logic(self, method_node):
        body_node = method_node.child_by_field_name('body')
        if body_node:
            return self._text(body_node)
        return None

    # ****** FIELD ****** #

    def find_all_field_nodes(self, node):
        fields = []
        if node.type == 'field_declaration':
            fields.append(node)
        for child in node.children:
            fields.extend(self.find_all_field_nodes(child))
        return fields

    def extract_field_name(self, field_node):
        var_dec = field_node.child_by_field_name('declarator')
        if var_dec:
            name_node = var_dec.child_by_field_name('name')
            if name_node:
                return self._text(name_node)
        return None

    def extract_field_value(self, field_node):
        var_declarator = field_node.child_by_field_name('declarator')
        if var_declarator:
            for i, child in enumerate(var_declarator.children):
                if child.type == '=' and i + 1 < len(var_declarator.children):
                    value_node = var_declarator.children[i + 1]
                    return self._text(value_node)
        return None

    # ****** CLASS ****** #

    def find_all_containers(self, node):
        containers = []
        if node.type in CONTAINER_TYPES:
            containers.append(node)
            return containers  # stop here — skip nested classes (Phase 2)
        for child in node.children:
            containers.extend(self.find_all_containers(child))
        return containers

    def extract_class_name(self, container_node):
        name_node = container_node.child_by_field_name('name')
        if name_node:
            return self._text(name_node)
        return None

    def extract_superclass(self, class_node):
        superclass_node = class_node.child_by_field_name('superclass')
        if superclass_node:
            return self._text(superclass_node).replace('extends ', '').strip()
        return None

    def extract_interfaces(self, class_node):
        interfaces_node = class_node.child_by_field_name('interfaces')
        if interfaces_node:
            text = self._text(interfaces_node).replace('implements ', '').strip()
            return [i.strip() for i in text.split(',')]
        return []

    def extract_nested_containers(self, container_node):
        nested = []
        body_node = container_node.child_by_field_name('body')
        if body_node:
            for child in body_node.children:
                if child.type in CONTAINER_TYPES:
                    name_node = child.child_by_field_name('name')
                    if name_node:
                        nested.append(self._text(name_node))
        return nested

    # ****** IMPORTS ****** #

    def extract_imports(self, internal_package_prefix=None):
        imports = []
        for child in self.root_node.children:
            if child.type == 'import_declaration':
                statement = self._text(child).strip()
                imports.append({
                    'statement': statement,
                    'category': categorize_import(statement, internal_package_prefix)
                })
        return imports

    # ****** LEGACY PATTERNS ****** #

    def detect_legacy_patterns(self, field_nodes, method_nodes, imports=None, client_config=None):
        detected = []
        all_text = ""
        for field in field_nodes:
            value = self.extract_field_value(field)
            if value:
                all_text += value
        for method in method_nodes:
            body = self.extract_method_logic(method)
            if body:
                all_text += body
        if imports:
            for imp in imports:
                all_text += imp['statement']

        all_patterns = {**JAVA_DEPRECATED, **FRAMEWORK_PATTERNS}
        if client_config:
            all_patterns.update(client_config.get("client_legacy_patterns", {}))

        for pattern_name, keywords in all_patterns.items():
            for keyword in keywords:
                if keyword in all_text:
                    detected.append(pattern_name)
                    break

        return detected


# ****** MODULE-LEVEL HELPERS (no source dependency) ****** #

def categorize_import(statement, internal_package_prefix=None):
    path = statement.replace('import ', '').replace(';', '').strip()
    if path.startswith(('java.', 'javax.')):
        return 'standard_java'
    if path.startswith(KNOWN_THIRD_PARTY_PREFIXES):
        return 'third_party'
    if internal_package_prefix and path.startswith(internal_package_prefix):
        return 'internal'
    return 'third_party'

def main():
    pass

if __name__ == '__main__':
    main()