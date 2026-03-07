"""
Query Classifier for Strict Mathematical Reasoning System
Detects mathematical/logical queries and routes to appropriate pipeline
"""

import re
from typing import Dict


class QueryClassifier:
    """Classifies queries as mathematical/strict or conversational"""

    def __init__(self):
        self.math_keywords = [
            # English
            "matrix",
            "determinant",
            "inverse",
            "derivative",
            "integral",
            "proof",
            "prove",
            "derive",
            "calculate",
            "solve",
            "verify",
            "dimension",
            "formula",
            "equation",
            "theorem",
            "lemma",
            "eigenvalue",
            "eigenvector",
            "rank",
            "trace",
            "transpose",
            "linear algebra",
            "calculus",
            "differential",
            "partial",
            # Arabic
            "مصفوفة",
            "محدد",
            "معكوس",
            "مشتقة",
            "تكامل",
            "برهان",
            "اثبات",
            "اشتق",
            "احسب",
            "حل",
            "تحقق",
            "بعد",
            "صيغة",
            "معادلة",
            "نظرية",
        ]

        self.strict_indicators = [
            "step by step",
            "خطوة بخطوة",
            "rigorously",
            "بدقة",
            "verify",
            "تحقق",
            "prove",
            "اثبت",
            "derive",
            "اشتق",
        ]

    def is_mathematical(self, query: str) -> bool:
            """
            Determine if query is mathematical/logical

            Args:
                query: User query

            Returns:
                True if mathematical query
            """
            if not isinstance(query, str):
                raise TypeError("The 'query' argument must be a string.")

            try:
                query_lower = query.lower()
            except Exception as e:
                raise ValueError(f"Failed to process the query: {e}")

            # Check for mathematical keywords
            has_math_keyword = any(kw in query_lower for kw in self.math_keywords)

            # Check for mathematical symbols
            has_math_symbols = bool(re.search(r"[\+\-\*/\=\^\(\)\[\]]", query))

            # Check for numbers with operations
            has_calculations = bool(re.search(r"\d+\s*[\+\-\*/]\s*\d+", query))

            result = has_math_keyword or (has_math_symbols and has_calculations)
            self.log.info(f"Query '{query}' is {'mathematical' if result else 'not mathematical'}")

            return result

    def requires_strict_mode(self, query: str) -> bool:
            """
            Determine if query requires strict reasoning mode

            Args:
                query: User query

            Returns:
                True if strict mode required
            """
            if not isinstance(query, str):
                raise TypeError("The 'query' argument must be a string.")

            try:
                query_lower = query.lower()
            except Exception as e:
                raise ValueError(f"Failed to process query: {e}")

            # Strict mode if mathematical AND has strict indicators
            is_math = self.is_mathematical(query)
            has_strict_indicator = any(ind in query_lower for ind in self.strict_indicators)

            # Also strict if asking for proof/derivation
            asks_for_proof = any(word in query_lower for word in ["prove", "derive", "اثبت", "اشتق", "برهان"])

            result = is_math and (has_strict_indicator or asks_for_proof)
            self.logger.info(f"Query '{query}' requires strict mode: {result}")
            return result

    def classify(self, query: str) -> str:
        """
        Classify query type

        Args:
            query: User query

        Returns:
            'strict' or 'conversational'
        """
        if self.requires_strict_mode(query):
            return "strict"
        elif self.is_mathematical(query):
            return "mathematical"  # Math but not strict
        else:
            return "conversational"

    def get_classification_details(self, query: str) -> Dict:
        """
        Get detailed classification information

        Args:
            query: User query

        Returns:
            Classification details
        """
        return {
            "query": query,
            "classification": self.classify(query),
            "is_mathematical": self.is_mathematical(query),
            "requires_strict": self.requires_strict_mode(query),
            "detected_keywords": [kw for kw in self.math_keywords if kw in query.lower()],
        }


if __name__ == "__main__":
    # Test cases
    classifier = QueryClassifier()

    test_queries = [
        "Calculate the determinant of a 2x2 matrix",
        "Prove that the determinant of a matrix equals the product of eigenvalues",
        "What is the weather today?",
        "Derive the formula for matrix inverse step by step",
        "احسب محدد المصفوفة",
        "اثبت أن محدد المصفوفة يساوي حاصل ضرب القيم الذاتية",
    ]

    print("Query Classification Tests:\n")
    for query in test_queries:
        details = classifier.get_classification_details(query)
        print(f"Query: {query}")
        print(f"Classification: {details['classification']}")
        print(f"Requires Strict: {details['requires_strict']}")
        print(f"Keywords: {details['detected_keywords']}")
        print("-" * 60)
