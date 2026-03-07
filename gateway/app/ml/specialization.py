import asyncio
import logging
from typing import Any, Dict, List

from gateway.app.ml.cross_evaluator import CrossDomainEvaluator
from gateway.app.ml.curriculum import get_all_domains, get_curriculum, get_intersections
try:
    from gateway.app.ml.data_adapter import DataAdapter
except ImportError:
    DataAdapter = None
try:
    from gateway.app.ml.dataset_expander import DatasetExpander
except ImportError:
    DatasetExpander = None
from gateway.app.ml.distillation import DistillationService
from gateway.app.ml.hf_data_manager import HFDataManager

logger = logging.getLogger("ml.specialization")


class IntegratedDomainSpecializer:
    """
    Orchestrator for multi-domain expert training.
    Executes the 8-week specialization plan across CS, AI, PROG, and MATH.
    """

    def __init__(self, secrets: Dict[str, str]):
            if not secrets:
                logger.warning("No secrets provided, initializing with empty dictionary.")
                secrets = {}
            self.secrets = secrets
            self.distiller = DistillationService(secrets=secrets)
            self.expander = DatasetExpander()
            self.cross_evaluator = CrossDomainEvaluator()
            self.data_manager = HFDataManager()
            self.adapter = DataAdapter()
            self.active_tasks = {}

    async def start_integrated_learning(self, domains: List[str] = None):
        """
        Start the parallel specialization process.
        """
        if domains is None:
            domains = get_all_domains()

        logger.info(f"Specialization: Starting integrated learning for domains: {domains}")

        # Phase 1: Common Foundations Discovery
        foundations = await self._discover_common_foundations()

        # Phase 2: Parallel Specialization
        tasks = []
        for domain in domains:
            curriculum = get_curriculum(domain)
            if curriculum:
                tasks.append(self._deep_specialize_domain(domain, curriculum))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Phase 3: Cross-Domain Integration
        integrated_knowledge = await self._build_cross_domain_knowledge(results)

        # Phase 4: Expert Evaluation
        domain_results_map = {res["domain"]: res for res in results if isinstance(res, dict)}
        final_report = await self.cross_evaluator.evaluate_specialization(domain_results_map)

        return {
            "status": "completed",
            "foundations": foundations,
            "expert_report": final_report,
            "integrated_knowledge": integrated_knowledge,
        }

    async def _discover_common_foundations(self) -> Dict:
        """Find the logical and mathematical bridges between all domains."""
        logger.info("Specialization: Mapping common foundations...")
        # Placeholder for real teacher-driven discovery
        return {}

    async def _deep_specialize_domain(self, domain: str, curriculum: Dict) -> Dict:
        """Execute deep training for a specific domain with real-world augmentation."""
        logger.info(f"Specialization: Deep dive into {domain}...")

        subtopics = curriculum.get("subtopics", [])
        hub_queries = curriculum.get("hub_queries", [])
        results = []

        # Phase A: Synthetic Distillation (The Foundation)
        for sub in subtopics[:1]:  # Demo limit
            logger.info(f"Specialization [{domain}]: Training on {sub}")
            synth_res = await self.distiller.run_distillation_cycle(sub, num_examples=5, expand=True)

            # Phase B: Real-World Augmentation (The Expert Edge)
            real_data_adapted = []
            if hub_queries:
                real_data_adapted = await self.augment_with_real_data(domain, hub_queries[0])

            # Phase C: Blended Finalization
            data_available = (synth_res and synth_res.get("success")) or (
                real_data_adapted and len(real_data_adapted) > 0
            )

            results.append(
                {
                    "subtopic": sub,
                    "status": "trained" if data_available else "skipped (no data)",
                    "synth_eval": synth_res.get("improvement_report") if synth_res else None,
                    "real_data_samples": len(real_data_adapted),
                }
            )

        return {"domain": domain, "specialization_level": "augmented", "details": results}

    async def augment_with_real_data(self, domain: str, query: str) -> List[Dict]:
        """Search and adapt real-world data from Hugging Face."""
        logger.info(f"Specialization [{domain}]: Searching Hub for '{query}'...")
        hits = self.data_manager.search_datasets(query, limit=1)

        if not hits:
            return []

        dataset_id = hits[0]["id"]
        logger.info(f"Specialization [{domain}]: Loading dataset '{dataset_id}'...")

        try:
            ds = self.data_manager.load_dataset(dataset_id, split="train", streaming=True)
            # Take a small sample of raw text
            raw_texts = []
            for i, row in enumerate(ds):
                if i >= 3:
                    break  # Limit for demo
                text = row.get("text") or row.get("content") or ""
                if text:
                    raw_texts.append(text)

            # Adapt to instructions
            adapted = await self.adapter.adapt_text_to_instructions(raw_texts, domain)
            return adapted
        except Exception as e:
            logger.error(f"Specialization [{domain}]: Augmentation failed: {e}")
            return []

    async def _build_cross_domain_knowledge(self, results: List[Any]) -> List[Dict]:
        """Train on the intersections between domains."""
        logger.info("Specialization: Integrating cross-domain bridges...")
        intersections = get_intersections()
        integration_results = []

        for bridge in intersections:
            theme = bridge["theme"]
            logger.info(f"Specialization: Building bridge - {theme}")
            # Simplified for now: just trigger a small distillation cycle on the bridge theme
            res = await self.distiller.run_distillation_cycle(theme, num_examples=3, expand=False)
            integration_results.append({"theme": theme, "status": "integrated", "eval": res.get("improvement_report")})

        return integration_results


class SpecializationService:
    """Gateway service for managing the specialization state."""

    def __init__(self, secrets: Dict[str, str]):
        self.specializer = IntegratedDomainSpecializer(secrets=secrets)

    async def trigger_specialization(self, config: Dict):
        """API entry point for specialization."""
        domains = config.get("domains", get_all_domains())
        return await self.specializer.start_integrated_learning(domains)
