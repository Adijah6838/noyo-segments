import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
from datetime import date

# Setup Test Database (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    # Clear tables before every test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_create_person():
    response = client.post("/people/", json={"name": "Alice", "email": "alice@example.com"})
    assert response.status_code == 201
    assert response.json()["name"] == "Alice"

def test_create_person_duplicate_email():
    client.post("/people/", json={"name": "Alice", "email": "alice@example.com"})
    response = client.post("/people/", json={"name": "Bob", "email": "alice@example.com"})
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_create_segment_invalid_dates():
    response = client.post("/segments/", json={
        "name": "Invalid Segment",
        "start_date": "2024-12-31",
        "end_date": "2024-01-01" # End before start
    })
    assert response.status_code == 422
    assert "end_date must be greater than" in response.text

def test_assign_segment():
    # Create person and segment
    client.post("/people/", json={"name": "Alice", "email": "alice@example.com"})
    client.post("/segments/", json={"name": "Q1 2024", "start_date": "2024-01-01", "end_date": "2024-03-31"})
    
    # Assign
    response = client.post("/people/1/segments/", json={"segment_id": 1})
    assert response.status_code == 201
    assert len(response.json()["segments"]) == 1

def test_prevent_overlapping_assignments():
    # Create person and two overlapping segments
    client.post("/people/", json={"name": "Alice", "email": "alice@example.com"})
    client.post("/segments/", json={"name": "Q1 2024", "start_date": "2024-01-01", "end_date": "2024-03-31"})
    client.post("/segments/", json={"name": "Q1 Special", "start_date": "2024-02-01", "end_date": "2024-04-15"})
    
    # Assign first segment
    client.post("/people/1/segments/", json={"segment_id": 1})
    
    # Try to assign overlapping segment
    response = client.post("/people/1/segments/", json={"segment_id": 2})
    assert response.status_code == 400
    assert "overlaps" in response.json()["detail"]

def test_pagination():
    # Create 15 people
    for i in range(15):
        client.post("/people/", json={"name": f"Person {i}", "email": f"p{i}@example.com"})
        
    response = client.get("/people/?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 15
    assert len(data["data"]) == 10
    
    response = client.get("/people/?page=2&limit=10")
    assert len(response.json()["data"]) == 5
