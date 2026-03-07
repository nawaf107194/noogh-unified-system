"""
Living Architectural Model v1.0
═══════════════════════════════

A dynamic, AST-based representation of the codebase structure.
Builds and maintains a graph of components, their relationships,
and derived metrics like centrality and fragility.

Used by the evolution engine to:
- Dynamically determine which files are "core" (high centrality)
- Predict impact of proposed changes
- Detect architectural smells
- Feed context to Brain for better refactoring decisions

Phase 1 of the Architectural Awareness roadmap.
"""

import ast
import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("unified_core.evolution.architecture")


# ═══════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════

@dataclass
class ComponentNode:
    """A single component (file) in the architecture graph."""
    path: str                          # Absolute path
    module: str                        # Python module name (dotted)
    layer: str                         # Architectural layer
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    import_targets: List[str] = field(default_factory=list)  # What this file imports
    imported_by: List[str] = field(default_factory=list)     # What imports this file
    lines: int = 0
    complexity: int = 0
    last_modified: float = 0.0
    last_scanned: float = 0.0
    
    # Derived metrics (computed after graph is built)
    in_degree: int = 0       # How many files import this
    out_degree: int = 0      # How many files this imports
    centrality: float = 0.0  # Normalized importance score
    is_core: bool = False    # Dynamically computed based on centrality


@dataclass
class DependencyEdge:
    """A dependency relationship between two components."""
    source: str      # Importing module
    target: str      # Imported module
    import_type: str # 'direct', 'from', 'conditional', 'lazy'
    symbols: List[str] = field(default_factory=list)  # Imported names


@dataclass 
class ClassInfo:
    """Detailed class information extracted via AST."""
    name: str
    file: str
    bases: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0


@dataclass
class ArchitecturalReport:
    """Summary of the architectural state."""
    total_components: int = 0
    total_edges: int = 0
    total_classes: int = 0
    total_functions: int = 0
    core_files: List[str] = field(default_factory=list)
    layers: Dict[str, int] = field(default_factory=dict)
    circular_deps: List[Tuple[str, str]] = field(default_factory=list)
    high_coupling: List[str] = field(default_factory=list)
    scan_time: float = 0.0


# ═══════════════════════════════════════════════════════════════
# Import Extractor (AST-based, non-recursive)
# ═══════════════════════════════════════════════════════════════

