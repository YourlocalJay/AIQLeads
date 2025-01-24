"lat": 40.7128, "lng": -74.0060}
            }
        }]
    }

    with patch.object(
        validation_service, 
        "_geocode_address",
        return_value=mock_geocode_response
    ):
        results = await validation_service.validate_contact(lead_data)
        
        assert "email" in results
        assert results["email"].is_valid
        
        assert "phone" in results
        assert results["phone"].is_valid
        
        assert "address" in results
        assert results["address"].is_valid