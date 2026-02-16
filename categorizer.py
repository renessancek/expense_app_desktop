import json
import os

class Categorizer:
    def __init__(self, rules_path='rules.json'):
        self.rules_path = rules_path
        self.load_rules()

    def load_rules(self):
        if os.path.exists(self.rules_path):
            with open(self.rules_path, 'r') as f:
                data = json.load(f)
                self.mappings = data.get('mappings', {})
                self.rules = data.get('rules', [])
        else:
            self.mappings = {}
            self.rules = []

    def save_rules(self):
        data = {
            'mappings': self.mappings,
            'rules': self.rules
        }
        with open(self.rules_path, 'w') as f:
            json.dump(data, f, indent=4)

    def suggest_category(self, description):
        desc = description.lower()

        # Check for exact or partial matches in the learned mappings
        for keyword, category in self.mappings.items():
            if keyword in desc:
                return category

        # Default rule-based categorization for common items if no learned mapping exists
        for rule in self.rules:
            if any(keyword in desc for keyword in rule['keywords']):
                return rule['category']

        return 'Sonstiges'

    def add_mapping(self, keyword, category):
        self.mappings[keyword.lower()] = category
        self.save_rules()

    def delete_mapping(self, keyword):
        if keyword in self.mappings:
            del self.mappings[keyword]
            self.save_rules()

    def add_rule(self, keywords, category):
        # Check if rule with this category already exists and append keywords
        for rule in self.rules:
            if rule['category'] == category:
                rule['keywords'] = list(set(rule['keywords'] + keywords))
                self.save_rules()
                return
        
        self.rules.append({"keywords": keywords, "category": category})
        self.save_rules()

    def delete_rule(self, category):
        self.rules = [r for r in self.rules if r['category'] != category]
        self.save_rules()

    def update_rule_keywords(self, category, keywords):
        for rule in self.rules:
            if rule['category'] == category:
                rule['keywords'] = [k.strip().lower() for k in keywords]
                self.save_rules()
                return True
        return False

    def extract_keyword(self, description):
        # Extract a potential keyword from a description (e.g., the first two words)
        words = description.split()
        return " ".join(words[:2]).lower() if words else ""
