"""
Tests for Mergington High School API using AAA (Arrange-Act-Assert) pattern
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Fixture to provide a TestClient instance"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Fixture to reset activities to clean state before each test"""
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": []
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": []
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": []
        }
    }
    
    # Clear and restore activities
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Test suite for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        ARRANGE: Prepare test data
        ACT: Call GET /activities
        ASSERT: Verify all activities are returned with correct structure
        """
        # Arrange (state is set up by reset_activities fixture)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_returns_correct_activity_structure(self, client, reset_activities):
        """
        ARRANGE: N/A (using fixture state)
        ACT: Call GET /activities and check activity structure
        ASSERT: Verify each activity has required fields
        """
        # Arrange (implicit via fixture)
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        chess_club = activities_data["Chess Club"]
        
        # Assert
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client, reset_activities):
        """
        ARRANGE: Prepare activity and email
        ACT: Call signup endpoint with valid data
        ASSERT: Verify student is added to participants
        """
        # Arrange
        activity_name = "Chess Club"
        email = "alice@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in activities[activity_name]["participants"]
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """
        ARRANGE: Prepare non-existent activity and email
        ACT: Call signup endpoint
        ASSERT: Verify 404 error is returned
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "bob@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_prevents_double_registration(self, client, reset_activities):
        """
        ARRANGE: Sign up a student first, then attempt to sign up again
        ACT: Call signup endpoint with same email twice
        ASSERT: Verify second attempt fails with 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "charlie@mergington.edu"
        
        # Act - First signup (should succeed)
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act - Second signup (should fail)
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
        # Verify participant list contains email only once
        assert activities[activity_name]["participants"].count(email) == 1
    
    def test_signup_multiple_students_same_activity(self, client, reset_activities):
        """
        ARRANGE: Prepare multiple students and activity
        ACT: Sign up multiple students for same activity
        ASSERT: Verify all students are in participants list
        """
        # Arrange
        activity_name = "Gym Class"
        emails = ["diane@mergington.edu", "evan@mergington.edu", "fiona@mergington.edu"]
        
        # Act
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert
        assert len(activities[activity_name]["participants"]) == 3
        for email in emails:
            assert email in activities[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Test suite for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, client, reset_activities):
        """
        ARRANGE: Sign up a student, then prepare to unregister
        ACT: Call unregister endpoint
        ASSERT: Verify student is removed from participants
        """
        # Arrange
        activity_name = "Chess Club"
        email = "grace@mergington.edu"
        # First, sign up
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        assert email in activities[activity_name]["participants"]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_activity_not_found(self, client, reset_activities):
        """
        ARRANGE: Prepare non-existent activity and email
        ACT: Call unregister endpoint
        ASSERT: Verify 404 error is returned
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "henry@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_student_not_registered(self, client, reset_activities):
        """
        ARRANGE: Prepare activity and email of non-registered student
        ACT: Call unregister endpoint
        ASSERT: Verify 400 error is returned
        """
        # Arrange
        activity_name = "Programming Class"
        email = "iris@mergington.edu"
        # Verify email is not registered
        assert email not in activities[activity_name]["participants"]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_specific_student_keeps_others(self, client, reset_activities):
        """
        ARRANGE: Sign up multiple students and select one to unregister
        ACT: Unregister one student
        ASSERT: Verify only that student is removed, others remain
        """
        # Arrange
        activity_name = "Gym Class"
        emails = ["jack@mergington.edu", "kate@mergington.edu", "leo@mergington.edu"]
        for email in emails:
            client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": emails[1]}  # Remove kate
        )
        
        # Assert
        assert response.status_code == 200
        assert len(activities[activity_name]["participants"]) == 2
        assert emails[0] in activities[activity_name]["participants"]  # jack still there
        assert emails[1] not in activities[activity_name]["participants"]  # kate removed
        assert emails[2] in activities[activity_name]["participants"]  # leo still there
