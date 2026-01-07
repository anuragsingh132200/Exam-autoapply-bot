"""
Field Learning Service
Learns field mappings from successful form fills for auto-suggestions.
"""
from typing import Optional
from datetime import datetime
from beanie import PydanticObjectId

from app.models.field_mapping import FieldMapping


class FieldLearnerService:
    """
    Field learning service that stores and retrieves learned field mappings.
    Improves over time by learning from successful form fills.
    """
    
    async def learn_mapping(
        self,
        field_label: str,
        mapped_to: str,
        exam_slug: str
    ) -> FieldMapping:
        """
        Learn or update a field mapping.
        
        Args:
            field_label: The form field label text
            mapped_to: The user data path this maps to
            exam_slug: The exam where this mapping was used
        
        Returns:
            The created or updated FieldMapping
        """
        # Check if mapping already exists
        existing = await FieldMapping.find_one(
            FieldMapping.field_label == field_label.lower().strip()
        )
        
        if existing:
            # Update existing mapping
            existing.times_used += 1
            existing.last_used_at = datetime.utcnow()
            
            # Add exam if not already seen
            if exam_slug not in existing.exams_seen:
                existing.exams_seen.append(exam_slug)
            
            # Increase confidence based on usage
            existing.confidence = min(1.0, existing.confidence + 0.1)
            
            await existing.save()
            return existing
        
        # Create new mapping
        mapping = FieldMapping(
            field_label=field_label.lower().strip(),
            mapped_to=mapped_to,
            exams_seen=[exam_slug],
            confidence=0.5,
            times_used=1
        )
        await mapping.insert()
        return mapping
    
    async def suggest_mapping(
        self,
        field_label: str,
        user_data_keys: list[str]
    ) -> Optional[str]:
        """
        Suggest a mapping for a field label based on learned patterns.
        
        Args:
            field_label: The form field label to match
            user_data_keys: Available user data field names
        
        Returns:
            Suggested user data key, or None if no good match
        """
        # Look for exact match in learned mappings
        label_lower = field_label.lower().strip()
        
        mapping = await FieldMapping.find_one(
            FieldMapping.field_label == label_lower
        )
        
        if mapping and mapping.confidence >= 0.5:
            if mapping.mapped_to in user_data_keys:
                return mapping.mapped_to
        
        # Try partial matching
        mappings = await FieldMapping.find(
            {"confidence": {"$gte": 0.5}}
        ).sort("-confidence").limit(50).to_list()
        
        for m in mappings:
            # Check if field label contains the learned label or vice versa
            if m.field_label in label_lower or label_lower in m.field_label:
                if m.mapped_to in user_data_keys:
                    return m.mapped_to
        
        # Fallback: simple keyword matching
        label_words = set(label_lower.replace("_", " ").replace("-", " ").split())
        
        for key in user_data_keys:
            key_words = set(key.lower().replace("_", " ").replace("-", " ").split())
            if label_words & key_words:  # Intersection
                return key
        
        return None
    
    async def get_all_mappings(self) -> list[FieldMapping]:
        """Get all learned mappings sorted by confidence."""
        return await FieldMapping.find().sort("-confidence").to_list()
    
    async def delete_mapping(self, mapping_id: str) -> bool:
        """Delete a learned mapping."""
        mapping = await FieldMapping.get(PydanticObjectId(mapping_id))
        if mapping:
            await mapping.delete()
            return True
        return False


# Global field learner instance
field_learner = FieldLearnerService()
