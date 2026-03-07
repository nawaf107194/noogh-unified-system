class RecallEngine(MemoryUpdateListener):
    def on_memory_update(self, memory):
        print(f"Recall Engine updated with new memory: {memory}")

# Usage
mm = MemoryManager()
recall_engine = RecallEngine()

MemoryManager.add_listener(recall_engine)

# Simulate a memory update
mm.update_memory("New memory added")