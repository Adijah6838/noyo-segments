from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from database import engine, get_db
from models import Base, Person, Segment, SegmentAssignment
from schemas import (
    PersonCreate, PersonUpdate, PersonResponse,
    SegmentCreate, SegmentResponse, SegmentAssignmentCreate,
    PaginatedPeople
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Noyo Segments API")

# --- People Endpoints ---

@app.post("/people/", response_model=PersonResponse, status_code=201)
def create_person(person: PersonCreate, db: Session = Depends(get_db)):
    db_person = db.query(Person).filter(Person.email == person.email).first()
    if db_person:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_person = Person(name=person.name, email=person.email)
    db.add(new_person)
    db.commit()
    db.refresh(new_person)
    return new_person

@app.get("/people/", response_model=PaginatedPeople)
def list_people(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    total = db.query(Person).count()
    people = db.query(Person).offset(offset).limit(limit).all()
    
    return {"total": total, "page": page, "limit": limit, "data": people}

@app.get("/people/{person_id}", response_model=PersonResponse)
def get_person(person_id: int, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

@app.patch("/people/{person_id}", response_model=PersonResponse)
def update_person(person_id: int, updates: PersonUpdate, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    if updates.email and updates.email != person.email:
        existing = db.query(Person).filter(Person.email == updates.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(person, key, value)
        
    db.commit()
    db.refresh(person)
    return person

@app.delete("/people/{person_id}", status_code=204)
def delete_person(person_id: int, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Delete assignments first to prevent FK constraint errors
    db.query(SegmentAssignment).filter(SegmentAssignment.person_id == person_id).delete()
    db.delete(person)
    db.commit()
    return None

# --- Segment Endpoints ---

@app.post("/segments/", response_model=SegmentResponse, status_code=201)
def create_segment(segment: SegmentCreate, db: Session = Depends(get_db)):
    # Validation is handled by Pydantic's field_validator
    db_segment = db.query(Segment).filter(Segment.name == segment.name).first()
    if db_segment:
        raise HTTPException(status_code=400, detail="Segment name already exists")
        
    new_segment = Segment(
        name=segment.name,
        start_date=segment.start_date,
        end_date=segment.end_date
    )
    db.add(new_segment)
    db.commit()
    db.refresh(new_segment)
    return new_segment

@app.post("/people/{person_id}/segments/", response_model=PersonResponse, status_code=201)
def assign_person_to_segment(
    person_id: int, 
    assignment: SegmentAssignmentCreate, 
    db: Session = Depends(get_db)
):
    # Use a transaction to ensure consistency
    try:
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
            
        segment = db.query(Segment).filter(Segment.id == assignment.segment_id).first()
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")
            
        # Check if assignment already exists
        existing = db.query(SegmentAssignment).filter(
            SegmentAssignment.person_id == person_id,
            SegmentAssignment.segment_id == segment.id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Person is already assigned to this segment")
            
        # Check for overlapping segment assignments (if prohibited by business rules)
        # For example, if a person is assigned to 'Q1 2024' they shouldn't be in 'Q1 2024 Special'
        # We check if the new segment dates overlap with any segment the person is already in.
        
        overlapping = db.query(SegmentAssignment).join(Segment).filter(
            SegmentAssignment.person_id == person_id,
            Segment.start_date <= segment.end_date,
            Segment.end_date >= segment.start_date
        ).first()
        
        if overlapping:
            # Note: Depending on the exact business rule, overlapping might be allowed.
            # The prompt says "Prevent overlapping assignments where prohibited."
            # We'll prohibit it for this implementation.
            raise HTTPException(
                status_code=400, 
                detail="This segment overlaps with an existing segment assignment for this person."
            )

        new_assignment = SegmentAssignment(person_id=person_id, segment_id=segment.id)
        db.add(new_assignment)
        db.commit()
        db.refresh(person)
        
        return person
    except Exception as e:
        db.rollback()
        raise e
