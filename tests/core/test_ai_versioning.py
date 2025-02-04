"""
Tests for AI-aware versioning system.
"""
[Previous code remains the same...]

    @pytest.mark.asyncio
    async def test_version_deprecation(self, version_config):
        """Test version deprecation."""
        # Register version
        await version_manager.register_version(
            feature_id=version_config['feature_id'],
            version=version_config['version'],
            feature_type=version_config['feature_type'],
            model_dependencies=version_config['model_dependencies'],
            config=version_config['config'],
            description=version_config['description'],
            author=version_config['author']
        )
        
        # Deprecate version
        await version_manager.deprecate_version(
            feature_id=version_config['feature_id'],
            version=version_config['version']
        )
        
        # Verify version is deprecated
        history = version_manager.get_version_history(
            feature_id=version_config['feature_id']
        )
        assert len(history) == 1
        assert history[0].status == VersionStatus.DEPRECATED

    @pytest.mark.asyncio
    async def test_experiment_failure_handling(self, version_config, experiment_config):
        """Test experiment failure and rollback handling."""
        # Register control version
        await version_manager.register_version(
            feature_id=version_config['feature_id'],
            version=experiment_config['control_version'],
            feature_type=version_config['feature_type'],
            model_dependencies=version_config['model_dependencies'],
            config=version_config['config'],
            description='Control version',
            author=version_config['author']
        )
        
        # Register test version
        await version_manager.register_version(
            feature_id=version_config['feature_id'],
            version=version_config['version'],
            feature_type=version_config['feature_type'],
            model_dependencies=version_config['model_dependencies'],
            config=version_config['config'],
            description=version_config['description'],
            author=version_config['author']
        )
        
        # Start experiment
        experiment = await version_manager.start_experiment(
            feature_id=experiment_config['feature_id'],
            version=experiment_config['version'],
            control_version=experiment_config['control_version'],
            traffic_percentage=experiment_config['traffic_percentage'],
            success_metrics=experiment_config['success_metrics'],
            target_improvement=experiment_config['target_improvement'],
            rollback_threshold=experiment_config['rollback_threshold'],
            duration_days=experiment_config['duration_days']
        )
        
        # Update metrics with poor performance
        await version_manager.update_experiment_metrics(
            experiment_id=experiment.experiment_id,
            metrics={
                'conversion_rate': 0.05,  # 50% worse
                'satisfaction_score': 3.2  # 20% worse
            }
        )
        
        # Fast forward to experiment end
        experiment.end_time = datetime.now()
        await version_manager._conclude_experiment(experiment.experiment_id)
        
        # Verify version was rolled back
        version = await version_manager.get_active_version(
            feature_id=experiment_config['feature_id']
        )
        assert version is not None
        assert version.version == experiment_config['control_version']

    @pytest.mark.asyncio
    async def test_multiple_versions(self, version_config):
        """Test handling of multiple versions."""
        versions = ['1.0.0', '1.1.0', '1.2.0']
        
        # Register multiple versions
        for version in versions:
            config = version_config.copy()
            config['version'] = version
            await version_manager.register_version(
                feature_id=config['feature_id'],
                version=version,
                feature_type=config['feature_type'],
                model_dependencies=config['model_dependencies'],
                config=config['config'],
                description=f"Version {version}",
                author=config['author']
            )
        
        # Verify version history
        history = version_manager.get_version_history(
            feature_id=version_config['feature_id']
        )
        assert len(history) == 3
        assert [v.version for v in history] == versions[::-1]  # Newest first

    @pytest.mark.asyncio
    async def test_experiment_results_tracking(self, version_config, experiment_config):
        """Test experiment results tracking and retrieval."""
        # Setup and start experiment
        await version_manager.register_version(
            feature_id=version_config['feature_id'],
            version=experiment_config['control_version'],
            feature_type=version_config['feature_type'],
            model_dependencies=version_config['model_dependencies'],
            config=version_config['config'],
            description='Control version',
            author=version_config['author']
        )
        
        await version_manager.register_version(
            feature_id=version_config['feature_id'],
            version=version_config['version'],
            feature_type=version_config['feature_type'],
            model_dependencies=version_config['model_dependencies'],
            config=version_config['config'],
            description=version_config['description'],
            author=version_config['author']
        )
        
        experiment = await version_manager.start_experiment(**experiment_config)
        
        # Record experiment results
        results = {
            'conversion_rate': 0.15,
            'satisfaction_score': 4.8,
            'latency': 120.0
        }
        await version_manager.update_experiment_metrics(
            experiment_id=experiment.experiment_id,
            metrics=results
        )
        
        # Get experiment results
        stored_results = version_manager.get_experiment_results(
            experiment_id=experiment.experiment_id
        )
        
        assert stored_results['feature_id'] == experiment_config['feature_id']
        assert stored_results['version'] == experiment_config['version']
        assert stored_results['status'] == 'active'
        assert all(
            stored_results['metrics'][k] == v
            for k, v in results.items()
        )

    @pytest.mark.asyncio
    async def test_concurrent_experiments(self, version_config):
        """Test handling of concurrent experiments."""
        # Register base version
        base_version = '1.0.0'
        await version_manager.register_version(
            feature_id=version_config['feature_id'],
            version=base_version,
            feature_type=version_config['feature_type'],
            model_dependencies=version_config['model_dependencies'],
            config=version_config['config'],
            description='Base version',
            author=version_config['author']
        )
        
        # Register two experimental versions
        test_versions = ['1.1.0', '1.1.1']
        for version in test_versions:
            config = version_config.copy()
            config['version'] = version
            await version_manager.register_version(
                feature_id=config['feature_id'],
                version=version,
                feature_type=config['feature_type'],
                model_dependencies=config['model_dependencies'],
                config=config['config'],
                description=f"Test version {version}",
                author=config['author']
            )
        
        # Start concurrent experiments
        experiments = []
        for version in test_versions:
            experiment = await version_manager.start_experiment(
                feature_id=version_config['feature_id'],
                version=version,
                control_version=base_version,
                traffic_percentage=0.3,
                success_metrics=['conversion_rate'],
                target_improvement=0.1,
                rollback_threshold=0.05,
                duration_days=7
            )
            experiments.append(experiment)
        
        # Verify both experiments are running
        for experiment in experiments:
            results = version_manager.get_experiment_results(
                experiment_id=experiment.experiment_id
            )
            assert results['status'] == 'active'
            assert results['version'] in test_versions

if __name__ == "__main__":
    pytest.main([__file__])