# shared/data_processing_facade.py

from shared.data_transformation_utility import DataTransformationUtility
from shared.data_serializer import DataSerializer
from shared.data_normalization import DataNormalizer
from shared.data_pipeline_optimizer import DataPipelineOptimizer

class DataProcessingFacade:
    def __init__(self):
        self.transformation_utility = DataTransformationUtility()
        self.serializer = DataSerializer()
        self.normalizer = DataNormalizer()
        self.optimizer = DataPipelineOptimizer()

    def process_data_pipeline(self, data):
        """Full pipeline: transform -> normalize -> optimize -> serialize"""
        transformed = self.transformation_utility.transform(data)
        normalized = self.normalizer.normalize(transformed)
        optimized = self.optimizer.optimize(normalized)
        return self.serializer.serialize(optimized)

    def transform_and_serialize(self, data):
        """Transform and serialize without normalization"""
        transformed = self.transformation_utility.transform(data)
        return self.serializer.serialize(transformed)

    def normalize_data(self, data):
        """Only normalize data"""
        return self.normalizer.normalize(data)

    def optimize_pipeline(self, data):
        """Optimize data pipeline"""
        return self.optimizer.optimize(data)