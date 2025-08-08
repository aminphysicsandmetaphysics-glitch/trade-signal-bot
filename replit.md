# Telegram Signal Bot Manager

## Overview

This is a Flask-based web application that manages a Telegram bot for parsing and forwarding trading signals. The system monitors specified Telegram channels for trading signals, parses them into a structured format, and forwards them to a destination channel. The application provides a web interface for configuration, monitoring, and real-time dashboard functionality.

The bot can parse trading signals containing entry points, stop losses, take profit levels, and risk-reward ratios from multiple source channels and reformat them before forwarding to a target channel.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 dark theme
- **Real-time Updates**: JavaScript-based dashboard with automatic refresh functionality
- **UI Components**: Responsive design with cards, forms, and status indicators
- **Static Assets**: CSS/JS files for dashboard interactivity

### Backend Architecture
- **Web Framework**: Flask with SQLAlchemy ORM for database operations
- **Database Models**: Two main models - Config (bot settings) and Signal (parsed trading data)
- **Bot Integration**: Telethon-based Telegram client for message handling
- **Threading**: Separate thread management for bot operations
- **API Endpoints**: RESTful endpoints for signal data retrieval

### Data Storage Solutions
- **Primary Database**: SQLite for development, configurable via DATABASE_URL environment variable
- **Connection Pooling**: Configured with pool recycling and pre-ping for reliability
- **Model Structure**: 
  - Config table stores API credentials, channel configurations, and session settings
  - Signal table stores parsed trading data with JSON fields for complex data types

### Authentication and Authorization
- **Session Management**: Flask session handling with configurable secret key
- **Environment-based Security**: API credentials and secrets managed via environment variables
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxies

### Signal Processing Pipeline
- **Message Parsing**: Regex-based pattern matching for trading signal extraction
- **Data Normalization**: Structured parsing of symbols, positions, entry points, stop losses, and take profits
- **Format Standardization**: Consistent signal formatting before forwarding
- **Source Tracking**: Maintains record of original channel and message content

## External Dependencies

### Telegram Integration
- **Telethon Library**: Telegram client library for bot functionality
- **API Requirements**: Telegram API ID and hash from my.telegram.org
- **Channel Access**: Requires access to source channels for message monitoring

### Web Framework Stack
- **Flask**: Core web application framework
- **SQLAlchemy**: Database ORM and query builder
- **Jinja2**: Template rendering engine
- **Werkzeug**: WSGI utilities and middleware

### Frontend Libraries
- **Bootstrap 5**: CSS framework with dark theme
- **Font Awesome**: Icon library for UI elements
- **Custom JavaScript**: Real-time dashboard functionality

### Development and Deployment
- **Environment Configuration**: Support for development and production settings
- **Database Migration**: Automatic table creation via SQLAlchemy
- **Session Management**: Persistent Telegram sessions for bot continuity
- **Logging**: Comprehensive logging system for debugging and monitoring