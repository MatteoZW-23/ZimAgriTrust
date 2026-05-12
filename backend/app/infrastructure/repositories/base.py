"""
Base Repository Pattern Implementation
Provides common CRUD operations and query building for all repositories.
This abstracts data access logic from business logic.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

# Type variable for generic repository
T = TypeVar('T')
M = TypeVar('M')  # ORM Model

class IRepository(ABC, Generic[T]):
    """
    Repository interface - defines contract for data access.
    All repositories implement this interface.
    """
    
    @abstractmethod
    async def get(self, id: UUID) -> Optional[T]:
        """Get single entity by ID"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create new entity"""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update existing entity"""
        pass
    
    @abstractmethod
    async def delete(self, id: UUID) -> None:
        """Delete entity by ID"""
        pass
    
    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        """Check if entity exists"""
        pass


class BaseRepository(IRepository[T]):
    """
    Base implementation of repository pattern.
    Provides common CRUD operations and query building.
    
    Concrete repositories inherit from this and override specific methods.
    """
    
    def __init__(self, db: Session, model: type):
        """
        Initialize repository with database session and ORM model.
        
        Args:
            db: SQLAlchemy session
            model: SQLAlchemy ORM model class
        """
        self.db = db
        self.model = model
    
    async def get(self, id: UUID) -> Optional[T]:
        """
        Retrieve single entity by ID.
        
        Returns:
            Entity if found, None otherwise
        """
        return self.db.query(self.model).filter(
            self.model.id == id
        ).first()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Retrieve all entities with pagination.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of entities
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    async def create(self, entity: T) -> T:
        """
        Create new entity in database.
        
        Args:
            entity: Entity object to create
        
        Returns:
            Created entity with ID assigned
        """
        self.db.add(entity)
        self.db.flush()  # Flush to get ID, don't commit yet (transaction control)
        self.db.refresh(entity)  # Refresh to get generated fields
        return entity
    
    async def update(self, entity: T) -> T:
        """
        Update existing entity in database.
        
        Args:
            entity: Entity object with updated values
        
        Returns:
            Updated entity
        """
        self.db.merge(entity)
        self.db.flush()
        return entity
    
    async def delete(self, id: UUID) -> None:
        """
        Delete entity from database.
        
        Args:
            id: ID of entity to delete
        """
        entity = await self.get(id)
        if entity:
            self.db.delete(entity)
            self.db.flush()
    
    async def exists(self, id: UUID) -> bool:
        """
        Check if entity exists.
        
        Args:
            id: ID to check
        
        Returns:
            True if entity exists, False otherwise
        """
        return self.db.query(self.model).filter(
            self.model.id == id
        ).first() is not None
    
    def _build_query(self, filters: Optional[Dict[str, Any]] = None):
        """
        Build query with optional filters.
        
        Args:
            filters: Dictionary of filter conditions {field_name: value}
        
        Returns:
            SQLAlchemy query object
        """
        query = self.db.query(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        return query
    
    async def find_by_filters(self, filters: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[T]:
        """
        Find entities matching multiple filter conditions.
        
        Args:
            filters: Dictionary of {field_name: value} to filter by
            skip: Pagination skip
            limit: Pagination limit
        
        Returns:
            List of matching entities
        """
        query = self._build_query(filters)
        return query.offset(skip).limit(limit).all()
    
    async def find_one_by_filters(self, filters: Dict[str, Any]) -> Optional[T]:
        """
        Find single entity matching filter conditions.
        
        Args:
            filters: Dictionary of {field_name: value} to filter by
        
        Returns:
            First matching entity or None
        """
        query = self._build_query(filters)
        return query.first()
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities, optionally with filters.
        
        Args:
            filters: Optional filter conditions
        
        Returns:
            Count of matching entities
        """
        query = self._build_query(filters)
        return query.count()
    
    def commit(self) -> None:
        """Commit pending changes to database"""
        self.db.commit()
    
    def rollback(self) -> None:
        """Rollback pending changes"""
        self.db.rollback()


class PagedResult(Generic[T]):
    """Wrapper for paginated query results"""
    
    def __init__(self, items: List[T], total: int, skip: int, limit: int):
        self.items = items
        self.total = total
        self.skip = skip
        self.limit = limit
        self.page = skip // limit + 1
        self.pages = (total + limit - 1) // limit
    
    def to_dict(self):
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "pages": self.pages,
            "limit": self.limit
        }
