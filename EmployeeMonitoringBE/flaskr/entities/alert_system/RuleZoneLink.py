from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from sqlalchemy import ForeignKey

class RuleZoneLink(Entity):
    __tablename__ = "rule_zone_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("alert_rules.id"), nullable=False)
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), nullable=False)
    
