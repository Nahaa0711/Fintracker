"""Transaction categorization engine."""
import json
from typing import Optional, List, Dict, Any
from src.database import Database


class Categorizer:
    def __init__(self, db: Database):
        self.db = db
        self._load_categories()
    
    def _load_categories(self):
        """Load categories from database into memory."""
        self.categories = self.db.get_categories()
    
    def categorize(self, description: str, debug: bool = False) -> Optional[int]:
        """Find matching category for transaction description."""
        description_lower = description.lower()
        
        if debug:
            print(f"  Categorizing: {description}")
        
        # Try to match keywords
        for category in self.categories:
            if not category['keywords']:
                continue
            
            keywords = json.loads(category['keywords'])
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    if debug:
                        print(f"    -> Matched '{keyword}' to {category['name']}")
                    return category['id']
        
        if debug:
            print(f"    -> No match found")
        return None  # Uncategorized
    
    def add_category_with_keywords(self, name: str, keywords: List[str], parent_name: Optional[str] = None) -> int:
        """Add a new category with keywords."""
        parent_id = None
        
        if parent_name:
            # Find parent category
            for cat in self.categories:
                if cat['name'] == parent_name and cat['parent_id'] is None:
                    parent_id = cat['id']
                    break
            
            # Create parent if doesn't exist
            if parent_id is None:
                parent_id = self.db.add_category(parent_name)
        
        category_id = self.db.add_category(name, parent_id, keywords)
        self._load_categories()  # Reload
        return category_id
    
    def initialize_default_categories(self):
        """Set up default category structure."""
        default_categories = {
            "Food": {
                "Groceries": ["loblaws", "metro", "walmart", "sobeys", "safeway", "t&t", "supermarket"],
                "Dining": ["restaurant", "pizza", "mcdonald", "tim horton", "starbucks", "uber eats", "doordash", "osmow", "shawerma", "shozan"],
                "Coffee": ["starbucks", "tim hortons", "second cup", "coffee"]
            },
            "Transportation": {
                "Gas": ["shell", "esso", "petro", "chevron", "gas station"],
                "Transit": ["ttc", "presto", "transit", "communauto"],
                "Ride Share": ["uber", "lyft"]
            },
            "Shopping": {
                "Retail": ["amazon", "bestbuy", "walmart", "shoppers drug mart"],
                "Clothing": ["zara", "h&m", "uniqlo", "gap"],
                "Electronics": ["apple", "bestbuy", "canada computers"]
            },
            "Health": {
                "Pharmacy": ["shoppers drug mart", "rexall", "pharmacy"],
                "Medical": ["hospital", "clinic", "doctor"],
                "Cannabis": ["value buds", "tokyo smoke"]
            },
            "Education": {
                "Tuition": ["uoft", "university", "college"],
                "Books": ["indigo", "chapters", "bookstore"],
                "Supplies": ["staples", "grand & toy"]
            },
            "Entertainment": {
                "Streaming": ["netflix", "spotify", "disney", "amazon prime"],
                "Movies": ["cineplex", "theatre"],
                "Gaming": ["steam", "playstation", "xbox"]
            },
            "Utilities": {
                "Internet": ["rogers", "bell", "telus"],
                "Phone": ["rogers", "bell", "fido", "koodo"],
                "Hydro": ["toronto hydro", "enbridge"]
            }
        }
        
        for parent_name, subcategories in default_categories.items():
            for subcat_name, keywords in subcategories.items():
                self.add_category_with_keywords(subcat_name, keywords, parent_name)
    
    def get_category_tree(self) -> Dict[str, List[str]]:
        """Get categories organized by parent."""
        tree = {}
        
        for cat in self.categories:
            if cat['parent_id'] is None:
                tree[cat['name']] = []
        
        for cat in self.categories:
            if cat['parent_id'] is not None:
                # Find parent name
                parent = next((c for c in self.categories if c['id'] == cat['parent_id']), None)
                if parent:
                    if parent['name'] not in tree:
                        tree[parent['name']] = []
                    tree[parent['name']].append(cat['name'])
        
        return tree




