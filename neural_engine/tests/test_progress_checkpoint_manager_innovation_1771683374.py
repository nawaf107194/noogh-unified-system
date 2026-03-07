import pytest
from typing import Optional

class Checkpoint:
    pass  # Mock implementation of Checkpoint class

class ProgressCheckpointManager:
    def __init__(self):
        self.checkpoints = []

    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """الحصول على آخر نقطة تحقق"""
        return self.checkpoints[-1] if self.checkpoints else None

# Create an instance of the manager for testing
manager = ProgressCheckpointManager()

def test_get_latest_checkpoint_happy_path():
    # Arrange
    checkpoint = Checkpoint()
    manager.checkpoints.append(checkpoint)

    # Act
    result = manager.get_latest_checkpoint()

    # Assert
    assert result == checkpoint

def test_get_latest_checkpoint_empty_checkpoints():
    # Arrange
    # No checkpoints added

    # Act
    result = manager.get_latest_checkpoint()

    # Assert
    assert result is None

def test_get_latest_checkpoint_with_multiple_checkpoints():
    # Arrange
    checkpoint1 = Checkpoint()
    checkpoint2 = Checkpoint()
    manager.checkpoints.append(checkpoint1)
    manager.checkpoints.append(checkpoint2)

    # Act
    result = manager.get_latest_checkpoint()

    # Assert
    assert result == checkpoint2

@pytest.mark.asyncio
async def test_get_latest_checkpoint_async():
    # Arrange
    checkpoint = Checkpoint()
    manager.checkpoints.append(checkpoint)

    # Act and Assert
    async def get_checkpoint_async():
        return manager.get_latest_checkpoint()

    result = await get_checkpoint_async()
    assert result == checkpoint