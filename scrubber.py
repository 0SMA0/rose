import os
import json
import re


# ****** TOKEN CATEGORIES ****** #

CATEGORY_CLASS      = "CLASS"
CATEGORY_CREDENTIAL = "CREDENTIAL"
CATEGORY_PII_EMAIL  = "PII_EMAIL"
CATEGORY_PII_PHONE  = "PII_PHONE"
CATEGORY_PII_SSN    = "PII_SSN"
CATEGORY_PII_NAME   = "PII_NAME"

# ****** TOKEN CATEGORIES END ****** #


# ****** CREDENTIAL CONSTANTS ****** #

# Field names that suggest the value is a credential
CREDENTIAL_FIELD_HINTS = (
    'password', 'passwd', 'pwd', 'secret', 'apikey', 'api_key',
    'token', 'credential', 'auth', 'key', 'connectionstring', 'connstr'
)

# Regex patterns for credentials the parser may not have extracted as field values
CREDENTIAL_PATTERNS = [
    re.compile(r'jdbc:[a-zA-Z0-9]+://[^\s"\'>;]+'),           # JDBC URLs
    re.compile(r'mongodb://[^\s"\']+'),                        # MongoDB URLs
    re.compile(r'postgres://[^\s"\']+'),                       # Postgres URLs
    re.compile(r'mysql://[^\s"\']+'),                          # MySQL URLs
    re.compile(r'AKIA[0-9A-Z]{16}'),                           # AWS access keys
    re.compile(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'),  # JWT tokens
    re.compile(r'(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*'),        # Bearer tokens
    re.compile(r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'),  # IP addresses
    re.compile(r',\s*"([a-zA-Z][a-zA-Z0-9_\-]*[0-9][a-zA-Z0-9_\-]*)"'),  # password-like string args after a comma
]

# ****** CREDENTIAL CONSTANTS END ****** #


class Scrubber:
    def __init__(self, source: str, knowledge_graph: dict, client_config=None):
        self.source = source
        self.knowledge_graph = knowledge_graph
        self.client_config = client_config or {}
        self.token_map = {}         # token → real value (saved to disk, used by Pass 2)
        self._value_to_token = {}   # real value → token (dedup — same value, same token)
        self._counters = {}         # category → current count

    def _generate_token(self, category: str, value: str) -> str:
        if value in self._value_to_token:
            return self._value_to_token[value]
        count = self._counters.get(category, 0) + 1
        self._counters[category] = count
        token = f"{category}_TOKEN_{count:03d}"
        self.token_map[token] = value
        self._value_to_token[value] = token
        return token

    # ****** FEATURE 2 — CREDENTIAL SCRUBBING ****** #

    def scrub_credentials(self):
        # Pass 1 — KG field values with credential-like names (primary signal)
        for field in self.knowledge_graph.get('fields', []):
            name = (field.get('name') or '').lower()
            value = field.get('value')
            if value and any(hint in name for hint in CREDENTIAL_FIELD_HINTS):
                clean_value = value.strip('"\'')
                if clean_value:
                    token = self._generate_token(CATEGORY_CREDENTIAL, clean_value)
                    self.source = self.source.replace(clean_value, token)

        # Pass 2 — regex scan for anything the parser missed
        all_patterns = list(CREDENTIAL_PATTERNS)
        for pattern in self.client_config.get('credential_patterns', []):
            all_patterns.append(re.compile(pattern))

        for pattern in all_patterns:
            for match in pattern.finditer(self.source):
                # Use group(1) if a capture group exists — replaces only the value, not surrounding context
                value = match.group(1) if match.lastindex else match.group(0)
                token = self._generate_token(CATEGORY_CREDENTIAL, value)
                self.source = self.source.replace(value, token)

        return self

    # ****** FEATURE 3 — PII SCRUBBING ****** #

    def scrub_pii(self):
        # Email addresses
        email_pattern = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
        for match in email_pattern.finditer(self.source):
            value = match.group(0)
            token = self._generate_token(CATEGORY_PII_EMAIL, value)
            self.source = self.source.replace(value, token)

        # Phone numbers — US formats: (555) 555-5555, 555-555-5555, +15555555555
        phone_pattern = re.compile(r'(\+1[\s\-]?)?\(?\d{3}\)?[\s\-]\d{3}[\s\-]\d{4}')
        for match in phone_pattern.finditer(self.source):
            value = match.group(0)
            token = self._generate_token(CATEGORY_PII_PHONE, value)
            self.source = self.source.replace(value, token)

        # SSN — 000-00-0000
        ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
        for match in ssn_pattern.finditer(self.source):
            value = match.group(0)
            token = self._generate_token(CATEGORY_PII_SSN, value)
            self.source = self.source.replace(value, token)

        return self

    # ****** FEATURE 4 — CLASS NAME TOKENIZATION ****** #

    def scrub_class_names(self):
        class_name = self.knowledge_graph.get('class')
        if not class_name:
            return self

        token = self._generate_token(CATEGORY_CLASS, class_name)
        self.source = re.sub(
            rf'\b{re.escape(class_name)}\b',
            token,
            self.source
        )

        return self

    # ****** FEATURE 5 — CLIENT CONFIG INTEGRATION ****** #

    def scrub_client_specific(self):
        # Company name aliases — e.g. ["Goldman", "GS", "Sachs"]
        for alias in self.client_config.get('company_names', []):
            if alias and alias in self.source:
                token = self._generate_token(CATEGORY_CLASS, alias)
                self.source = re.sub(rf'\b{re.escape(alias)}\b', token, self.source)

        # Internal system names — e.g. ["LegacyServiceLocator", "OldAuthHelper"]
        for name in self.client_config.get('internal_system_names', []):
            if name and name in self.source:
                token = self._generate_token(CATEGORY_CLASS, name)
                self.source = re.sub(rf'\b{re.escape(name)}\b', token, self.source)

        return self

    # ****** FEATURE 6 — FORWARD PASS ****** #

    def _strip_comments(self):
        # Strip block comments /* ... */ and /** ... */
        self.source = re.sub(r'/\*[\s\S]*?\*/', '', self.source)
        # Strip single-line comments // ... — negative lookbehind avoids matching :// in URLs
        self.source = re.sub(r'(?<!:)//[^\n]*', '', self.source)
        return self

    def scrub(self) -> str:
        self._strip_comments()
        self.scrub_credentials()
        self.scrub_pii()
        self.scrub_class_names()
        self.scrub_client_specific()
        return self.source

    # ****** FEATURE 7 — REVERSE PASS ****** #

    def restore(self, modernized_source: str) -> str:
        # Sort tokens by number descending — avoids partial replacement collisions
        sorted_tokens = sorted(
            self.token_map.keys(),
            key=lambda t: int(t.split('_TOKEN_')[-1]),
            reverse=True
        )
        for token in sorted_tokens:
            modernized_source = modernized_source.replace(token, self.token_map[token])
        return modernized_source

    # ****** FEATURE 8 — TOKEN MAP PERSISTENCE ****** #

    def save_token_map(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.token_map, f, indent=2)

    @classmethod
    def load_token_map(cls, filepath: str) -> dict:
        with open(filepath, 'r') as f:
            return json.load(f)

    # ****** FEATURE 9 — SCRUB REPORT ****** #

    def scrub_report(self) -> dict:
        counts = {}
        sources = {}

        for token, value in self.token_map.items():
            category = token.split('_TOKEN_')[0]
            counts[category] = counts.get(category, 0) + 1

            # Determine whether detection came from KG or regex
            kg_values = {
                f.get('value', '').strip('"\'')
                for f in self.knowledge_graph.get('fields', [])
                if f.get('value')
            }
            kg_values.add(self.knowledge_graph.get('class', ''))

            origin = 'knowledge_graph' if value in kg_values else 'regex'
            sources.setdefault(category, {}).setdefault(origin, 0)
            sources[category][origin] += 1

        return {
            "class": self.knowledge_graph.get('class'),
            "total_replacements": len(self.token_map),
            "by_category": counts,
            "by_origin": sources,
        }


def main():
    import json
    from parser import parse_file

    # Parse the test file to get the Knowledge Graph node
    kg = parse_file('GoldmanSachsPaymentProcessor.java')[0]

    # Load raw source
    with open('GoldmanSachsPaymentProcessor.java', 'r') as f:
        source = f.read()

    client_config = {
        'company_names': ['Goldman', 'GS', 'Sachs'],
        'internal_system_names': [],
        'credential_patterns': [],
    }

    s = Scrubber(source, kg, client_config)
    scrubbed = s.scrub()

    print("===== SCRUBBED SOURCE =====")
    print(scrubbed)
    print("\n===== TOKEN MAP =====")
    print(json.dumps(s.token_map, indent=2))
    print("\n===== SCRUB REPORT =====")
    print(json.dumps(s.scrub_report(), indent=2))

if __name__ == '__main__':
    main()
