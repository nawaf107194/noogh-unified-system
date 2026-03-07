# unified_core/intelligence/causal_reasoning.py

from unified_core.intelligence.systems_thinking import SystemsThinking
from unified_core.intelligence.session_time_filter import SessionTimeFilter

class CausalReasoning:
    def __init__(self, systems_thinking: SystemsThinking, session_time_filter: SessionTimeFilter):
        self.systems_thinking = systems_thinking
        self.session_time_filter = session_time_filter

    def analyze_failure(self, task_result):
        """
        Analyzes the failure of a task to identify its root cause.
        
        :param task_result: Result of the failed task
        :return: Root cause of the failure
        """
        # Use Systems Thinking to identify potential causes
        causal_factors = self.systems_thinking.identify_causal_factors(task_result)
        
        # Filter out temporary or false positive issues
        filtered_causes = self.session_time_filter.filter_out_temporary_issues(causal_factors)
        
        return filtered_causes

    def suggest_alternatives(self, root_cause):
        """
        Suggests alternative actions based on the identified root cause.
        
        :param root_cause: Root cause of the failure
        :return: List of alternative actions
        """
        alternatives = []
        for factor in root_cause:
            if "temporary" in factor.lower():
                alternatives.append(f"Retry task after cooling down")
            elif "resource" in factor.lower():
                alternatives.append(f"Increase resources or allocate more capacity")
            # Add more alternative suggestions based on the root cause
        return alternatives

# Example usage
if __name__ == '__main__':
    systems_thinking = SystemsThinking()
    session_time_filter = SessionTimeFilter()
    causal_reasoning = CausalReasoning(systems_thinking, session_time_filter)
    
    task_result = {"status": "failed", "message": "Resource limit exceeded"}
    root_cause = causal_reasoning.analyze_failure(task_result)
    print("Root Cause:", root_cause)
    alternatives = causal_reasoning.suggest_alternatives(root_cause)
    print("Alternatives:", alternatives)