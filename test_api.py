import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
friend_id_alice = None
friend_id_roman = None
def test_create_friend_with_valid_photo():
    test_file_content = b"\xFF\xD8\xFF\xE0" 

    files = {'photo': ('alice.jpg', test_file_content, 'image/jpeg')}
    
    data = {
        "name": "Тест-Аліса",
        "profession": "Тестувальник",
        "profession_description": "Працює з фейковими даними"
    }

    response =  client.post("/friends", data=data, files=files)
    friend_id_alice1 = response.json()['FriendID']
    global friend_id_alice
    friend_id_alice = friend_id_alice1
    assert response.status_code == 200
    assert 'PhotoUrl' in response.json()


def test_invalid_file():
    test_file_content = b"\xFF\xD8\xFF\xE0"
    files = {'text': ('alice.txt', test_file_content, 'txt')}
    data = {
        "name": "Тест-Аліса",
        "profession": "Тестувальник",
        "profession_description": "Працює з фейковими даними"
    }

    response =  client.post("/friends", data=data, files=files)
    assert response.status_code == 422


def test_invalid_data():
    test_file_content = b"\xFF\xD8\xFF\xE0" 

    files = {'photo': ('alice.jpg', test_file_content, 'image/jpeg')}
    data = {
        "profession": "Тестувальник",
        "profession_description": "Працює з фейковими даними"
    }
    response =  client.post("/friends", data=data, files=files)
    assert response.status_code == 422

def test_get_all_records():
    test_file_content = b"\xFF\xD8\xFF\xE0"
    files2 = {'photo': ('roman.jpg', test_file_content, 'image/jpeg')}
    data2 = {
        "name": "Тест-Роман",
        "profession": "Теж тестувальник виходить",
        "profession_description": "Робить вигляд що працює"
    }
    friend_data = client.post("/friends", data=data2, files=files2)
    friend_id_roman1 = friend_data.json()['FriendID']
    global friend_id_roman
    friend_id_roman = friend_id_roman1
    response = client.get('friends')
    assert response.status_code == 200
    friends_list = response.json()
    assert isinstance(friends_list, list)
    added_names = ["Тест-Аліса", "Тест-Роман"]

    retrieved_names = [f['Name'] for f in friends_list]
    assert added_names[0] in retrieved_names
    assert added_names[1] in retrieved_names


def test_delete_friend():
    response1 = client.delete(f'/friends/delete/{friend_id_alice}')
    response2 = client.delete(f'/friends/delete/{friend_id_roman}')
    assert response1.status_code == 200
    assert response2.status_code == 200