"""Unit тесты для базы данных лиц."""

import pytest
import tempfile
import shutil
import numpy as np
from pathlib import Path
from watchdog_face_detection.face_database import FaceDatabase


class TestFaceDatabase:
    """Тесты для FaceDatabase."""

    @pytest.fixture
    def temp_db(self):
        """Создает временную базу данных для тестов."""
        temp_dir = tempfile.mkdtemp()
        db = FaceDatabase(database_path=temp_dir)
        yield db
        shutil.rmtree(temp_dir)

    def test_database_init(self, temp_db):
        """Тест инициализации базы данных."""
        assert temp_db.database_path.exists()
        assert temp_db.embeddings_dir.exists()
        assert isinstance(temp_db.faces, dict)

    def test_add_face(self, temp_db):
        """Тест добавления лица."""
        person_id = "test_person_1"
        name = "Test Person"
        embedding = np.random.rand(128).astype(np.float32)

        result = temp_db.add_face(person_id=person_id, name=name, embedding=embedding)

        assert result is True
        assert person_id in temp_db.faces
        assert temp_db.faces[person_id]['name'] == name
        assert len(temp_db.faces[person_id]['embeddings']) == 1
        assert np.allclose(temp_db.faces[person_id]['embeddings'][0], embedding)

    def test_add_multiple_faces(self, temp_db):
        """Тест добавления нескольких лиц."""
        person_id = "test_person_1"
        name = "Test Person"
        
        for i in range(3):
            embedding = np.random.rand(128).astype(np.float32)
            temp_db.add_face(person_id=person_id, name=name, embedding=embedding)

        assert len(temp_db.faces[person_id]['embeddings']) == 3

    def test_get_face(self, temp_db):
        """Тест получения информации о лице."""
        person_id = "test_person_1"
        name = "Test Person"
        embedding = np.random.rand(128).astype(np.float32)

        temp_db.add_face(person_id=person_id, name=name, embedding=embedding)
        face_info = temp_db.get_face(person_id)

        assert face_info is not None
        assert face_info['name'] == name
        assert len(face_info['embeddings']) == 1

    def test_get_face_not_found(self, temp_db):
        """Тест получения несуществующего лица."""
        face_info = temp_db.get_face("non_existent")
        assert face_info is None

    def test_list_all_faces(self, temp_db):
        """Тест получения списка всех лиц."""
        # Добавляем несколько лиц
        for i in range(3):
            person_id = f"person_{i}"
            name = f"Person {i}"
            embedding = np.random.rand(128).astype(np.float32)
            temp_db.add_face(person_id=person_id, name=name, embedding=embedding)

        all_faces = temp_db.list_all_faces()
        assert len(all_faces) == 3
        assert all(isinstance(face, dict) for face in all_faces)

    def test_remove_face(self, temp_db):
        """Тест удаления лица."""
        person_id = "test_person_1"
        name = "Test Person"
        embedding = np.random.rand(128).astype(np.float32)

        temp_db.add_face(person_id=person_id, name=name, embedding=embedding)
        assert person_id in temp_db.faces

        result = temp_db.remove_face(person_id)
        assert result is True
        assert person_id not in temp_db.faces

    def test_remove_face_not_found(self, temp_db):
        """Тест удаления несуществующего лица."""
        result = temp_db.remove_face("non_existent")
        assert result is False

    def test_save_and_load_database(self, temp_db):
        """Тест сохранения и загрузки базы данных."""
        person_id = "test_person_1"
        name = "Test Person"
        embedding = np.random.rand(128).astype(np.float32)

        temp_db.add_face(person_id=person_id, name=name, embedding=embedding)
        temp_db.save_database()

        # Создаем новую базу и загружаем
        db2 = FaceDatabase(database_path=str(temp_db.database_path))
        assert person_id in db2.faces
        assert db2.faces[person_id]['name'] == name

