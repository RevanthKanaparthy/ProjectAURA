import networkx as nx
import pickle
import os
import re

GRAPH_FILE = "storage/graph_data.pkl"

def simple_stem(word: str) -> str:
    """A basic stemmer to handle plurals and common suffixes."""
    word = word.lower().strip()
    if not word:
        return ""
    
    # Plurals
    if word.endswith('es') and len(word) > 3:
        return word[:-2]
    if word.endswith('s') and not word.endswith(('is', 'as', 'us', 'ss')) and len(word) > 2:
        return word[:-1]
    
    # Verb/Adjective endings (improves matching for 'patented', 'publishing')
    if word.endswith('ing') and len(word) > 4:
        return word[:-3]
    if word.endswith('ed') and len(word) > 3:
        return word[:-2]
        
    return word

class CogGraph:
    def __init__(self):
        self.graph = nx.Graph()
        self.load()

    def load(self):
        if os.path.exists(GRAPH_FILE):
            with open(GRAPH_FILE, "rb") as f:
                self.graph = pickle.load(f)
        else:
            # Ensure storage directory exists
            os.makedirs(os.path.dirname(GRAPH_FILE), exist_ok=True)

    def save(self):
        with open(GRAPH_FILE, "wb") as f:
            pickle.dump(self.graph, f)

    def add_entry(self, chunk_id, themes, entities):
        """Adds a chunk and links it to extracted themes and entities."""
        # Add Chunk Node
        self.graph.add_node(chunk_id, type="chunk")
        
        # Link Themes
        for theme in themes:
            theme_id = f"theme:{theme.lower().strip()}"
            self.graph.add_node(theme_id, type="theme", label=theme)
            self.graph.add_edge(chunk_id, theme_id)
            
        # Link Entities
        for entity in entities:
            entity_id = f"entity:{entity.lower().strip()}"
            self.graph.add_node(entity_id, type="entity", label=entity)
            self.graph.add_edge(chunk_id, entity_id)
        
        self.save()

    def find_related_chunks(self, themes, entities):
        """Finds chunks connected to the given themes or entities using fuzzy, stemmed matching."""
        related_chunks = set()
        
        # Debug: Print graph stats to ensure data exists
        print(f"DEBUG: Graph Search - Total Nodes: {self.graph.number_of_nodes()}")
        
        # Stem the incoming query themes and entities
        target_theme_stems = {simple_stem(t) for t in themes if t}
        target_entity_stems = {simple_stem(e) for e in entities if e}
        
        print(f"DEBUG: Query Stems - Themes: {target_theme_stems}, Entities: {target_entity_stems}")

        # No need to search if the query has no extractable terms
        if not target_theme_stems and not target_entity_stems:
            return []

        match_count = 0
        for node, data in self.graph.nodes(data=True):
            node_type = data.get("type")
            if node_type not in ["theme", "entity"]:
                continue
            
            if ":" not in node: continue
            label = node.split(":", 1)[1]
            
            # Tokenize and stem the label from the graph node
            # Split on space, slash, hyphen, parens to handle "patent(s)" or "multi-word"
            graph_label_words = set(re.split(r'[\s/\-()]+', label)) 
            graph_label_stems = {simple_stem(w) for w in graph_label_words if w}

            is_match = False
            
            # 1. Check Themes
            if node_type == "theme" and target_theme_stems:
                # Strategy A: Stem Intersection
                if not target_theme_stems.isdisjoint(graph_label_stems):
                    is_match = True
                # Strategy B: Substring match on raw label (fallback)
                elif any(stem in label for stem in target_theme_stems):
                    is_match = True

            # 2. Check Entities
            elif node_type == "entity" and target_entity_stems:
                if not target_entity_stems.isdisjoint(graph_label_stems):
                    is_match = True
                elif any(stem in label for stem in target_entity_stems):
                    is_match = True
            
            if is_match:
                match_count += 1
                neighbors = self.graph.neighbors(node)
                related_chunks.update(neighbors)
                
        print(f"DEBUG: Graph Search - Matched {match_count} nodes, found {len(related_chunks)} related chunks.")
        return list(related_chunks)

# Singleton instance
graph_store = CogGraph()