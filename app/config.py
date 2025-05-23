import os
from enum import Enum, auto

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'my_secret_key')
    DEBUG = False
    TESTING = False
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'railway.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Reservation system constraints
    CONFIRMED_BERTHS = 63
    RAC_BERTHS = 18  # 9 side-lower berths, 2 passengers per berth
    WAITING_LIST_MAX = 10
    MIN_AGE_FOR_BERTH = 5
    SENIOR_CITIZEN_AGE = 60

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    # Production-specific configuration
    pass

# Enums for statuses and berth types
class TicketStatus(str, Enum):
    CONFIRMED = "confirmed"
    RAC = "rac"
    WAITING = "waiting"
    CANCELLED = "cancelled"

class BerthType(str, Enum):
    LOWER = "lower"
    MIDDLE = "middle"
    UPPER = "upper"
    SIDE_LOWER = "side-lower"

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
