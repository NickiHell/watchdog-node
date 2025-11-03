"""Модуль базы данных лиц.

Хранит и управляет базой данных лиц с эмбеддингами.
"""

import os
import pickle
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime
import rclpy
from rclpy.logging import get_logger


class FaceDatabase:
    """Класс для управления базой данных лиц."""

    def __init__(self, database_path: str = '~/.watchdog_faces'):
        """Инициализирует базу данных лиц.

        Args:
            database_path: Путь к директории базы данных
        """
        self.database_path = Path(os.path.expanduser(database_path))
        self.database_path.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger('FaceDatabase')

        # Структура базы: {person_id: {'name': str, 'embeddings': List[np.ndarray], 'metadata': dict}}
        self.faces: Dict[str, Dict] = {}
        self.metadata_file = self.database_path / 'metadata.json'
        self.embeddings_dir = self.database_path / 'embeddings'

        self.embeddings_dir.mkdir(exist_ok=True)
        self.load_database()

    def load_database(self) -> bool:
        """Загружает базу данных из файлов.

        Returns:
            True если успешно загружено
        """
        try:
            # Загружаем метаданные
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {}

            # Загружаем эмбеддинги
            for person_id, person_data in metadata.items():
                embedding_file = self.embeddings_dir / f'{person_id}.pkl'
                if embedding_file.exists():
                    with open(embedding_file, 'rb') as f:
                        embeddings = pickle.load(f)
                    self.faces[person_id] = {
                        'name': person_data.get('name', 'Unknown'),
                        'embeddings': embeddings,
                        'metadata': person_data,
                        'created_at': person_data.get('created_at', ''),
                        'updated_at': person_data.get('updated_at', ''),
                    }
                else:
                    self.logger.warn(f'Эмбеддинги для {person_id} не найдены')

            self.logger.info(f'База данных загружена: {len(self.faces)} лиц')
            return True

        except Exception as e:
            self.logger.error(f'Ошибка загрузки базы данных: {e}')
            return False

    def save_database(self) -> bool:
        """Сохраняет базу данных в файлы.

        Returns:
            True если успешно сохранено
        """
        try:
            # Сохраняем метаданные
            metadata = {}
            for person_id, person_data in self.faces.items():
                embedding_file = self.embeddings_dir / f'{person_id}.pkl'

                # Сохраняем эмбеддинги
                with open(embedding_file, 'wb') as f:
                    pickle.dump(person_data['embeddings'], f)

                # Сохраняем метаданные
                metadata[person_id] = {
                    'name': person_data['name'],
                    'created_at': person_data.get('created_at', ''),
                    'updated_at': person_data.get('updated_at', datetime.now().isoformat()),
                    'embedding_count': len(person_data['embeddings']),
                }

            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            self.logger.info(f'База данных сохранена: {len(self.faces)} лиц')
            return True

        except Exception as e:
            self.logger.error(f'Ошибка сохранения базы данных: {e}')
            return False

    def add_face(
        self,
        person_id: str,
        name: str,
        embedding: np.ndarray,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Добавляет лицо в базу данных.

        Args:
            person_id: Уникальный ID человека
            name: Имя человека
            embedding: Эмбеддинг лица
            metadata: Дополнительные метаданные

        Returns:
            True если успешно добавлено
        """
        try:
            if embedding is None:
                self.logger.error('Эмбеддинг не может быть None')
                return False

            now = datetime.now().isoformat()

            if person_id in self.faces:
                # Обновляем существующее лицо
                self.faces[person_id]['embeddings'].append(embedding)
                self.faces[person_id]['updated_at'] = now
                if name:
                    self.faces[person_id]['name'] = name
                if metadata:
                    self.faces[person_id]['metadata'].update(metadata)
            else:
                # Добавляем новое лицо
                self.faces[person_id] = {
                    'name': name,
                    'embeddings': [embedding],
                    'metadata': metadata or {},
                    'created_at': now,
                    'updated_at': now,
                }

            self.save_database()
            self.logger.info(f'Лицо добавлено: {person_id} ({name})')
            return True

        except Exception as e:
            self.logger.error(f'Ошибка добавления лица: {e}')
            return False

    def find_face(self, embedding: np.ndarray, threshold: float = 0.6) -> Optional[Tuple[str, str, float]]:
        """Находит лицо в базе данных.

        Args:
            embedding: Эмбеддинг для поиска
            threshold: Порог схожести

        Returns:
            Кортеж (person_id, name, distance) или None если не найдено
        """
        if embedding is None:
            return None

        best_match = None
        best_distance = float('inf')

        for person_id, person_data in self.faces.items():
            # Проверяем все эмбеддинги для этого человека
            for stored_embedding in person_data['embeddings']:
                # Вычисляем расстояние
                distance = np.linalg.norm(embedding - stored_embedding)

                if distance < best_distance:
                    best_distance = distance
                    best_match = (person_id, person_data['name'], distance)

        # Проверяем, соответствует ли лучший результат порогу
        if best_match and best_distance <= threshold:
            return best_match

        return None

    def remove_face(self, person_id: str) -> bool:
        """Удаляет лицо из базы данных.

        Args:
            person_id: ID человека для удаления

        Returns:
            True если успешно удалено
        """
        try:
            if person_id in self.faces:
                del self.faces[person_id]

                # Удаляем файл эмбеддинга
                embedding_file = self.embeddings_dir / f'{person_id}.pkl'
                if embedding_file.exists():
                    embedding_file.unlink()

                self.save_database()
                self.logger.info(f'Лицо удалено: {person_id}')
                return True
            else:
                self.logger.warn(f'Лицо не найдено: {person_id}')
                return False

        except Exception as e:
            self.logger.error(f'Ошибка удаления лица: {e}')
            return False

    def list_faces(self) -> List[Dict]:
        """Возвращает список всех лиц в базе.

        Returns:
            Список словарей с информацией о лицах
        """
        result = []
        for person_id, person_data in self.faces.items():
            result.append({
                'person_id': person_id,
                'name': person_data['name'],
                'embedding_count': len(person_data['embeddings']),
                'created_at': person_data.get('created_at', ''),
                'updated_at': person_data.get('updated_at', ''),
            })
        return result

    def get_face_info(self, person_id: str) -> Optional[Dict]:
        """Получает информацию о лице.

        Args:
            person_id: ID человека

        Returns:
            Словарь с информацией или None
        """
        if person_id in self.faces:
            person_data = self.faces[person_id].copy()
            person_data['person_id'] = person_id
            return person_data
        return None

    def is_authorized(self, person_id: str) -> bool:
        """Проверяет, авторизован ли человек (в базе).

        Args:
            person_id: ID человека

        Returns:
            True если авторизован
        """
        return person_id in self.faces