class ImportExtractor:
    """Extract imports, classes, and functions from a Python AST.
    
    v1.1: Non-recursive — only processes module.body top-level nodes.
    This avoids the performance trap of generic_visit on large files.
    """
    
    def __init__(self):
        self.imports: List[Dict[str, Any]] = []
        self.classes: List[ClassInfo] = []
        self.functions: List[str] = []
        self.top_level_functions: List[str] = []
    
    def extract(self, tree: ast.Module):
        """Process only top-level statements in the module."""
        for node in tree.body:
            if isinstance(node, ast.Import):
                self._handle_import(node)
            elif isinstance(node, ast.ImportFrom):
                self._handle_import_from(node)
            elif isinstance(node, ast.ClassDef):
                self._handle_class(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._handle_function(node)
            elif isinstance(node, (ast.If, ast.Try)):
                # Check for conditional/guarded imports (e.g. if TYPE_CHECKING:)
                self._handle_conditional(node)
    
    def _handle_import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append({
                "module": alias.name,
                "name": alias.asname or alias.name,
                "type": "direct",
                "line": node.lineno
            })
    
    def _handle_import_from(self, node: ast.ImportFrom):
        module = node.module or ""
        level = node.level or 0
        import_type = "from" if level == 0 else "relative"
        
        names = [alias.name for alias in (node.names or [])]
        self.imports.append({
            "module": module,
            "names": names,
            "type": import_type,
            "level": level,
            "line": node.lineno
        })
    
    def _handle_class(self, node: ast.ClassDef):
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                # e.g. module.ClassName
                parts = []
                current = base
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                bases.append('.'.join(reversed(parts)))
        
        methods = [n.name for n in node.body 
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        
        decorators = []
        for d in node.decorator_list:
            if isinstance(d, ast.Name):
                decorators.append(d.id)
            elif isinstance(d, ast.Attribute):
                decorators.append(d.attr)
        
        self.classes.append(ClassInfo(
            name=node.name,
            file="",  # Set by caller
            bases=bases,
            methods=methods,
            decorators=decorators,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno
        ))
    
    def _handle_function(self, node):
        self.top_level_functions.append(node.name)
        self.functions.append(node.name)
    
    def _handle_conditional(self, node):
        """Extract imports from if/try blocks (e.g. TYPE_CHECKING guards)."""
        body = []
        if isinstance(node, ast.If):
            body = node.body + (node.orelse or [])
        elif isinstance(node, ast.Try):
            body = node.body
            for handler in (node.handlers or []):
                body.extend(handler.body)
        
        for child in body:
            if isinstance(child, ast.Import):
                self._handle_import(child)
            elif isinstance(child, ast.ImportFrom):
                self._handle_import_from(child)


# ═══════════════════════════════════════════════════════════════
# Living Architecture Model
# ═══════════════════════════════════════════════════════════════

class LivingArchitectureModel:
    """
    A dynamic, self-updating model of the codebase architecture.
    
    Builds a graph of components (files), their dependencies (imports),
    and computes derived metrics (centrality, coupling, cohesion).
    
    Usage:
        model = LivingArchitectureModel(src_root="/path/to/src")
        model.scan()  # Full scan
        model.update_file("/path/to/changed_file.py")  # Incremental
        
        # Query the model
        model.get_impact("/path/to/file.py")
        model.get_core_files()
        model.detect_smells()
    """
    
    # Layer classification rules (ordered by priority)
    LAYER_RULES = [
        ("evolution",  "EVOLUTION"),
        ("core",       "CORE"),
        ("agent",      "CORE"),
        ("neural",     "CORE"),
        ("security",   "SECURITY"),
        ("governor",   "GOVERNANCE"),
        ("actuator",   "ACTUATORS"),
        ("executor",   "ACTUATORS"),
        ("tools",      "TOOLS"),
        ("scripts",    "TOOLS"),
        ("skills",     "SKILLS"),
    ]
    
    def __init__(self, src_root: str = None):
        if src_root is None:
            # Use src/ (not unified_core/) so module names match absolute imports
            # e.g. "unified_core.evolution.controller" instead of "evolution.controller"
            src_root = str(Path(__file__).resolve().parents[2])
        self.src_root = Path(src_root)
        
        # Graph data
        self.nodes: Dict[str, ComponentNode] = {}
        self.edges: List[DependencyEdge] = []
        self.classes: Dict[str, ClassInfo] = {}  # "file:class" -> ClassInfo
        
        # Indexes for fast lookup
        self._import_index: Dict[str, Set[str]] = {}  # module -> set of importers
        self._reverse_index: Dict[str, Set[str]] = {} # module -> set of imported modules
        
        # State
        self._last_full_scan: float = 0.0
        self._scan_count: int = 0
        
        # Persistence
        self._cache_file = Path(os.getenv(
            "NOOGH_ARCH_CACHE",
            os.path.expanduser("~/.noogh/evolution/arch_model.json")
        ))
    
    # ─── Scanning ─────────────────────────────────────────────────
    
    def scan(self, force: bool = False) -> ArchitecturalReport:
        """Full project scan. Rebuilds the entire graph."""
        start = time.time()
        
        self.nodes.clear()
        self.edges.clear()
        self.classes.clear()
        self._import_index.clear()
        self._reverse_index.clear()
        
        py_files = list(self.src_root.rglob("*.py"))
        
        for py_file in py_files:
            try:
                self._scan_file(str(py_file))
            except Exception as e:
                logger.debug(f"Skip {py_file.name}: {e}")
        
        # Resolve imports to actual files
        self._resolve_dependencies()
        
        # Compute derived metrics
        self._compute_metrics()
        
        self._last_full_scan = time.time()
        self._scan_count += 1
        
        report = self._generate_report()
        report.scan_time = time.time() - start
        
        # Save to disk
        self._save_cache()
        
        logger.info(
            f"🏗️ Architecture scan #{self._scan_count}: "
            f"{report.total_components} files, {report.total_edges} deps, "
            f"{len(report.core_files)} core files, "
            f"{len(report.circular_deps)} circular deps "
            f"({report.scan_time:.1f}s)"
        )
        
        return report
    
    def update_file(self, file_path: str):
        """Incremental update after a file changes."""
        abs_path = str(Path(file_path).resolve())
        
        # Remove old data for this file
        old_node = self.nodes.get(abs_path)
        if old_node:
            # Remove old edges originating from this file
            self.edges = [e for e in self.edges if e.source != old_node.module]
            # Remove old classes
            self.classes = {k: v for k, v in self.classes.items() 
                          if not k.startswith(f"{abs_path}:")}
        
        # Re-scan the file
        try:
            self._scan_file(abs_path)
        except Exception as e:
            logger.warning(f"Failed to update {abs_path}: {e}")
            return
        
        # Re-resolve and recompute
        self._resolve_dependencies()
        self._compute_metrics()
        
        logger.debug(f"🔄 Architecture updated: {Path(abs_path).name}")
    
    def _scan_file(self, file_path: str):
        """Scan a single file and extract its AST information."""
        path = Path(file_path)
        if not path.exists() or not path.suffix == '.py':
            return
        
        try:
            source = path.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(source)
        except SyntaxError:
            return
        
        extractor = ImportExtractor()
        extractor.extract(tree)
        
        # Determine module name
        try:
            rel = path.relative_to(self.src_root)
            module = str(rel).replace('/', '.').replace('.py', '')
            if module.endswith('.__init__'):
                module = module[:-9]
        except ValueError:
            module = path.stem
        
        # Determine architectural layer
        layer = self._classify_layer(str(path))
        
        # Create or update node
        node = ComponentNode(
            path=str(path),
            module=module,
            layer=layer,
            classes=[c.name for c in extractor.classes],
            functions=extractor.top_level_functions,
            import_targets=[],  # Filled during resolve
            lines=len(source.splitlines()),
            complexity=self._estimate_complexity(tree),
            last_modified=path.stat().st_mtime,
            last_scanned=time.time()
        )
        
        self.nodes[str(path)] = node
        
        # Store class info
        for cls in extractor.classes:
            cls.file = str(path)
            self.classes[f"{str(path)}:{cls.name}"] = cls
        
        # Store raw imports for later resolution
        node._raw_imports = extractor.imports
    
    def _classify_layer(self, path: str) -> str:
        """Classify a file into an architectural layer."""
        path_lower = path.lower()
        for keyword, layer in self.LAYER_RULES:
            if keyword in path_lower:
                return layer
        return "GENERAL"
    
    def _estimate_complexity(self, tree: ast.AST) -> int:
        """Quick complexity estimate from AST.
        
        v1.1: Capped at MAX_NODES to prevent hangs on large files.
        """
        MAX_NODES = 5000
        complexity = 1
        node_count = 0
        
        for node in ast.walk(tree):
            node_count += 1
            if node_count > MAX_NODES:
                # Estimate remaining complexity proportionally
                complexity = int(complexity * (node_count + 1000) / node_count)
                break
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                               ast.With, ast.Assert)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
    
    # ─── Dependency Resolution ────────────────────────────────────
    
    def _resolve_dependencies(self):
        """Resolve raw imports to actual file paths in the project.
        
        v1.1: Multi-strategy resolution handles:
        - Direct module match
        - Suffix match (e.g. 'unified_core.evolution.ledger' matches 'evolution.ledger')
        - Relative imports (from . / from .. / from ...)
        - Parent package match
        - Basename match as fallback
        """
        # Build multiple lookup indexes for flexible matching
        module_to_path: Dict[str, str] = {}      # exact module -> path
        suffix_index: Dict[str, str] = {}          # last N segments -> path
        basename_index: Dict[str, List[str]] = {}  # filename stem -> [paths]
        
        for path, node in self.nodes.items():
            module_to_path[node.module] = path
            
            # Build suffix index (all possible suffixes)
            parts = node.module.split('.')
            for i in range(len(parts)):
                suffix = '.'.join(parts[i:])
                # Only keep first match (more specific wins)
                if suffix not in suffix_index:
                    suffix_index[suffix] = path
            
            # Basename index
            basename = parts[-1] if parts else ''
            basename_index.setdefault(basename, []).append(path)
        
        self.edges.clear()
        self._import_index.clear()
        self._reverse_index.clear()
        
        for path, node in self.nodes.items():
            raw_imports = getattr(node, '_raw_imports', [])
            resolved_targets = set()
            
            for imp in raw_imports:
                target_module = imp.get("module", "")
                level = imp.get("level", 0)
                imp_type = imp.get("type", "direct")
                
                # ── Strategy 1: Resolve relative imports ──
                if level > 0:
                    parts = node.module.split('.')
                    if level <= len(parts):
                        base = '.'.join(parts[:-level])
                        target_module = f"{base}.{target_module}" if target_module else base
                    else:
                        continue  # Can't resolve — level too deep
                
                if not target_module:
                    continue
                
                # ── Strategy 2: Try exact match ──
                target_path = module_to_path.get(target_module)
                
                # ── Strategy 3: Suffix match ──
                # Handles: "unified_core.evolution.ledger" when stored as "evolution.ledger"
                if not target_path:
                    target_path = suffix_index.get(target_module)
                
                # ── Strategy 4: Strip common prefixes and try again ──
                if not target_path:
                    # Try removing 'unified_core.' prefix
                    for prefix in ('unified_core.', 'noogh.', 'src.'):
                        if target_module.startswith(prefix):
                            stripped = target_module[len(prefix):]
                            target_path = module_to_path.get(stripped)
                            if not target_path:
                                target_path = suffix_index.get(stripped)
                            if target_path:
                                break
                
                # ── Strategy 5: Parent package ──
                if not target_path and '.' in target_module:
                    parent = target_module.rsplit('.', 1)[0]
                    target_path = module_to_path.get(parent)
                    if not target_path:
                        target_path = suffix_index.get(parent)
                
                # ── Strategy 6: Basename fallback ──
                if not target_path:
                    last_part = target_module.rsplit('.', 1)[-1]
                    candidates = basename_index.get(last_part, [])
                    if len(candidates) == 1:
                        # Unambiguous — use it
                        target_path = candidates[0]
                
                # ── Record edge if resolved ──
                if target_path and target_path != path:
                    resolved_targets.add(target_path)
                    
                    edge = DependencyEdge(
                        source=node.module,
                        target=self.nodes[target_path].module,
                        import_type=imp_type,
                        symbols=imp.get("names", [])
                    )
                    self.edges.append(edge)
                    
                    # Update indexes
                    target_node = self.nodes[target_path]
                    self._import_index.setdefault(target_node.module, set()).add(node.module)
                    self._reverse_index.setdefault(node.module, set()).add(target_node.module)
            
            # Update node
            node.import_targets = list(resolved_targets)
            node.out_degree = len(resolved_targets)
    
    # ─── Metrics Computation ──────────────────────────────────────
    
    def _compute_metrics(self):
        """Compute derived metrics for all nodes."""
        # Compute in-degree (how many files import each file)
        in_counts: Dict[str, int] = {}
        for edge in self.edges:
            in_counts[edge.target] = in_counts.get(edge.target, 0) + 1
        
        max_in = max(in_counts.values()) if in_counts else 1
        
        for path, node in self.nodes.items():
            node.in_degree = in_counts.get(node.module, 0)
            node.imported_by = list(self._import_index.get(node.module, set()))
            
            # Centrality = normalized in-degree (0-1)
            # Files imported by many others are more "central"
            node.centrality = node.in_degree / max_in if max_in > 0 else 0
            
            # Dynamic core detection:
            # A file is "core" if it's in the top 20% by centrality
            # AND has at least 3 importers
            node.is_core = (node.centrality >= 0.3 and node.in_degree >= 3)
    
    # ─── Query API ────────────────────────────────────────────────
    
    def get_core_files(self) -> List[str]:
        """Return dynamically-detected core files sorted by centrality."""
        core = [(n.path, n.centrality, n.in_degree) 
                for n in self.nodes.values() if n.is_core]
        core.sort(key=lambda x: -x[1])
        return [os.path.basename(c[0]) for c in core]
    
    def get_impact(self, file_path: str) -> Dict[str, Any]:
        """Predict impact of changing a file.
        
        Returns which files depend on it (directly and transitively),
        and an impact score (0-1).
        """
        abs_path = str(Path(file_path).resolve())
        node = self.nodes.get(abs_path)
        if not node:
            return {"direct": [], "transitive": [], "impact_score": 0}
        
        # Direct dependents
        direct = list(self._import_index.get(node.module, set()))
        
        # Transitive dependents (BFS)
        visited = set(direct)
        queue = list(direct)
        transitive = []
        
        while queue:
            current = queue.pop(0)
            dependents = self._import_index.get(current, set())
            for dep in dependents:
                if dep not in visited:
                    visited.add(dep)
                    queue.append(dep)
                    transitive.append(dep)
        
        total_files = len(self.nodes) or 1
        impact_score = len(visited) / total_files
        
        return {
            "direct": direct,
            "transitive": transitive,
            "direct_count": len(direct),
            "transitive_count": len(transitive),
            "impact_score": round(impact_score, 3)
        }
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a file."""
        abs_path = str(Path(file_path).resolve())
        node = self.nodes.get(abs_path)
        if not node:
            return None
        
        return {
            "module": node.module,
            "layer": node.layer,
            "classes": node.classes,
            "functions": node.functions,
            "in_degree": node.in_degree,
            "out_degree": node.out_degree,
            "centrality": round(node.centrality, 3),
            "is_core": node.is_core,
            "imported_by": node.imported_by,
            "imports": [self.nodes[t].module for t in node.import_targets 
                       if t in self.nodes],
            "lines": node.lines,
            "complexity": node.complexity
        }
    
    def detect_smells(self) -> List[Dict[str, Any]]:
        """Detect architectural smells."""
        smells = []
        
        # 1. Circular dependencies
        for src_module, targets in self._reverse_index.items():
            for tgt_module in targets:
                reverse_targets = self._reverse_index.get(tgt_module, set())
                if src_module in reverse_targets:
                    pair = tuple(sorted([src_module, tgt_module]))
                    smell = {
                        "type": "circular_dependency",
                        "severity": "high",
                        "modules": list(pair),
                        "description": f"Circular dependency: {pair[0]} ↔ {pair[1]}"
                    }
                    if smell not in smells:
                        smells.append(smell)
        
        # 2. God files (too many responsibilities)
        for node in self.nodes.values():
            if len(node.classes) > 5 or len(node.functions) > 20:
                smells.append({
                    "type": "god_file",
                    "severity": "medium",
                    "file": os.path.basename(node.path),
                    "description": f"{os.path.basename(node.path)} has {len(node.classes)} classes, "
                                   f"{len(node.functions)} functions"
                })
        
        # 3. High coupling (file depends on too many others)
        avg_out = sum(n.out_degree for n in self.nodes.values()) / max(len(self.nodes), 1)
        for node in self.nodes.values():
            if node.out_degree > avg_out * 3 and node.out_degree > 10:
                smells.append({
                    "type": "high_coupling",
                    "severity": "medium",
                    "file": os.path.basename(node.path),
                    "out_degree": node.out_degree,
                    "description": f"{os.path.basename(node.path)} imports {node.out_degree} modules "
                                   f"(avg={avg_out:.1f})"
                })
        
        # 4. Layer violations (lower layer importing higher)
        layer_order = {"TOOLS": 0, "SKILLS": 1, "ACTUATORS": 2, "GENERAL": 3,
                       "SECURITY": 4, "GOVERNANCE": 4, "CORE": 5, "EVOLUTION": 6}
        
        for edge in self.edges:
            src_node = next((n for n in self.nodes.values() if n.module == edge.source), None)
            tgt_node = next((n for n in self.nodes.values() if n.module == edge.target), None)
            if src_node and tgt_node:
                src_level = layer_order.get(src_node.layer, 3)
                tgt_level = layer_order.get(tgt_node.layer, 3)
                if src_level < tgt_level and abs(src_level - tgt_level) > 1:
                    smells.append({
                        "type": "layer_violation",
                        "severity": "low",
                        "source": os.path.basename(src_node.path),
                        "target": os.path.basename(tgt_node.path),
                        "description": f"{src_node.layer}→{tgt_node.layer}: "
                                       f"{os.path.basename(src_node.path)} imports "
                                       f"{os.path.basename(tgt_node.path)}"
                    })
        
        return smells
    
    def _generate_report(self) -> ArchitecturalReport:
        """Generate a summary report."""
        layer_counts: Dict[str, int] = {}
        total_classes = 0
        total_funcs = 0
        
        for node in self.nodes.values():
            layer_counts[node.layer] = layer_counts.get(node.layer, 0) + 1
            total_classes += len(node.classes)
            total_funcs += len(node.functions)
        
        # Detect circular deps
        circular = []
        seen_pairs = set()
        for src_module, targets in self._reverse_index.items():
            for tgt_module in targets:
                reverse_targets = self._reverse_index.get(tgt_module, set())
                if src_module in reverse_targets:
                    pair = tuple(sorted([src_module, tgt_module]))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        circular.append(pair)
        
        return ArchitecturalReport(
            total_components=len(self.nodes),
            total_edges=len(self.edges),
            total_classes=total_classes,
            total_functions=total_funcs,
            core_files=self.get_core_files(),
            layers=layer_counts,
            circular_deps=circular,
            high_coupling=[os.path.basename(n.path) for n in self.nodes.values() 
                          if n.out_degree > 10]
        )
    
    # ─── Persistence ──────────────────────────────────────────────
    
    def _save_cache(self):
        """Save the model to disk for fast reload."""
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "version": "1.0",
                "scan_time": self._last_full_scan,
                "scan_count": self._scan_count,
                "nodes": {
                    p: {
                        "module": n.module, "layer": n.layer,
                        "classes": n.classes, "functions": n.functions,
                        "lines": n.lines, "in_degree": n.in_degree,
                        "out_degree": n.out_degree, "centrality": n.centrality,
                        "is_core": n.is_core
                    }
                    for p, n in self.nodes.items()
                },
                "core_files": self.get_core_files(),
                "edge_count": len(self.edges)
            }
            
            with open(self._cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save arch cache: {e}")
    
    def load_cache(self) -> bool:
        """Load cached model from disk. Returns True if loaded."""
        try:
            if not self._cache_file.exists():
                return False
            
            with open(self._cache_file, 'r') as f:
                data = json.load(f)
            
            self._last_full_scan = data.get("scan_time", 0)
            self._scan_count = data.get("scan_count", 0)
            
            logger.info(f"🏗️ Architecture model loaded from cache "
                       f"({len(data.get('nodes', {}))} components)")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load arch cache: {e}")
            return False


# ═══════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════

_model_instance: Optional[LivingArchitectureModel] = None

def get_architecture_model(src_root: str = None) -> LivingArchitectureModel:
    """Get or create the singleton architecture model."""
    global _model_instance
    if _model_instance is None:
        _model_instance = LivingArchitectureModel(src_root)
    return _model_instance


# ═══════════════════════════════════════════════════════════════
# CLI for testing
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    src_root = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[1])
    
    model = LivingArchitectureModel(src_root)
    report = model.scan()
    
    print(f"\n{'═' * 60}")
    print(f"🏗️  Living Architecture Model — Scan Report")
    print(f"{'═' * 60}")
    print(f"  📁 Components: {report.total_components}")
    print(f"  🔗 Dependencies: {report.total_edges}")
    print(f"  🏛️  Classes: {report.total_classes}")
    print(f"  ⚙️  Functions: {report.total_functions}")
    print(f"  ⏱️  Scan time: {report.scan_time:.2f}s")
    
    print(f"\n{'─' * 60}")
    print(f"  📊 Layers:")
    for layer, count in sorted(report.layers.items(), key=lambda x: -x[1]):
        bar = '█' * count
        print(f"    {layer:12s} │ {count:3d} │ {bar}")
    
    print(f"\n{'─' * 60}")
    print(f"  🎯 Core Files (dynamically detected):")
    for f in report.core_files[:15]:
        print(f"    • {f}")
    
    if report.circular_deps:
        print(f"\n{'─' * 60}")
        print(f"  ⚠️  Circular Dependencies ({len(report.circular_deps)}):")
        for a, b in report.circular_deps[:10]:
            print(f"    ↔ {a.split('.')[-1]} ↔ {b.split('.')[-1]}")
    
    smells = model.detect_smells()
    if smells:
        print(f"\n{'─' * 60}")
        print(f"  🦨 Architectural Smells ({len(smells)}):")
        for smell in smells[:10]:
            print(f"    [{smell['severity'].upper():6s}] {smell['type']:25s} │ {smell['description']}")
    
    print(f"\n{'═' * 60}")
