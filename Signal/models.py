from app import db
from datetime import datetime
import json

class Config(db.Model):
    """Configuration model for storing bot settings"""
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.String(50))
    api_hash = db.Column(db.String(100))
    session_name = db.Column(db.String(50), default='signal_bot')
    from_channels = db.Column(db.Text)  # JSON string of channel IDs/usernames
    to_channel = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_from_channels_list(self):
        """Get from_channels as a Python list"""
        if self.from_channels:
            try:
                return json.loads(self.from_channels)
            except:
                return []
        return []

class Signal(db.Model):
    """Model for storing parsed trading signals"""
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20))
    position = db.Column(db.String(10))  # BUY/SELL
    entry = db.Column(db.String(20))
    stop_loss = db.Column(db.String(20))
    take_profits = db.Column(db.Text)  # JSON string of TP levels
    risk_reward = db.Column(db.String(20))
    source_channel = db.Column(db.String(100))
    formatted_signal = db.Column(db.Text)
    original_message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_take_profits_list(self):
        """Get take_profits as a Python list"""
        if self.take_profits:
            try:
                return json.loads(self.take_profits)
            except:
                return []
        return []
    
    def __repr__(self):
        return f'<Signal {self.symbol} {self.position} @ {self.timestamp}>'
