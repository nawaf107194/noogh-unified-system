"""
Prompt Library Manager - Advanced Features
Manages bulk import, categorization, and intelligent prompt selection
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from gateway.app.prompts.prompt_manager import get_prompt_manager


@dataclass
class PromptMetadata:
    """Enhanced metadata for imported prompts."""

    source_file: str
    source_category: str
    original_size: int
    import_date: str
    quality_score: float  # 0-1 based on heuristics
    tags: List[str]
    use_cases: List[str]


class PromptLibrary:
    """
    Advanced prompt library with intelligent features:
    - Bulk import from collections
    - Smart categorization
    - Quality scoring
    - Semantic search
    - Usage analytics
    """

    def __init__(self, collection_dir: str):
            """
            Initialize library.

            Args:
                collection_dir: Path to system-prompts collection
            """
            self.collection_dir = Path(collection_dir)
            self.manager = get_prompt_manager()
            self.metadata_file = Path("data/prompts/library_metadata.json")
            self.metadata = {}

            if not self.metadata_file.exists():
                return

            self._load_metadata()

    def _load_metadata(self):
            """Load metadata from file."""
            if not self.metadata_file.exists():
                logger.warning("Metadata file does not exist.")
                return

            try:
                with open(self.metadata_file, "r") as f:
                    data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metadata from file: {e}")
                return

            for prompt_id, meta_dict in data.items():
                try:
                    self.metadata[prompt_id] = PromptMetadata(**meta_dict)
                except Exception as e:
                    logger.error(f"Failed to reconstruct metadata for {prompt_id}: {e}")

    def _save_metadata(self):
            """Save metadata to file."""
            if not hasattr(self.metadata_file, 'parent'):
                logger.error("self.metadata_file does not have a parent attribute.")
                return

            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

            if not self.metadata:
                logger.warning("No metadata to save.")
                return

            with open(self.metadata_file, "w") as f:
                data = {pid: vars(meta) for pid, meta in self.metadata.items()}
                json.dump(data, f, indent=2)

    def calculate_quality_score(self, content: str, filepath: Path) -> float:
        """
        Calculate quality score (0-1) based on heuristics.

        Factors:
        - Length (optimal range)
        - Structure (has sections)
        - Variables usage
        - Source reputation
        """
        score = 0.5  # Base score

        # Length score (optimal: 5KB-20KB)
        size_kb = len(content) / 1024
        if 5 <= size_kb <= 20:
            score += 0.2
        elif size_kb > 50:
            score -= 0.1  # Too long

        # Structure score
        if "##" in content or "====" in content:
            score += 0.1  # Has sections

        # Variables score
        import re

        variables = re.findall(r"\{(\w+)\}", content)
        if variables:
            score += 0.1

        # Source reputation
        reputation_sources = {
            "core": 0.2,
            "system": 0.15,
            "Cursor": 0.15,
            "Claude": 0.1,
        }

        for keyword, bonus in reputation_sources.items():
            if keyword.lower() in str(filepath).lower():
                score += bonus
                break

        # Cap at 1.0
        return min(score, 1.0)

    def extract_tags(self, content: str, filepath: Path) -> List[str]:
        """Extract relevant tags from content."""
        tags = []
        content_lower = content.lower()

        # Grouped keyword definitions
        tag_definitions = {
            "python": ["python", "pip", "pytest"],
            "javascript": ["javascript", "npm", "react", "vue"],
            "typescript": ["typescript", "tsx"],
            "go": ["golang", "go"],
            "rust": ["rust", "cargo"],
            "security": ["security", "vulnerability"],
            "testing": ["test", "qa"],
            "devops": ["deploy", "devops"],
            "frontend": ["ui", "frontend"],
            "backend": ["api", "backend"],
            "expert": ["senior", "expert"],
            "architect": ["architect"],
        }

        for tag, keywords in tag_definitions.items():
            if any(kw in content_lower for kw in keywords):
                tags.append(tag)

        return list(set(tags))

    def extract_use_cases(self, content: str) -> List[str]:
            """Extract potential use cases."""
            use_cases = []

            markers = {
                "code review": ["review", "analyze code", "code quality"],
                "debugging": ["debug", "fix", "error", "bug"],
                "architecture": ["architect", "design system", "scalability"],
                "documentation": ["document", "readme", "api docs"],
                "testing": ["test", "qa", "quality assurance"],
                "refactoring": ["refactor", "clean code", "optimize"],
            }

            if not content:
                logger.warning("Empty content received, returning empty list")
                return use_cases

            content_lower = content.lower()
            for use_case, keywords in markers.items():
                if any(kw in content_lower for kw in keywords):
                    use_cases.append(use_case)

            return use_cases

    def smart_import(
        self, categories: List[str] = None, min_quality: float = 0.5, max_size_kb: int = 50, limit: int = 100
    ) -> Dict:
        """Smart import with filtering and scoring."""
        if categories is None:
            categories = ["core", "system", "ide", "tasks"]

        imported = []
        skipped = []

        for category in categories:
            cat_path = self.collection_dir / category
            if not cat_path.exists():
                continue

            print(f"\n📂 Processing: {category}/")
            files = sorted(list(cat_path.glob("*.txt")) + list(cat_path.glob("*.md")), key=lambda f: f.stat().st_size)

            for filepath in files:
                if len(imported) >= limit:
                    break
                result = self._process_single_import(filepath, category, min_quality, max_size_kb)
                if result["success"]:
                    imported.append(result["data"])
                    print(f"  ✅ {filepath.stem:<40} Q:{result['data']['quality']:.2f} {result['data']['tags'][:2]}")
                else:
                    skipped.append(f"{filepath.name} ({result['reason']})")

        self._save_metadata()
        self._print_import_summary(imported, skipped)

        return {
            "imported": imported,
            "skipped": skipped[:10],
            "stats": {
                "total_imported": len(imported),
                "total_skipped": len(skipped),
                "avg_quality": sum(p["quality"] for p in imported) / len(imported) if imported else 0,
            },
        }

    def _process_single_import(
        self, filepath: Path, category: str, min_quality: float, max_size_kb: int
    ) -> Dict[str, Any]:
        """Process a single file for import."""
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            size_kb = len(content) / 1024

            if size_kb > max_size_kb:
                return {"success": False, "reason": f"too large: {size_kb:.1f}KB"}

            quality = self.calculate_quality_score(content, filepath)
            if quality < min_quality:
                return {"success": False, "reason": f"low quality: {quality:.2f}"}

            import re

            variables = list(set(re.findall(r"\{(\w+)\}", content)))
            tags = self.extract_tags(content, filepath)
            use_cases = self.extract_use_cases(content)

            validation = self.manager.validate_prompt(content, "standard")
            if not validation["valid"]:
                return {"success": False, "reason": validation["issues"][0]}

            import datetime

            prompt_id = self.manager.create_prompt(
                name=f"{category}/{filepath.stem}",
                description=f"Q{int(quality*100)}: {', '.join(tags[:3])} | {', '.join(use_cases[:2])}",
                template=content,
                category=category,
                variables=variables,
                author="library_import",
                safety_level="standard",
                is_public=True,
            )

            self.metadata[prompt_id] = PromptMetadata(
                source_file=str(filepath),
                source_category=category,
                original_size=int(size_kb * 1024),
                import_date=datetime.datetime.utcnow().isoformat(),
                quality_score=quality,
                tags=tags,
                use_cases=use_cases,
            )

            return {
                "success": True,
                "data": {"name": filepath.stem, "quality": quality, "tags": tags, "size_kb": size_kb},
            }
        except Exception as e:
            return {"success": False, "reason": str(e)[:50]}

    def _print_import_summary(self, imported: List[Dict], skipped: List[str]):
        """Print a nice summary to console."""
        print(f"\n{'='*70}")
        print("📊 Import Complete:")
        print(f"  ✅ Imported: {len(imported)}")
        print(f"  ⚠️  Skipped: {len(skipped)}")
        if imported:
            avg_q = sum(p["quality"] for p in imported) / len(imported)
            print(f"  📈 Avg Quality: {avg_q:.2f}")
        print(f"{'='*70}")

    def recommend_prompt(self, task_description: str, limit: int = 5) -> List[Dict]:
            """
            Recommend best prompts for a task using simple keyword matching.

            Args:
                task_description: User's task description
                limit: Number of recommendations

            Returns:
                List of recommended prompts with scores
            """
            task_lower = task_description.lower()
            recommendations = []
            TAG_MATCH_SCORE = 0.3
            USE_CASE_MATCH_SCORE = 0.4
            QUALITY_BONUS_MULTIPLIER = 0.3

            for prompt_id, metadata in self.metadata.items():
                score = 0.0

                # Tag matching
                for tag in metadata.tags:
                    if tag.lower() in task_lower:
                        score += TAG_MATCH_SCORE

                # Use case matching
                for use_case in metadata.use_cases:
                    if use_case.lower() in task_lower:
                        score += USE_CASE_MATCH_SCORE

                # Quality bonus
                score += metadata.quality_score * QUALITY_BONUS_MULTIPLIER

                if score > 0:
                    prompt = self.manager.get_prompt(prompt_id)
                    recommendations.append(
                        {
                            "prompt_id": prompt_id,
                            "name": prompt.name if prompt else "Unknown",
                            "score": score,
                            "tags": metadata.tags,
                            "use_cases": metadata.use_cases,
                            "quality": metadata.quality_score,
                        }
                    )

            # Sort by score
            recommendations.sort(key=lambda x: x["score"], reverse=True)

            return recommendations[:limit]


# Quick usage
if __name__ == "__main__":
    library = PromptLibrary("/home/noogh/projects/noogh_unified_system/src/system-prompts-and-models-of-ai-tools-main")

    # Smart import
    results = library.smart_import(categories=["core", "system", "ide"], min_quality=0.6, max_size_kb=40, limit=20)

    print("\n🎯 Recommendations for 'security code review':")
    recs = library.recommend_prompt("security code review", limit=5)
    for i, rec in enumerate(recs, 1):
        print(f"{i}. {rec['name']} (score: {rec['score']:.2f})")
