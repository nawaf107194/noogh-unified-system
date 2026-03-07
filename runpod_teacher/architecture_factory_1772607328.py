# Register architecture
factory = ArchitectureFactory(config_manager)
factory.register("my_architecture", MyArchitectureClass, 
                 ArchitectureSpec(config_key="my_arch_config", 
                                 required_params=["param1", "param2"],
                                 dependencies=[DependencyClass1, DependencyClass2]))

# Create architecture
architecture = factory.create("my_architecture", param1="value1", param2="value2")