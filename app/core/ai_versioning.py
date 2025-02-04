"""
AI-aware versioning system for managing AI model versions,
feature experiments, and scoring algorithm evolution.
"""
[Previous code remains the same until _conclude_experiment method...]

    async def _conclude_experiment(self, experiment_id: str):
        """Conclude an experiment and decide on rollout/rollback."""
        with self._lock:
            experiment = self._active_experiments[experiment_id]
            feature_version = self._versions[experiment.feature_id][experiment.version]
            
            # Calculate improvement
            improvements = []
            for metric in experiment.success_metrics:
                if metric in feature_version.metrics:
                    control_version = self._versions[experiment.feature_id][experiment.control_version]
                    if metric in control_version.metrics:
                        improvement = (feature_version.metrics[metric] - 
                                     control_version.metrics[metric]) / \
                                    control_version.metrics[metric]
                        improvements.append(improvement)
            
            avg_improvement = sum(improvements) / len(improvements) if improvements else 0
            
            # Decide on rollout/rollback
            new_status = VersionStatus.EXPERIMENT
            if avg_improvement >= experiment.target_improvement:
                # Success - activate the version
                new_status = VersionStatus.ACTIVE
                logger.info(f"Experiment {experiment_id} succeeded - activating version")
            elif avg_improvement < -experiment.rollback_threshold:
                # Failure - rollback
                new_status = VersionStatus.ROLLBACK
                logger.warning(f"Experiment {experiment_id} failed - rolling back")
            else:
                # Inconclusive - keep in experiment mode
                logger.info(f"Experiment {experiment_id} inconclusive - maintaining experiment status")
                
            feature_version.status = new_status
            feature_version.updated_at = datetime.now()
            
            try:
                self._db.execute(
                    """
                    UPDATE feature_versions
                    SET status = ?, updated_at = ?
                    WHERE feature_id = ? AND version = ?
                    """,
                    (
                        new_status.value,
                        datetime.now().isoformat(),
                        experiment.feature_id,
                        experiment.version
                    )
                )
                self._db.commit()
                
                # Remove from active experiments
                del self._active_experiments[experiment_id]
            except Exception as e:
                logger.error(f"Error concluding experiment: {e}")
                raise

    async def get_active_version(
        self,
        feature_id: str,
        model_compatibility: Optional[Dict[str, str]] = None
    ) -> Optional[FeatureVersion]:
        """Get the active version of a feature."""
        with self._lock:
            if feature_id not in self._versions:
                return None
                
            # Find active version with compatible model dependencies
            active_versions = [
                v for v in self._versions[feature_id].values()
                if v.status == VersionStatus.ACTIVE
            ]
            
            if not active_versions:
                return None
                
            if model_compatibility:
                # Filter by model compatibility
                compatible_versions = [
                    v for v in active_versions
                    if all(
                        model in v.model_dependencies and
                        v.model_dependencies[model] == version
                        for model, version in model_compatibility.items()
                    )
                ]
                
                if compatible_versions:
                    # Return most recently updated compatible version
                    return max(compatible_versions, key=lambda v: v.updated_at)
                    
            # Return most recently updated active version
            return max(active_versions, key=lambda v: v.updated_at)

    def get_version_history(
        self,
        feature_id: str
    ) -> List[FeatureVersion]:
        """Get version history for a feature."""
        with self._lock:
            if feature_id not in self._versions:
                return []
                
            return sorted(
                self._versions[feature_id].values(),
                key=lambda v: v.created_at,
                reverse=True
            )

    async def deprecate_version(
        self,
        feature_id: str,
        version: str
    ):
        """Deprecate a feature version."""
        with self._lock:
            if feature_id not in self._versions or \
               version not in self._versions[feature_id]:
                raise ValueError("Invalid feature or version")
                
            feature_version = self._versions[feature_id][version]
            feature_version.status = VersionStatus.DEPRECATED
            feature_version.updated_at = datetime.now()
            
            try:
                self._db.execute(
                    """
                    UPDATE feature_versions
                    SET status = ?, updated_at = ?
                    WHERE feature_id = ? AND version = ?
                    """,
                    (
                        VersionStatus.DEPRECATED.value,
                        datetime.now().isoformat(),
                        feature_id,
                        version
                    )
                )
                self._db.commit()
            except Exception as e:
                logger.error(f"Error deprecating version: {e}")
                raise

    def get_experiment_results(
        self,
        experiment_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get results for a specific experiment."""
        with self._lock:
            if experiment_id not in self._active_experiments:
                # Check completed experiments in DB
                try:
                    cur = self._db.execute(
                        """
                        SELECT feature_id, version, metrics
                        FROM feature_versions
                        WHERE experiment_id = ?
                        """,
                        (experiment_id,)
                    )
                    result = cur.fetchone()
                    if result:
                        feature_id, version, metrics = result
                        return {
                            'feature_id': feature_id,
                            'version': version,
                            'metrics': json.loads(metrics),
                            'status': 'completed'
                        }
                except Exception as e:
                    logger.error(f"Error fetching experiment results: {e}")
                return None
                
            experiment = self._active_experiments[experiment_id]
            feature_version = self._versions[experiment.feature_id][experiment.version]
            return {
                'feature_id': experiment.feature_id,
                'version': experiment.version,
                'metrics': feature_version.metrics,
                'status': 'active',
                'progress': (datetime.now() - experiment.start_time) / \
                           (experiment.end_time - experiment.start_time)
            }

    def __del__(self):
        """Cleanup database connection."""
        try:
            self._db.close()
        except:
            pass

# Global version manager instance
version_manager = AIVersionManager()