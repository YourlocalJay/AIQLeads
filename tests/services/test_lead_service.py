    @pytest.mark.asyncio
    async def test_cache_metrics(self, lead_service, sample_lead):
        """Test cache performance metrics"""
        # Simulate some cache hits and misses
        lead_service.cache_hits = 10
        lead_service.cache_misses = 5

        metrics = await lead_service.get_cache_metrics()
        assert metrics["cache_hits"] == 10
        assert metrics["cache_misses"] == 5
        assert metrics["hit_ratio"] == 0.6667  # 10/(10+5)

    @pytest.mark.asyncio
    async def test_clear_cache(self, lead_service):
        """Test cache clearing functionality"""
        # Add some items to cache
        async with lead_service._cache_lock:
            lead_service._local_cache["test1"] = "value1"
            lead_service._local_cache["test2"] = "value2"

        # Clear cache
        await lead_service.clear_cache()

        # Verify local cache is empty
        assert len(lead_service._local_cache) == 0
        # Verify Redis was cleared
        lead_service.redis.flushdb.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_concurrency(self, lead_service):
        """Test concurrent cache access"""
        async def concurrent_access(key):
            async with lead_service._cache_lock:
                lead_service._local_cache[key] = "value"
                await asyncio.sleep(0.1)  # Simulate work
                return lead_service._local_cache[key]

        # Run multiple cache operations concurrently
        tasks = [
            concurrent_access(f"key{i}") 
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)

        # Verify all operations completed successfully
        assert len(results) == 5
        assert all(v == "value" for v in results)

    @pytest.mark.asyncio
    async def test_fingerprint_generation(self, lead_service, sample_lead):
        """Test lead fingerprint generation"""
        # Generate fingerprint
        fingerprint1 = await lead_service._generate_fingerprint(sample_lead)
        
        # Should be deterministic
        fingerprint2 = await lead_service._generate_fingerprint(sample_lead)
        assert fingerprint1 == fingerprint2
        
        # Should be different for different leads
        modified_lead = sample_lead.copy()
        modified_lead.contact_info.email = "different@example.com"
        different_fingerprint = await lead_service._generate_fingerprint(modified_lead)
        assert fingerprint1 != different_fingerprint

    @pytest.mark.asyncio
    async def test_error_handling(self, lead_service, sample_lead):
        """Test error handling in various scenarios"""
        # Test database error
        lead_service.database.fetchrow = AsyncMock(side_effect=Exception("DB Error"))
        is_duplicate = await lead_service.is_duplicate(sample_lead)
        assert not is_duplicate  # Should fail safely

        # Test Redis error
        lead_service.redis.exists = AsyncMock(side_effect=Exception("Redis Error"))
        is_duplicate = await lead_service.is_duplicate(sample_lead)
        assert not is_duplicate  # Should fail safely

        # Test phone parsing error
        with patch('phonenumbers.parse', side_effect=NumberParseException(0, "Error")):
            normalized = await lead_service._normalize_phone("invalid")
            assert normalized == ""  # Should handle error gracefully