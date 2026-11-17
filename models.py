from sqlalchemy import Column, Integer, String, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Person(Base):
    __tablename__ = "people"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    
    segments = relationship("SegmentAssignment", back_populates="person")

class Segment(Base):
    __tablename__ = "segments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    assignments = relationship("SegmentAssignment", back_populates="segment")

class SegmentAssignment(Base):
    __tablename__ = "segment_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)
    
    __table_args__ = (UniqueConstraint('person_id', 'segment_id', name='uq_person_segment'),)

    person = relationship("Person", back_populates="segments")
    segment = relationship("Segment", back_populates="assignments")