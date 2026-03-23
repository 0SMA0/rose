from tree_sitter import Parser, Language
import tree_sitter_java as ts_java

# Set up parser
parser = Parser(Language(ts_java.language()))

# Code must be in bytes

code = b"""
import java.sql.DriverManager;
import org.springframework.stereotype.Service;
import com.example.internal.LegacyHelper;

public class car extends Vehicle implements Runnable, Serializable {
private int s;
public final static String car = 'car';
private int t = 1;

private void greet(String name) {
    System.out.println("Hello");
}
public static int add(int a, int b) {
    return a + b;
}
}
"""

# parse the code into a tree 
tree = parser.parse(code)
root_node = tree.root_node

# print(f"Root tyoe: {root_node.type}") #Output: program

# Manual Transversal (this is used instead of s_experssion/sexxp)
def print_tree(node, indent = 0):
    print(" " * indent + f"({node.type})")
    for child in node.children:
        print_tree(child, indent + 1)
    
# Call the tree printer
# print_tree(root_node) #<--- shows the hierarchical structure

# Recursive func to find all method nodes
def find_all_methods_nodes(node):
    methods = []
    if node.type == 'method_declaration':
        methods.append(node)
    for child in node.children:
        methods.extend(find_all_methods_nodes(child))
    
    
    return methods



# ****** METHOD START ****** # 
def find_method_name(method_nodes):
    names = []
    if method_nodes:
        print(f"\nFound {len(method_nodes)} methods(s):")
        for method_node in method_nodes:
            print(extract_return_type(method_node))
            names.append(extract_method_name(method_node))
    return names

# TO GET METHOD SIGNATURE, USE NEEDED EXTRACTS  
def extract_modifiers(node): # <-- used by both methods and fields
    modifer_node = node.child_by_field_name('modifiers')
    if modifer_node:
        modifer_text = code[modifer_node.start_byte : modifer_node.end_byte].decode('utf-8')
        return modifer_text #contains static and other modifiers

def extract_return_type(node): # <-- used by both methods and fields
    rt_node = node.child_by_field_name('type')
    if rt_node:
        rt_text = code[rt_node.start_byte : rt_node.end_byte].decode('utf-8')
        return rt_text

def extract_method_name(method_node):
    name_node = method_node.child_by_field_name('name')
    if name_node:
        name_text = code[name_node.start_byte : name_node.end_byte].decode('utf-8')
        return name_text
    
def extract_method_parameters(method_node):
    parameters_node = method_node.child_by_field_name('parameters')
    if parameters_node:
        params_text = code[parameters_node.start_byte : parameters_node.end_byte].decode('utf-8')
        return params_text

# CONTAINS \n (need to traverse it to get a more structured body)
def extract_method_logic(method_node):
    body_node = method_node.child_by_field_name('body')
    if body_node:
        return code[body_node.start_byte : body_node.end_byte].decode('utf-8')
    return None

# method_nodes = find_all_methods_nodes(root_node)
# find_method_name(method_nodes)

# ****** METHOD END ****** # 


# ****** FIELD START ****** #
    #NOTE To get modifiers and return type, use functions in Method area 

def find_all_field_nodes(node):
    fields = []
    if node.type == 'field_declaration':
        fields.append(node)
    for child in node.children:
        fields.extend(find_all_field_nodes(child))
    return fields

def find_field_names(field_nodes):
    names = []
    if field_nodes:
        print(f"\nFound {len(field_nodes)} field(s):")
        for field_node in field_nodes:
            print(extract_field_value(field_node))
            names.append(extract_field_name(field_node))
    return names

def extract_field_name(field_node):
    var_dec= field_node.child_by_field_name('declarator')
    if var_dec:
        name_node = var_dec.child_by_field_name('name')
        if name_node:
            name_text = code[name_node.start_byte : name_node.end_byte].decode('utf-8')
            return name_text
    return None
    
def extract_field_value(field_node):
    var_declarator = field_node.child_by_field_name('declarator')
    if var_declarator:
        for i, child in enumerate(var_declarator.children):
            if child.type == '=' and i + 1 < len(var_declarator.children):
                value_node = var_declarator.children[i + 1]
                text = code[value_node.start_byte : value_node.end_byte].decode('utf-8')
                return text
    return None

# ****** FIELD END ****** #
# field_nodes = find_all_field_nodes(root_node)
# find_field_names(field_nodes)

# ****** CLASS START ****** #

CONTAINER_TYPES = {
    'class_declaration': 'class',
    'enum_declaration': 'enum',
    'interface_declaration': 'interface'
}

def find_all_containers(node):
    containers = []
    if node.type in CONTAINER_TYPES:
        containers.append(node)
        return containers  # stop here — skip nested classes (Phase 2)
    for child in node.children:
        containers.extend(find_all_containers(child))
    return containers

def extract_class_name(container_node):
    name_node = container_node.child_by_field_name('name')
    if name_node:
        return code[name_node.start_byte : name_node.end_byte].decode('utf-8')
    return None

def extract_superclass(class_node):
    superclass_node = class_node.child_by_field_name('superclass')
    if superclass_node:
        text = code[superclass_node.start_byte : superclass_node.end_byte].decode('utf-8')
        return text.replace('extends ', '').strip()
    return None

def extract_interfaces(class_node):
    interfaces_node = class_node.child_by_field_name('interfaces')
    if interfaces_node:
        text = code[interfaces_node.start_byte : interfaces_node.end_byte].decode('utf-8')
        text = text.replace('implements ', '').strip()
        return [i.strip() for i in text.split(',')]
    return []

# ****** CLASS END ****** #


# ****** IMPORTS START ****** #

def categorize_import(statement):
    path = statement.replace('import ', '').replace(';', '').strip()
    if path.startswith(('java.', 'javax.')):
        return 'standard_java'
    return 'third_party'

def extract_imports(root_node):
    imports = []
    for child in root_node.children:
        if child.type == 'import_declaration':
            statement = code[child.start_byte : child.end_byte].decode('utf-8').strip()
            imports.append({
                'statement': statement,
                'category': categorize_import(statement)
            })
    return imports

# ****** IMPORTS END ****** #

# print(extract_imports(root_node))

