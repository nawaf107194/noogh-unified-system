#!/usr/bin/env python3
"""
NOOGH Physics Educator Agent - FIXED VERSION
تحويل من JSON خام إلى كلاس Python حقيقي متكامل
An agent specialized in physics education: mechanics, electromagnetism,
quantum theory, optics, and more.
"""
import asyncio
import logging
import json
import math
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger("agents.physics_educator")


class PhysicsEducatorAgent:
    """
    An agent specialized in providing information and assistance
    related to physics, including mechanics, electromagnetism,
    quantum theory, optics, and more.

    FIXED: Converted from raw JSON to a full Python class.
    """

    # ------------------------------------------------------------------ #
    #  Knowledge base
    # ------------------------------------------------------------------ #

    KNOWLEDGE_BASE = {
        "mechanics": {
            "Newton's First Law": "An object at rest stays at rest, and an object in motion stays in motion unless acted upon by a net external force.",
            "Newton's Second Law": "F = ma. The net force on an object equals its mass times its acceleration.",
            "Newton's Third Law": "For every action, there is an equal and opposite reaction.",
            "Kinetic Energy": "KE = (1/2) * m * v^2",
            "Potential Energy (gravity)": "PE = m * g * h",
            "Momentum": "p = m * v",
            "Work": "W = F * d * cos(theta)",
            "Power": "P = W / t",
        },
        "electromagnetism": {
            "Coulomb's Law": "F = k * q1 * q2 / r^2",
            "Electric Field": "E = F / q = k * Q / r^2",
            "Ohm's Law": "V = I * R",
            "Power (electrical)": "P = V * I = I^2 * R",
            "Faraday's Law": "EMF = -dPhi_B/dt (changing magnetic flux induces EMF)",
            "Maxwell's Equations": "Four equations describing how electric and magnetic fields propagate and interact.",
        },
        "quantum_theory": {
            "Planck's Equation": "E = h * f (energy of a photon)",
            "de Broglie wavelength": "lambda = h / p (wave-particle duality)",
            "Heisenberg Uncertainty": "Delta_x * Delta_p >= hbar/2",
            "Schrodinger Equation": "ih * d(psi)/dt = H * psi (quantum state evolution)",
            "Photoelectric Effect": "KE_max = h*f - phi (work function)",
        },
        "optics": {
            "Snell's Law": "n1 * sin(theta1) = n2 * sin(theta2)",
            "Speed of Light": "c = 3 * 10^8 m/s in vacuum",
            "Mirror Equation": "1/f = 1/do + 1/di",
            "Lens Equation": "1/f = 1/do + 1/di",
            "Double-slit interference": "d * sin(theta) = m * lambda",
        },
        "thermodynamics": {
            "First Law": "Delta_U = Q - W (energy conservation)",
            "Second Law": "Entropy of an isolated system tends to increase.",
            "Ideal Gas Law": "PV = nRT",
            "Boltzmann Constant": "k_B = 1.38 * 10^-23 J/K",
        }
    }

    CONSTANTS = {
        "speed_of_light": (3e8, "m/s"),
        "planck": (6.626e-34, "J*s"),
        "gravitational": (6.674e-11, "N*m^2/kg^2"),
        "electron_charge": (1.602e-19, "C"),
        "electron_mass": (9.109e-31, "kg"),
        "proton_mass": (1.673e-27, "kg"),
        "avogadro": (6.022e23, "mol^-1"),
        "boltzmann": (1.381e-23, "J/K"),
        "gravity": (9.81, "m/s^2"),
        "gas_constant": (8.314, "J/(mol*K)"),
    }

    FORMULAS = {
        "kinetic_energy": lambda m, v: 0.5 * m * v ** 2,
        "potential_energy": lambda m, h, g=9.81: m * g * h,
        "momentum": lambda m, v: m * v,
        "force": lambda m, a: m * a,
        "work": lambda f, d, theta=0: f * d * math.cos(math.radians(theta)),
        "power": lambda w, t: w / t if t else 0,
        "ohms_law_v": lambda i, r: i * r,
        "wave_frequency": lambda v, lam: v / lam if lam else 0,
        "photon_energy": lambda f: 6.626e-34 * f,
    }

    def __init__(self):
        self.handlers = {
            "EXPLAIN_CONCEPT": self._explain_concept,
            "CALCULATE": self._calculate,
            "LIST_TOPICS": self._list_topics,
            "GET_CONSTANT": self._get_constant,
            "SOLVE_PROBLEM": self._solve_problem,
        }
        self._running = False
        logger.info("\u2705 PhysicsEducatorAgent initialized")

    # ------------------------------------------------------------------ #
    #  Task handlers
    # ------------------------------------------------------------------ #

    async def _explain_concept(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Explains a physics concept.
        Args:
            concept (str): The concept name.
            topic (str): Optional topic area.
        """
        concept = task.get("concept", task.get("input", ""))
        if not concept:
            return {"success": False, "error": "No concept provided"}

        logger.info(f"\U0001f4da Explaining concept: {concept}")

        concept_lower = concept.lower()
        found = []

        for topic, laws in self.KNOWLEDGE_BASE.items():
            for law_name, explanation in laws.items():
                if concept_lower in law_name.lower() or concept_lower in explanation.lower():
                    found.append({
                        "topic": topic,
                        "name": law_name,
                        "explanation": explanation
                    })

        if found:
            logger.info(f"\u2705 Found {len(found)} matches for '{concept}'")
            return {
                "success": True,
                "concept": concept,
                "results": found,
                "count": len(found)
            }
        else:
            return {
                "success": False,
                "concept": concept,
                "error": f"Concept '{concept}' not found in knowledge base.",
                "hint": "Try topics: mechanics, electromagnetism, quantum_theory, optics, thermodynamics"
            }

    async def _calculate(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs a physics calculation.
        Args:
            formula (str): Formula name.
            params (dict): Parameters for the formula.
        """
        formula_name = task.get("formula", "").lower().replace(" ", "_")
        params = task.get("params", {})

        if formula_name not in self.FORMULAS:
            return {
                "success": False,
                "error": f"Formula '{formula_name}' not available.",
                "available": list(self.FORMULAS.keys())
            }

        try:
            formula_func = self.FORMULAS[formula_name]
            result = formula_func(**params)
            logger.info(f"\u2705 Calculated {formula_name} = {result}")
            return {
                "success": True,
                "formula": formula_name,
                "params": params,
                "result": result
            }
        except (TypeError, ZeroDivisionError) as e:
            return {"success": False, "error": f"Calculation error: {e}"}

    async def _list_topics(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Lists all available topics and their concepts."""
        summary = {}
        for topic, laws in self.KNOWLEDGE_BASE.items():
            summary[topic] = list(laws.keys())
        return {"success": True, "topics": summary, "total_concepts": sum(len(v) for v in summary.values())}

    async def _get_constant(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a physics constant.
        Args:
            name (str): Constant name.
        """
        name = task.get("name", task.get("input", "")).lower().replace(" ", "_")
        if name in self.CONSTANTS:
            value, unit = self.CONSTANTS[name]
            return {"success": True, "name": name, "value": value, "unit": unit}
        return {
            "success": False,
            "error": f"Constant '{name}' not found.",
            "available": list(self.CONSTANTS.keys())
        }

    async def _solve_problem(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempts to solve a physics word problem.
        Args:
            problem (str): Problem description.
        """
        problem = task.get("problem", task.get("input", ""))
        if not problem:
            return {"success": False, "error": "No problem provided"}

        logger.info(f"\U0001f9ea Solving problem: {problem[:60]}")

        # Identify relevant concepts
        relevant = []
        for topic, laws in self.KNOWLEDGE_BASE.items():
            for law_name, explanation in laws.items():
                for keyword in problem.lower().split():
                    if len(keyword) > 3 and keyword in explanation.lower():
                        relevant.append({"topic": topic, "law": law_name, "explanation": explanation})
                        break

        return {
            "success": True,
            "problem": problem,
            "relevant_concepts": relevant[:5],
            "guidance": (
                "1. Identify given variables\n"
                "2. Identify unknown variable\n"
                "3. Select appropriate formula from relevant concepts\n"
                "4. Substitute values and solve\n"
                "5. Check units"
            )
        }

    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Unified task entry point."""
        action = task.get("action", task.get("type", "")).upper()
        handler = self.handlers.get(action)
        if handler:
            return await handler(task)
        # default: explain concept
        return await self._explain_concept(task)

    def start(self):
        self._running = True
        logger.info("\U0001f7e2 PhysicsEducatorAgent started")

    def stop(self):
        self._running = False
        logger.info("\U0001f534 PhysicsEducatorAgent stopped")


if __name__ == "__main__":
    async def main():
        logging.basicConfig(level=logging.INFO)
        agent = PhysicsEducatorAgent()
        agent.start()

        # Test 1: List topics
        topics = await agent.handle_task({"action": "LIST_TOPICS"})
        print("Topics:", json.dumps(topics, indent=2))

        # Test 2: Explain concept
        result = await agent.handle_task({
            "action": "EXPLAIN_CONCEPT",
            "concept": "Newton"
        })
        print("Concept:", json.dumps(result, indent=2))

        # Test 3: Calculate KE
        calc = await agent.handle_task({
            "action": "CALCULATE",
            "formula": "kinetic_energy",
            "params": {"m": 10, "v": 5}
        })
        print("KE calculation:", json.dumps(calc, indent=2))

    asyncio.run(main())
