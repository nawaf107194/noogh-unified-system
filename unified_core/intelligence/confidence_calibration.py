import unified_core.intelligence.memory_compression as memory

class ConfidenceCalibration:
    def __init__(self):
        self.memory = memory.MemoryCompression()

    def update_confidence(self, action, outcome):
        # Retrieve historical data for similar actions
        past_data = self.memory.retrieve_similar_actions(action)
        
        if not past_data:
            return 0.5  # Neutral confidence if no history
        
        success_rate = sum(1 for result in past_data if result == outcome) / len(past_data)
        
        # Adjust confidence based on the success rate
        if success_rate < 0.2:
            return 0.3
        elif success_rate < 0.5:
            return 0.6
        elif success_rate < 0.8:
            return 0.9
        else:
            return 1.0

    def get_confidence_threshold(self, action):
        confidence = self.update_confidence(action, "success")
        if confidence > 0.75:
            threshold = 0.85
        elif confidence > 0.5:
            threshold = 0.75
        else:
            threshold = 0.6
        
        return threshold

# Example usage
if __name__ == '__main__':
    calibration = ConfidenceCalibration()
    action_confidence = calibration.update_confidence("buy_signal", "success")
    confidence_threshold = calibration.get_confidence_threshold("buy_signal")
    print(f"Action confidence: {action_confidence}, Confidence threshold: {confidence_threshold}")