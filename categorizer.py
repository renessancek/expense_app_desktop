import datetime
import json
import os
import re
import shutil

class Categorizer:
    def __init__(self, rules_path=None):
        if rules_path is None:
            default_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'expense-app-desktop')
            self.rules_path = os.path.join(default_dir, 'rules.json')
            self._migrate_legacy_rules()
        else:
            self.rules_path = rules_path

        self.load_rules()

    def _migrate_legacy_rules(self):
        legacy_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rules.json')
        if os.path.exists(self.rules_path):
            return
        if not os.path.exists(legacy_path):
            return

        os.makedirs(os.path.dirname(os.path.abspath(self.rules_path)), exist_ok=True)
        shutil.copy2(legacy_path, self.rules_path)

    def load_rules(self):
        if os.path.exists(self.rules_path):
            with open(self.rules_path, 'r') as f:
                data = json.load(f)
                self.mappings = data.get('mappings', {})
                self.rules = data.get('rules', [])
        else:
            self.mappings = {}
            self.rules = []

        self._compile_regexes()

    def _compile_regexes(self):
        self._compiled_rules = []
        for rule in self.rules:
            compiled_keywords = [re.compile(rf'\b{re.escape(k.lower())}\b') for k in rule['keywords']]
            self._compiled_rules.append({
                'category': rule['category'],
                'compiled_keywords': compiled_keywords
            })

        self._compiled_mappings = []
        for keyword, category in self.mappings.items():
            self._compiled_mappings.append((re.compile(rf'\b{re.escape(keyword.lower())}\b'), category))


    def save_rules(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.rules_path)), exist_ok=True)

        # Create backup before saving
        if os.path.exists(self.rules_path):
            backup_dir = os.path.join(os.path.dirname(os.path.abspath(self.rules_path)), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"rules_backup_{timestamp}.json")
            
            shutil.copy2(self.rules_path, backup_path)
            
            # Keep only the last 10 backups to save space
            backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith("rules_backup_")])
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    os.remove(old_backup)

        data = {
            'mappings': self.mappings,
            'rules': self.rules
        }
        with open(self.rules_path, 'w') as f:
            json.dump(data, f, indent=4)

    def _persist_rules(self):
        self.save_rules()
        self._compile_regexes()

    def _persist_rules(self):
        self.save_rules()
        self._compile_regexes()

    def suggest_category(self, description):
        desc = description.lower()

        # 1. First priority: Manual/Global Rules
        for rule in self._compiled_rules:
            for pattern in rule['compiled_keywords']:
                if pattern.search(desc):
                    return rule['category']


        # 2. Second priority: Learned Mappings
        for pattern, category in self._compiled_mappings:
            if pattern.search(desc):
                return category

        return 'Sonstiges'

    def add_mapping(self, keyword, category):
        self.mappings[keyword.lower()] = category
        self._persist_rules()

    def delete_mapping(self, keyword):
        normalized_keyword = keyword.lower().strip()
        if normalized_keyword in self.mappings:
            del self.mappings[normalized_keyword]
            self._persist_rules()

    def add_rule(self, keywords, category):
        # Check if rule with this category already exists and append keywords
        for rule in self.rules:
            if rule['category'] == category:
                rule['keywords'] = list(set(rule['keywords'] + keywords))
                self._persist_rules()
                return
        
        self.rules.append({"keywords": keywords, "category": category})
        self._persist_rules()

    def delete_rule(self, category):
        self.rules = [r for r in self.rules if r['category'] != category]
        self._persist_rules()

    def get_all_categories(self):
        # Unique set of categories from rules and mappings
        cats = {rule['category'] for rule in self.rules}
        cats.update(self.mappings.values())
        
        # Ensure default essential categories exist
        defaults = {"Sonstiges", "Supermarkt", "Amazon", "Versicherung", "Computerspiele", "Trading", "Haus"}
        cats.update(defaults)
        
        return sorted(list(cats))

    def update_rule_keywords(self, category, keywords):
        for rule in self.rules:
            if rule['category'] == category:
                rule['keywords'] = [k.strip().lower() for k in keywords]
                self._persist_rules()
                return True
        return False

    def rename_category(self, old_name, new_name):
        """Renames a category in both mappings and rules."""
        if not new_name or old_name == new_name:
            return False
            
        # Update mappings
        for keyword, category in self.mappings.items():
            if category == old_name:
                self.mappings[keyword] = new_name
                
        # Update rules
        for rule in self.rules:
            if rule['category'] == old_name:
                rule['category'] = new_name
                
        self._persist_rules()
        return True

    def restore_latest_backup(self):
        """Restores the most recent file from the backups directory."""
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(self.rules_path)), 'backups')
        if not os.path.exists(backup_dir):
            return False, "No backups found."
            
        backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith("rules_backup_")])
        if not backups:
            return False, "No backups found."
            
        latest_backup = backups[-1]
        shutil.copy2(latest_backup, self.rules_path)
        self.load_rules()
        return True, f"Restored from {os.path.basename(latest_backup)}"

    def extract_keyword(self, description):
        # Extract a potential keyword from a description (e.g., the first two words)
        words = description.split()
        return " ".join(words[:2]).lower() if words else ""
