import os

class Config:
    """Base configuration."""
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'devkey')
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('DATABASE_URL', 'sqlite:///hotel.db')
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG: bool = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG: bool = False

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
