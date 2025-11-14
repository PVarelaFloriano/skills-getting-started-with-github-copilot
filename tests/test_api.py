"""
Tests for the High School Activities API endpoints.
"""

import pytest
from fastapi import status


class TestGetActivities:
    """Test cases for GET /activities endpoint."""

    def test_get_activities_success(self, client, reset_activities):
        """Test successful retrieval of activities."""
        response = client.get("/activities")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check that we get the expected activities
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Check structure of an activity
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_structure(self, client, reset_activities):
        """Test that activities have the correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Test cases for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, reset_activities, sample_activity_name, sample_email):
        """Test successful signup for an activity."""
        response = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": sample_email}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert sample_email in data["message"]
        assert sample_activity_name in data["message"]
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert sample_email in activities[sample_activity_name]["participants"]

    def test_signup_activity_not_found(self, client, reset_activities, sample_email):
        """Test signup for non-existent activity."""
        response = client.post(
            "/activities/NonExistentActivity/signup",
            params={"email": sample_email}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_already_registered(self, client, reset_activities, sample_activity_name, existing_participant_email):
        """Test signup for activity when already registered."""
        response = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": existing_participant_email}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()

    def test_signup_with_special_characters_in_activity_name(self, client, reset_activities, sample_email):
        """Test signup with URL encoding in activity name."""
        activity_name = "Chess Club"  # Contains space
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_signup_with_special_characters_in_email(self, client, reset_activities, sample_activity_name):
        """Test signup with special characters in email."""
        email = "test+tag@mergington.edu"
        response = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[sample_activity_name]["participants"]


class TestUnregisterFromActivity:
    """Test cases for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client, reset_activities, sample_activity_name, existing_participant_email):
        """Test successful unregistration from an activity."""
        # Verify participant is initially registered
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert existing_participant_email in activities[sample_activity_name]["participants"]
        
        # Unregister the participant
        response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": existing_participant_email}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert existing_participant_email in data["message"]
        assert sample_activity_name in data["message"]
        
        # Verify the participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert existing_participant_email not in activities[sample_activity_name]["participants"]

    def test_unregister_activity_not_found(self, client, reset_activities, sample_email):
        """Test unregistration from non-existent activity."""
        response = client.delete(
            "/activities/NonExistentActivity/unregister",
            params={"email": sample_email}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_unregister_not_registered(self, client, reset_activities, sample_activity_name, sample_email):
        """Test unregistration when not registered for activity."""
        response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": sample_email}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "not registered" in data["detail"].lower()

    def test_unregister_with_special_characters(self, client, reset_activities):
        """Test unregistration with special characters in activity name and email."""
        # First, add a participant with special characters
        email = "test+tag@mergington.edu"
        activity_name = "Chess Club"
        
        # Sign up first
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == status.HTTP_200_OK
        
        # Then unregister
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == status.HTTP_200_OK


class TestRootEndpoint:
    """Test cases for the root endpoint."""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index.html."""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == "/static/index.html"


class TestIntegrationWorkflows:
    """Test complete workflows combining multiple endpoints."""

    def test_signup_and_unregister_workflow(self, client, reset_activities, sample_activity_name, sample_email):
        """Test complete signup and unregister workflow."""
        # 1. Check initial state
        activities_response = client.get("/activities")
        initial_activities = activities_response.json()
        initial_participants = initial_activities[sample_activity_name]["participants"].copy()
        
        # 2. Sign up for activity
        signup_response = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": sample_email}
        )
        assert signup_response.status_code == status.HTTP_200_OK
        
        # 3. Verify signup worked
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert sample_email in activities[sample_activity_name]["participants"]
        assert len(activities[sample_activity_name]["participants"]) == len(initial_participants) + 1
        
        # 4. Unregister from activity
        unregister_response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": sample_email}
        )
        assert unregister_response.status_code == status.HTTP_200_OK
        
        # 5. Verify unregistration worked
        activities_response = client.get("/activities")
        final_activities = activities_response.json()
        assert sample_email not in final_activities[sample_activity_name]["participants"]
        assert len(final_activities[sample_activity_name]["participants"]) == len(initial_participants)

    def test_multiple_participants_same_activity(self, client, reset_activities, sample_activity_name):
        """Test adding multiple participants to the same activity."""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Sign up multiple participants
        for email in emails:
            response = client.post(
                f"/activities/{sample_activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == status.HTTP_200_OK
        
        # Verify all participants are registered
        activities_response = client.get("/activities")
        activities = activities_response.json()
        participants = activities[sample_activity_name]["participants"]
        
        for email in emails:
            assert email in participants
        
        # Unregister one participant
        response = client.delete(
            f"/activities/{sample_activity_name}/unregister",
            params={"email": emails[0]}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify only that participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        participants = activities[sample_activity_name]["participants"]
        
        assert emails[0] not in participants
        assert emails[1] in participants
        assert emails[2] in participants