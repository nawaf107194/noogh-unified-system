from typing import Dict, Any, Optional
from shared.data_serializer import DataSerializer
from shared.data_transformation_utility import DataTransformationUtility
from shared.data_normalization import DataNormalizer
from shared.chunked_data_loader import ChunkedDataLoader

class DataPipeline:
    """
    Coordinates the end-to-end data processing pipeline.
    Implements the Pipeline/Assembly Line pattern for data processing.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the pipeline with required components.
        
        Args:
            config: Dictionary containing configuration parameters
        """
        self.config = config
        self.serializer = DataSerializer(config.get('serialization_config'))
        self.transformer = DataTransformationUtility(config.get('transformation_config'))
        self.normalizer = DataNormalizer(config.get('normalization_config'))
        self.loader = ChunkedDataLoader(config.get('loading_config'))
        
    def process_data(self, raw_data: Any, pipeline_steps: Optional[list] = None) -> Any:
        """
        Execute the data processing pipeline.
        
        Args:
            raw_data: Input data to process
            pipeline_steps: Optional list of steps to execute (default: all steps)
            
        Returns:
            Processed data
        """
        if pipeline_steps is None:
            pipeline_steps = ['serialize', 'transform', 'normalize', 'load']
            
        data = raw_data
        
        if 'serialize' in pipeline_steps:
            data = self.serializer.serialize(data)
            
        if 'transform' in pipeline_steps:
            data = self.transformer.transform(data)
            
        if 'normalize' in pipeline_steps:
            data = self.normalizer.normalize(data)
            
        if 'load' in pipeline_steps:
            data = self.loader.load(data)
            
        return data
        
    def get_default_pipeline_config(self) -> Dict[str, Any]:
        """
        Returns default configuration for the pipeline.
        """
        return {
            'serialization_config': {},
            'transformation_config': {},
            'normalization_config': {},
            'loading_config': {}
        }