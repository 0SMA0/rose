public class Test {

    /*
     * Parser output:
     *
     * [{'class': 'Test', 'type': 'class', 'source_path': 'Test.java',
     * 'scrubbed_path': None, 'superclass': None, 'interfaces': [],
     * 'nested_classes': [], 'methods': [{'name': 'getId', 'return_type': 'int',
     * 'modifiers': None, 'parameters': '()', 'body': '{\n return id;\n }'},
     * {'name': 'getName', 'return_type': 'String', 'modifiers': None, 'parameters':
     * '()', 'body': '{\n return name;\n }'}, {'name': 'increaseId', 'return_type':
     * 'void', 'modifiers': None, 'parameters': '(int increment)', 'body': '{\n for
     * (int i = 0; i < increment; i++) {\n this.id++;\n }\n }'}, {'name': 'main',
     * 'return_type': 'void', 'modifiers': None, 'parameters': '(String[] args)',
     * 'body': '{\n System.out.println("Hello, World!");\n }'}], 'fields': [{'name':
     * 'id', 'type': 'int', 'modifiers': None, 'value': None}, {'name': 'name',
     * 'type': 'String', 'modifiers': None, 'value': None}], 'imports': [],
     * 'legacy_patterns': [], 'coupling_score': 0.0, 'refactor_risk': 'LOW',
     * 'business_domain': None}]
     */
    private int id;
    private String name;

    public Test(int id, String name) {
        this.id = id;
        this.name = name;
    }

    public int getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public void increaseId(int increment) {
        for (int i = 0; i < increment; i++) {
            this.id++;
        }
    }

    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}