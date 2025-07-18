#!/usr/bin/env python3
"""
Configuration settings for StubHub Scraper
==========================================
Centralized configuration management with environment variable support
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScraperConfig:
    """Configuration settings for the event scraper."""
    # Input/Output files
    input_csv: str = "worldcities.csv"
    combined_csv: str = "events.csv"
    progress_log: str = "progress_log_event.log"
    out_dir: str = "wget_output"
    
    # Performance settings
    concurrent_cities: int = int(os.getenv('CONCURRENT_CITIES', 5))
    wait_seconds: float = float(os.getenv('WAIT_SECONDS', 1.0))
    
    # Retry settings
    max_retries: int = int(os.getenv('MAX_RETRIES', 3))
    retry_delay: float = float(os.getenv('RETRY_DELAY', 2.0))
    
    # Request settings
    request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    # Logging
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_file: str = os.getenv('LOG_FILE', 'scraper.log')


@dataclass
class VenueFetcherConfig:
    """Configuration settings for the venue map fetcher."""
    # Input/Output
    events_csv: str = "events.csv"
    venue_dir: str = "venues"
    
    # Performance settings
    concurrent_venues: int = int(os.getenv('CONCURRENT_VENUES', 10))
    
    # Retry settings
    max_retries: int = int(os.getenv('MAX_RETRIES', 3))
    retry_delay: float = float(os.getenv('RETRY_DELAY', 2.0))
    
    # Request settings
    request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    # Logging
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_file: str = os.getenv('LOG_FILE', 'venue_fetcher.log')


@dataclass
class HTTPConfig:
    """HTTP headers and settings for requests."""
    headers: tuple = (
        "-H", "Content-Type: application/x-www-form-urlencoded",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36",
        "-H", "Accept: */*",
        "-H", "Accept-Encoding: gzip, deflate",
        "-H", "Referer: https://www.stubhub.com/",
        "-H", "Origin: https://www.stubhub.com",
        "-H", "Connection: keep-alive",
    )
    
    # Rate limiting
    respect_rate_limits: bool = bool(os.getenv('RESPECT_RATE_LIMITS', True))
    rate_limit_delay: float = float(os.getenv('RATE_LIMIT_DELAY', 1.0))


def get_scraper_config() -> ScraperConfig:
    """Get scraper configuration with validation."""
    config = ScraperConfig()
    _validate_config(config)
    return config


def get_venue_fetcher_config() -> VenueFetcherConfig:
    """Get venue fetcher configuration with validation."""
    config = VenueFetcherConfig()
    _validate_config(config)
    return config


def get_http_config() -> HTTPConfig:
    """Get HTTP configuration."""
    return HTTPConfig()


def _validate_config(config) -> None:
    """Validate configuration settings."""
    # Validate concurrent workers
    if hasattr(config, 'concurrent_cities') and config.concurrent_cities < 1:
        raise ValueError("concurrent_cities must be at least 1")
    
    if hasattr(config, 'concurrent_venues') and config.concurrent_venues < 1:
        raise ValueError("concurrent_venues must be at least 1")
    
    # Validate retry settings
    if config.max_retries < 1:
        raise ValueError("max_retries must be at least 1")
    
    if config.retry_delay < 0:
        raise ValueError("retry_delay must be non-negative")
    
    # Validate timeout
    if config.request_timeout < 1:
        raise ValueError("request_timeout must be at least 1 second")


def print_config_info() -> None:
    """Print current configuration for debugging."""
    print("=== Current Configuration ===")
    print(f"Scraper Config: {get_scraper_config()}")
    print(f"Venue Fetcher Config: {get_venue_fetcher_config()}")
    print(f"HTTP Config: {get_http_config()}")
    print("==============================")


if __name__ == "__main__":
    # For testing configuration
    print_config_info()