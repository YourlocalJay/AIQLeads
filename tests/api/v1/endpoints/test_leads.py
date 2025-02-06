        assert data["lead_id"] == str(sample_lead.id)
        assert data["score"] == 85.5
        
    @pytest.mark.asyncio
    async def test_batch_scoring(self, sample_batch_leads):
        """Test batch lead scoring"""
        # Mock lead_service and lead_scorer
        lead_service.is_duplicate = AsyncMock(return_value=False)
        
        score_result = MagicMock(
            score=85.5,
            confidence=0.92,
            contributing_factors=[{"factor": "location", "weight": 0.7}],
            recommendations=["Follow up within 24 hours"]
        )
        lead_scorer.analyze = AsyncMock(return_value=score_result)
        
        response = client.post("/score/batch", 
                             json=[lead.dict() for lead in sample_batch_leads])
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["scores"]) == len(sample_batch_leads)
        assert len(data["errors"]) == 0
        
    @pytest.mark.asyncio
    async def test_batch_scoring_with_errors(self, sample_batch_leads):
        """Test batch scoring with some failures"""
        # Mock first lead as duplicate
        async def mock_is_duplicate(lead):
            return lead.id == sample_batch_leads[0].id
        lead_service.is_duplicate = AsyncMock(side_effect=mock_is_duplicate)
        
        # Mock scorer to fail for second lead
        async def mock_analyze(lead_data, **kwargs):
            if lead_data.id == sample_batch_leads[1].id:
                raise Exception("Scoring failed")
            return MagicMock(
                score=85.5,
                confidence=0.92,
                contributing_factors=[{"factor": "location", "weight": 0.7}],
                recommendations=["Follow up within 24 hours"]
            )
        lead_scorer.analyze = AsyncMock(side_effect=mock_analyze)
        
        response = client.post("/score/batch", 
                             json=[lead.dict() for lead in sample_batch_leads])
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["scores"]) == 1  # Only third lead successful
        assert len(data["errors"]) == 2  # First two leads failed
        
    @pytest.mark.asyncio
    async def test_component_status(self):
        """Test component status endpoint"""
        component_id = "api/v1/leads/score"
        status_info = {
            "status": "🟢 Active",
            "notes": "System operational"
        }
        tracker.get_status = MagicMock(return_value=status_info)
        
        response = client.get(f"/status/{component_id}")
        assert response.status_code == 200
        assert response.json() == status_info
        
    @pytest.mark.asyncio
    async def test_invalid_lead_data(self):
        """Test validation of invalid lead data"""
        invalid_lead = {
            "source": "test",
            "contact_info": {
                "email": "not-an-email",
                "phone": "invalid-phone",
                "preferred_contact": "email"
            },
            "preferences": {
                "property_types": ["residential"],
                "price_range": {"min": 500000.0, "max": 200000.0},  # Invalid range
                "locations": []
            }
        }
        
        response = client.post("/score", json=invalid_lead)
        assert response.status_code == 422
        
    @pytest.mark.asyncio
    async def test_error_handling(self, sample_lead):
        """Test error handling during scoring process"""
        lead_service.is_duplicate = AsyncMock(return_value=False)
        lead_scorer.analyze = AsyncMock(side_effect=Exception("Scoring failed"))
        
        response = client.post("/score", json=sample_lead.dict())
        assert response.status_code == 500
        assert "Error processing lead" in response.json()["detail"]