import pytest
from datetime import datetime
from src.aggregator.components.pricing_engine import PricingEngine
from src.config import Settings

@pytest.fixture
def settings():
    return Settings()

@pytest.fixture
def pricing_engine(settings):
    return PricingEngine(settings)

@pytest.fixture
def sample_lead_data():
    return {
        'type': 'standard',
        'industry': 'technology',
        'location': 'San Francisco',
        'created_at': datetime.utcnow().isoformat(),
        'verification_status': {
            'email': 1.0,
            'phone': 0.8,
            'address': 0.9
        },
        'enrichment_data': {
            'company_size': True,
            'revenue': True,
            'social_presence': True
        },
        'fraud_risk_scores': {
            'identity': 0.1,
            'location': 0.2,
            'behavior': 0.1
        },
        'subscription_tier': 'premium'
    }

@pytest.mark.asyncio
async def test_basic_price_calculation(pricing_engine, sample_lead_data):
    """Test basic price calculation functionality."""
    price = await pricing_engine.calculate_price(sample_lead_data)
    assert isinstance(price, float)
    assert price > 0

@pytest.mark.asyncio
async def test_quality_impact(pricing_engine, sample_lead_data):
    """Test quality score impact on price."""
    # Test high quality lead
    high_quality = sample_lead_data.copy()
    high_quality['verification_status'] = {'email': 1.0, 'phone': 1.0, 'address': 1.0}
    high_price = await pricing_engine.calculate_price(high_quality)
    
    # Test low quality lead
    low_quality = sample_lead_data.copy()
    low_quality['verification_status'] = {'email': 0.2, 'phone': 0.3, 'address': 0.1}
    low_price = await pricing_engine.calculate_price(low_quality)
    
    assert high_price > low_price

@pytest.mark.asyncio
async def test_subscription_discount(pricing_engine, sample_lead_data):
    """Test subscription tier impact on price."""
    # Test premium tier
    premium = sample_lead_data.copy()
    premium['subscription_tier'] = 'premium'
    premium_price = await pricing_engine.calculate_price(premium)
    
    # Test basic tier
    basic = sample_lead_data.copy()
    basic['subscription_tier'] = 'basic'
    basic_price = await pricing_engine.calculate_price(basic)
    
    assert premium_price < basic_price

@pytest.mark.asyncio
async def test_price_limits(pricing_engine, sample_lead_data):
    """Test price limit enforcement."""
    price = await pricing_engine.calculate_price(sample_lead_data)
    assert price >= pricing_engine.settings.MIN_PRICE
    assert price <= pricing_engine.settings.MAX_PRICE

@pytest.mark.asyncio
async def test_invalid_data_handling(pricing_engine):
    """Test handling of invalid input data."""
    invalid_data = {}
    price = await pricing_engine.calculate_price(invalid_data)
    assert isinstance(price, float)
    assert price > 0  # Should return fallback price

@pytest.mark.asyncio
async def test_fraud_risk_impact(pricing_engine, sample_lead_data):
    """Test fraud risk impact on price."""
    # Test high risk lead
    high_risk = sample_lead_data.copy()
    high_risk['fraud_risk_scores'] = {
        'identity': 0.8,
        'location': 0.7,
        'behavior': 0.9
    }
    high_risk_price = await pricing_engine.calculate_price(high_risk)
    
    # Test low risk lead
    low_risk = sample_lead_data.copy()
    low_risk['fraud_risk_scores'] = {
        'identity': 0.1,
        'location': 0.2,
        'behavior': 0.1
    }
    low_risk_price = await pricing_engine.calculate_price(low_risk)
    
    assert low_risk_price > high_risk_price

@pytest.mark.asyncio
async def test_enrichment_impact(pricing_engine, sample_lead_data):
    """Test data enrichment impact on price."""
    # Test fully enriched lead
    enriched = sample_lead_data.copy()
    enriched['enrichment_data'] = {
        'company_size': True,
        'revenue': True,
        'social_presence': True,
        'industry_details': True,
        'technographics': True
    }
    enriched_price = await pricing_engine.calculate_price(enriched)
    
    # Test minimal enrichment
    basic = sample_lead_data.copy()
    basic['enrichment_data'] = {
        'company_size': True
    }
    basic_price = await pricing_engine.calculate_price(basic)
    
    assert enriched_price > basic_price

@pytest.mark.asyncio
async def test_market_adjustment(pricing_engine, sample_lead_data):
    """Test market conditions impact on price."""
    # Test different market conditions
    locations = ['San Francisco', 'New York', 'Chicago']
    prices = []
    
    for location in locations:
        lead = sample_lead_data.copy()
        lead['location'] = location
        price = await pricing_engine.calculate_price(lead)
        prices.append(price)
    
    # Verify prices vary by market
    assert len(set(prices)) > 1

@pytest.mark.asyncio
async def test_demand_factor(pricing_engine, sample_lead_data):
    """Test demand impact on price."""
    # Test different industries
    industries = ['technology', 'healthcare', 'finance']
    prices = []
    
    for industry in industries:
        lead = sample_lead_data.copy()
        lead['industry'] = industry
        price = await pricing_engine.calculate_price(lead)
        prices.append(price)
    
    # Verify prices vary by industry demand
    assert len(set(prices)) > 1

@pytest.mark.asyncio
async def test_completeness_impact(pricing_engine, sample_lead_data):
    """Test data completeness impact on price."""
    # Test complete lead
    complete_price = await pricing_engine.calculate_price(sample_lead_data)
    
    # Test incomplete lead
    incomplete = sample_lead_data.copy()
    del incomplete['industry']
    del incomplete['enrichment_data']
    incomplete_price = await pricing_engine.calculate_price(incomplete)
    
    assert complete_price > incomplete_price

@pytest.mark.asyncio
async def test_cache_behavior(pricing_engine, sample_lead_data):
    """Test caching behavior for market and demand data."""
    # First calculation should populate cache
    first_price = await pricing_engine.calculate_price(sample_lead_data)
    
    # Modify internal cache timestamps
    pricing_engine.market_cache = {}
    pricing_engine.demand_cache = {}
    
    # Second calculation should use fresh cache
    second_price = await pricing_engine.calculate_price(sample_lead_data)
    
    # Prices should be similar despite cache reset
    assert abs(first_price - second_price) < 0.01

@pytest.mark.asyncio
async def test_batch_pricing(pricing_engine):
    """Test batch price calculation."""
    leads = [
        sample_lead_data(),
        sample_lead_data(),
        sample_lead_data()
    ]
    
    # Calculate prices in batch
    prices = await asyncio.gather(*[
        pricing_engine.calculate_price(lead)
        for lead in leads
    ])
    
    assert len(prices) == len(leads)
    assert all(isinstance(p, float) for p in prices)
    assert all(p > 0 for p in prices)