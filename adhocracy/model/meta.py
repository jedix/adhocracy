"""SQLAlchemy Metadata and Session object"""
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from decorator import decorator
import hooks

__all__ = ['Session', 'data', 'extension', 'engine']

# SQLAlchemy database engine.  Updated by model.init_model()
engine = None

# SQLAlchemy session manager.  Updated by model.init_model()
# REFACT: this is an instance, not a class - so it should be lowercased
Session = None

# Global metadata. If you have multiple databases with overlapping table
# names, you'll need a metadata for each database
data = MetaData()

extension = hooks.HookExtension() 
