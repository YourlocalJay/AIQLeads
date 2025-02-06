from pydantic import BaseModel, EmailStr, Field, validator, constr, root_validator
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
import re

# Precompiled regex for better performance
PHONE_REGEX = re.compile(r'^\+?\d{1,3}?[-.\s]?\d{1,14}$')

class LeadStatus(str, Enum):
    """Enum defining possible lead statuses."""
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    CONVERTED = "converted"
    INACTIVE = "inactive"

# 📌 Contact Info Model
class ContactInfo(BaseModel):
    email: Optional[EmailStr]
    phone: Optional[constr(strip_whitespace=True, regex=PHONE_REGEX.pattern)]
    preferred_contact: Optional[str] = "email"
    best_time: Optional[str]

    @validator("phone")
    def validate_phone(cls, v):
        """Validate phone format and strip unnecessary characters."""
        if v and not PHONE_REGEX.match(v):
            raise ValueError("Invalid phone number format.")
        return v

# 📌 Lead Preferences Model
class LeadPreferences(BaseModel):
    property_types: List[str] = []
    price_range: Dict[str, float] = Field(default_factory=lambda: {"min": 0.0, "max": 0.0})
    locations: List[str] = []
    timeline: Optional[str]
    financing_type: Optional[str]

    @validator("price_range")
    def validate_price_range(cls, v):
        """Ensure minimum price is less than the maximum price."""
        if v["min"] >= v["max"]:
            raise ValueError("Minimum price must be less than maximum price.")
        return v

# 📌 Lead History Model
class LeadHistory(BaseModel):
    first_contact: datetime
    last_contact: datetime
    total_interactions: int = Field(ge=0, default=0)
    engagement_score: float = Field(ge=0, le=100, default=0.0)
    previous_purchases: int = Field(ge=0, default=0)
    notes: List[str] = []

    @root_validator(pre=True)
    def validate_contact_dates(cls, values):
        """Ensure last_contact is after first_contact."""
        first_contact, last_contact = values.get("first_contact"), values.get("last_contact")
        if first_contact and last_contact and last_contact < first_contact:
            raise ValueError("Last contact must be after first contact.")
        return values

# 📌 Lead Model
class Lead(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    source: str
    status: LeadStatus = Field(default=LeadStatus.NEW)
    contact_info: ContactInfo
    preferences: LeadPreferences
    history: Optional[LeadHistory] = None
    metadata: Dict = Field(default_factory=dict)

    class Config:
        """Model configuration settings."""
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    def update_timestamp(self):
        """Update the last modified timestamp."""
        self.updated_at = datetime.utcnow()

    def update_status(self, new_status: LeadStatus):
        """Update the lead status and timestamp."""
        self.status = new_status
        self.update_timestamp()

    def add_note(self, note: str):
        """Add a note to the lead history and update interaction count."""
        if not self.history:
            self.history = LeadHistory(
                first_contact=self.created_at,
                last_contact=datetime.utcnow(),
                total_interactions=0
            )
        self.history.notes.append(note)
        self.history.total_interactions += 1
        self.history.last_contact = datetime.utcnow()
        self.update_timestamp()

    def record_interaction(self, engagement_increase: float = 5.0):
        """Log an interaction with the lead, increasing engagement score."""
        if not self.history:
            self.history = LeadHistory(
                first_contact=self.created_at,
                last_contact=datetime.utcnow(),
                total_interactions=1,
                engagement_score=engagement_increase
            )
        else:
            self.history.total_interactions += 1
            self.history.engagement_score = min(100, self.history.engagement_score + engagement_increase)
            self.history.last_contact = datetime.utcnow()
        self.update_timestamp()

    @classmethod
    def from_dict(cls, data: dict) -> "Lead":
        """Create a Lead instance from a dictionary."""
        for field in ["id", "created_at", "updated_at"]:
            if data.get(field) and isinstance(data[field], str):
                if field == "id":
                    data[field] = UUID(data[field])
                else:
                    data[field] = datetime.fromisoformat(data[field])
        return cls(**data)
