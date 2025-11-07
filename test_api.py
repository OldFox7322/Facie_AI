import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Global variables to store created friend IDs for reuse across tests
friend_id_alice = None
friend_id_roman = None


# =====================================================
# Test: Create a new friend with a valid JPEG photo file
# =====================================================
def test_create_friend_with_valid_photo():
    # Simulated binary JPEG file content
    test_file_content = b"\xFF\xD8\xFF\xE0"

    # Prepare multipart/form-data for upload
    files = {'photo': ('alice.jpg', test_file_content, 'image/jpeg')}
    data = {
        "name": "Тест-Аліса",
        "profession": "Тестувальник",
        "profession_description": "Працює з фейковими даними"
    }

    # Send POST request to create friend
    response = client.post("/friends", data=data, files=files)

    # Extract created FriendID for later use
    friend_id_alice1 = response.json()['FriendID']
    global friend_id_alice
    friend_id_alice = friend_id_alice1

    # Check response
    assert response.status_code == 200
    assert 'PhotoUrl' in response.json()


# ============================================================
# Test: Attempt to upload invalid file (non-image type)
# ============================================================
def test_invalid_file():
    test_file_content = b"\xFF\xD8\xFF\xE0"
    # Wrong field name and incorrect MIME type
    files = {'text': ('alice.txt', test_file_content, 'txt')}
    data = {
        "name": "Тест-Аліса",
        "profession": "Тестувальник",
        "profession_description": "Працює з фейковими даними"
    }

    # Expecting validation error from FastAPI
    response = client.post("/friends", data=data, files=files)
    assert response.status_code == 422


# ============================================================
# Test: Attempt to create friend with missing required fields
# ============================================================
def test_invalid_data():
    test_file_content = b"\xFF\xD8\xFF\xE0" 

    files = {'photo': ('alice.jpg', test_file_content, 'image/jpeg')}
    # Missing the 'name' field
    data = {
        "profession": "Тестувальник",
        "profession_description": "Працює з фейковими даними"
    }
    response = client.post("/friends", data=data, files=files)
    assert response.status_code == 422


# ============================================================
# Test: Get all friend records and verify that created ones exist
# ============================================================
def test_get_all_records():
    # Create another friend record
    test_file_content = b"\xFF\xD8\xFF\xE0"
    files2 = {'photo': ('roman.jpg', test_file_content, 'image/jpeg')}
    data2 = {
        "name": "Тест-Роман",
        "profession": "Теж тестувальник виходить",
        "profession_description": "Робить вигляд що працює"
    }

    # Add friend and store ID
    friend_data = client.post("/friends", data=data2, files=files2)
    friend_id_roman1 = friend_data.json()['FriendID']
    global friend_id_roman
    friend_id_roman = friend_id_roman1

    # Retrieve all friends from the API
    response = client.get('friends')
    assert response.status_code == 200

    # Validate structure and data
    friends_list = response.json()
    assert isinstance(friends_list, list)
    added_names = ["Тест-Аліса", "Тест-Роман"]
    retrieved_names = [f['Name'] for f in friends_list]

    # Verify that both friends exist in the response
    assert added_names[0] in retrieved_names
    assert added_names[1] in retrieved_names


# ============================================================
# Test: Delete both previously created friends
# ============================================================
def test_delete_friend():
    # Delete both records using stored IDs
    response1 = client.delete(f'/friends/delete/{friend_id_alice}')
    response2 = client.delete(f'/friends/delete/{friend_id_roman}')

    # Validate both deletions were successful
    assert response1.status_code == 200
    assert response2.status_code == 200
