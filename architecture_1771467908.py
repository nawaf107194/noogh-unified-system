# Example usage in another module
from architecture_1771467908 import DataAugmentationFactory

config = {'type': 'basic'}
factory = DataAugmentationFactory()
data_augmentor = factory.create_data_augmentor(config)
augmented_data = data_augmentor.augment(original_data)