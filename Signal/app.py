import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from threading import Thread
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///signal_bot.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize the app with the extension
db.init_app(app)

# Import signal bot functionality
from signal_bot import SignalBot

# Global bot instance
bot_instance = None

with app.app_context():
    # Import models
    from models import Config, Signal
    db.create_all()

@app.route('/')
def index():
    """Main dashboard page"""
    config = Config.query.first()
    recent_signals = Signal.query.order_by(Signal.timestamp.desc()).limit(10).all()
    
    bot_status = "Not Running"
    if bot_instance and bot_instance.is_running():
        bot_status = "Running"
    elif config and config.api_id and config.api_hash:
        bot_status = "Configured - Ready to Start"
    
    return render_template('index.html', 
                         config=config, 
                         recent_signals=recent_signals,
                         bot_status=bot_status)

@app.route('/config', methods=['GET', 'POST'])
def config_page():
    """Configuration page for API settings and channels"""
    if request.method == 'POST':
        try:
            # Get or create config
            config = Config.query.first()
            if not config:
                config = Config()
                db.session.add(config)
            
            # Update config from form
            config.api_id = request.form.get('api_id')
            config.api_hash = request.form.get('api_hash')
            config.session_name = request.form.get('session_name', 'signal_bot')
            config.to_channel = request.form.get('to_channel')
            
            # Parse source channels (comma separated)
            from_channels_str = request.form.get('from_channels', '')
            if from_channels_str:
                try:
                    # Handle both numeric IDs and usernames
                    channels = []
                    for ch in from_channels_str.split(','):
                        ch = ch.strip()
                        if ch.isdigit():
                            channels.append(int(ch))
                        else:
                            channels.append(ch)
                    config.from_channels = json.dumps(channels)
                except Exception as e:
                    flash(f'Error parsing source channels: {str(e)}', 'error')
                    return redirect(url_for('config_page'))
            
            db.session.commit()
            flash('Configuration saved successfully!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Error saving configuration: {str(e)}', 'error')
    
    config = Config.query.first()
    return render_template('config.html', config=config)

@app.route('/dashboard')
def dashboard():
    """Real-time dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/signals')
def api_signals():
    """API endpoint for real-time signal updates"""
    try:
        signals = Signal.query.order_by(Signal.timestamp.desc()).limit(20).all()
        signals_data = []
        
        for signal in signals:
            signals_data.append({
                'id': signal.id,
                'symbol': signal.symbol,
                'position': signal.position,
                'entry': signal.entry,
                'stop_loss': signal.stop_loss,
                'take_profits': signal.take_profits,
                'risk_reward': signal.risk_reward,
                'source_channel': signal.source_channel,
                'timestamp': signal.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'formatted_signal': signal.formatted_signal
            })
        
        bot_status = "stopped"
        if bot_instance and bot_instance.is_running():
            bot_status = "running"
        
        return jsonify({
            'signals': signals_data,
            'bot_status': bot_status,
            'total_signals': Signal.query.count()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/start_bot', methods=['POST'])
def start_bot():
    """Start the Telegram bot"""
    global bot_instance
    
    try:
        config = Config.query.first()
        if not config or not config.api_id or not config.api_hash:
            flash('Please configure API credentials first', 'error')
            return redirect(url_for('index'))
        
        if bot_instance and bot_instance.is_running():
            flash('Bot is already running', 'warning')
            return redirect(url_for('index'))
        
        # Parse from_channels
        from_channels = []
        if config.from_channels:
            from_channels = json.loads(config.from_channels)
        
        # Create and start bot
        bot_instance = SignalBot(
            api_id=int(config.api_id),
            api_hash=config.api_hash,
            session_name=config.session_name,
            from_channels=from_channels,
            to_channel=config.to_channel
        )
        
        # Start bot in background thread
        bot_thread = Thread(target=bot_instance.start, daemon=True)
        bot_thread.start()
        
        flash('Bot started successfully!', 'success')
        
    except Exception as e:
        flash(f'Error starting bot: {str(e)}', 'error')
        logging.error(f"Error starting bot: {str(e)}")
    
    return redirect(url_for('index'))

@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    """Stop the Telegram bot"""
    global bot_instance
    
    try:
        if bot_instance and bot_instance.is_running():
            bot_instance.stop()
            flash('Bot stopped successfully!', 'success')
        else:
            flash('Bot is not running', 'warning')
    except Exception as e:
        flash(f'Error stopping bot: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/clear_signals', methods=['POST'])
def clear_signals():
    """Clear all signal history"""
    try:
        Signal.query.delete()
        db.session.commit()
        flash('Signal history cleared successfully!', 'success')
    except Exception as e:
        flash(f'Error clearing signals: {str(e)}', 'error')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
