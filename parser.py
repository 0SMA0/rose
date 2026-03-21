from tree_sitter import Parser, Language
import tree_sitter_java as ts_java

# Set up parser
parser = Parser(Language(ts_java.language()))

# Code must be in bytes

code = b"""
private void greet(String name) {
    System.out.println("Hello");
}
public static int add(int a, int b) {
    return a + b;
}
"""

# parse the code into a tree 
tree = parser.parse(code)
root_node = tree.root_node

print(f"Root tyoe: {root_node.type}") #Output: program

# Manual Transversal (this is used instead of s_experssion/sexxp)
def print_tree(node, indent = 0):
    print(" " * indent + f"({node.type})")
    for child in node.children:
        print_tree(child, indent + 1)
    
# Call the tree printer
print_tree(root_node) #<--- shows the hierarchical structure

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
            print(extract_method_modifiers(method_node))
            names.append(extract_method_name(method_node))
    return names

# TO GET METHOD SIGNATURE, USE NEEDED EXTRACTS 
def extract_method_modifiers(method_node):
    modifer_node = method_node.child_by_field_name('modifiers')
    if modifer_node:
        modifer_text = code[modifer_node.start_byte : modifer_node.end_byte].decode('utf-8')
        return modifer_text #contains static and other modifiers

def extract_return_type(method_node):
    rt_node = method_node.child_by_field_name('type')
    if rt_node:
        rt_text = code[rt_node.start_byte : rt_node.end_byte].decode('utf-8')
        return rt_text

def extract_method_name(method_node):
    name_node = method_node.child_by_field_name('name')
    if name_node:
        name_text = code[name_node.start_byte : name_node.end_byte].decode('utf-8')
        return name_text
    
def extract_parameters(method_node):
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

# ****** METHOD END ****** # 

method_nodes = find_all_methods_nodes(root_node)
find_method_name(method_nodes)