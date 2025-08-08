from telethon import TelegramClient, events
import re
import asyncio
import logging
from threading import Thread
import json
from datetime import datetime

class SignalBot:
    """Telegram signal bot with web interface integration"""
    
    def __init__(self, api_id, api_hash, session_name, from_channels, to_channel):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.from_channels = from_channels
        self.to_channel = to_channel
        self.client = None
        self.running = False
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def parse_signal(self, message):
        """Advanced signal parsing with multiple format support"""
        text = message.message.strip()
        
        # Pre-validation: Must contain trading keywords
        signal_keywords = ['entry', 'tp', 'sl', 'target', 'stop', 'buy', 'sell', 'long', 'short']
        if not any(keyword in text.lower() for keyword in signal_keywords):
            return None
            
        # Enhanced validation: Check signal structure
        if not self._is_valid_signal_structure(text):
            return None
            
        return self._extract_signal_data(text, message)
    
    def _is_valid_signal_structure(self, text):
        """Validate if message has proper signal structure"""
        lines = text.splitlines()
        text_lower = text.lower()
        
        # Filter out common non-signal patterns first
        non_signal_patterns = [
            r'close.*profit',
            r'move sl',
            r'change tp',
            r'\+\d+.*pips',
            r'sl reached',
            r'tp reached',
            r'break.*even',
            r'entry.*break.*even',
            r'position.*update',
            r'trade.*update',
            r'close.*position',
            r'delete',
            r'remove.*order',
            r'cancel',
            r'activated',
            r'didn.*t.*activate',
            r'subscription',
            r'upgrade',
            r'contact.*@',
            r'website',
            r'calculator',
            r'economic.*calendar',
            r'risk.*management',
            r'lot.*size',
            r'weekend',
            r'market.*close',
            r'analyze?',
            r'tradingview',
            r'screenshot',
            r'profit.*screenshot',
            r'important.*update',
            r'note.*from',
            r'apologize',
            r'transparency',
            r'support.*on',
            r'favor',
            r'energy.*flowing'
        ]
        
        for pattern in non_signal_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # Must have minimum length for valid signals
        if len(text) < 20:
            return False
            
        # Count signal components
        has_symbol = False
        has_position = False
        has_entry = False
        has_sl = False
        has_tp = False
        price_count = 0
        
        for line in lines:
            line_clean = line.strip()
            line_lower = line_clean.lower()
            
            # Skip empty lines and non-relevant lines
            if not line_clean or len(line_clean) < 3:
                continue
                
            # Symbol patterns (enhanced)
            symbol_patterns = [
                r'[A-Z]{3,8}USD[T]?',
                r'[A-Z]{3,8}BTC',
                r'[A-Z]{3,8}ETH', 
                r'XAU[A-Z]*',
                r'GOLD',
                r'[A-Z]{6}',  # Like EURAUD, GBPUSD
                r'#[A-Z]{3,8}'
            ]
            
            for pattern in symbol_patterns:
                if re.search(pattern, line_clean.upper()):
                    has_symbol = True
                    break
                    
            # Position patterns (enhanced)
            position_indicators = ['buy', 'sell', 'long', 'short']
            if any(pos in line_lower for pos in position_indicators):
                if not any(exclude in line_lower for exclude in ['close', 'profit', 'update']):
                    has_position = True
                    
            # Entry patterns (enhanced)
            entry_patterns = [
                r'entry.*price.*:?\s*([\d.]+)',
                r'e:\s*([\d.]+)',
                r'entry.*:?\s*([\d.]+)',
                r'enter.*:?\s*([\d.]+)',
                # Simple format: "GOLD BUY 3373.33" or "USDCAD SELL 1.37480"
                r'(?:buy|sell)\s+([\d.]+)',
                r'(?:buy|sell)\s+(?:limit\s+)?([\d]+)'
            ]
            
            for pattern in entry_patterns:
                if re.search(pattern, line_lower):
                    has_entry = True
                    price_count += 1
                    break
                    
            # Stop loss patterns (enhanced)
            sl_patterns = [
                r'stop.*loss.*:?\s*([\d.]+)',
                r'sl.*:?\s*([\d.]+)',
                r'stop.*:?\s*([\d.]+)'
            ]
            
            for pattern in sl_patterns:
                if re.search(pattern, line_lower):
                    has_sl = True
                    price_count += 1
                    break
                    
            # Take profit patterns (enhanced)
            tp_patterns = [
                r'tp\d*.*:?\s*([\d.]+)',
                r'take.*profit.*:?\s*([\d.]+)',
                r'target.*:?\s*([\d.]+)',
                r'✔️.*tp\d*.*:?\s*([\d.]+)'
            ]
            
            for pattern in tp_patterns:
                if re.search(pattern, line_lower):
                    has_tp = True
                    price_count += 1
                    break
        
        # Enhanced validation:
        # 1. Must have symbol
        # 2. Must have entry price
        # 3. Must have either SL or TP
        # 4. Must have at least 2 prices (entry + sl/tp)
        return (has_symbol and has_entry and (has_sl or has_tp) and price_count >= 2)
    
    def _extract_signal_data(self, text, message):
        """Extract signal data with enhanced parsing"""
        lines = text.splitlines()
        
        symbol = ""
        position = ""
        entry = ""
        sl = ""
        r_r = ""
        tps = []
        
        for line in lines:
            line_clean = line.strip()
            line_lower = line_clean.lower()
            
            # Skip empty lines and irrelevant lines
            if not line_clean or len(line_clean) < 3:
                continue
                
            # Enhanced symbol detection
            if not symbol:
                symbol = self._extract_symbol(line_clean)
                
            # Enhanced position detection  
            if not position:
                position = self._extract_position(line_lower)
                
            # Enhanced entry detection with specific patterns
            if not entry:
                if any(keyword in line_lower for keyword in ['entry', 'e:']):
                    entry = self._extract_price(line_clean)
                elif symbol and not any(keyword in line_lower for keyword in ['tp', 'sl', 'stop', 'target']):
                    # For format like "GOLD BUY 3373.33" or "USDCAD SELL 1.37480"
                    if any(pos in line_lower for pos in ['buy', 'sell']):
                        price = self._extract_price(line_clean)
                        if price:
                            entry = price
                # Also try to extract entry from first line if symbol and position are found
                elif symbol and position and line_clean == lines[0]:
                    price = self._extract_price(line_clean)
                    if price:
                        entry = price
                            
            # Enhanced stop loss detection
            if not sl:
                if any(keyword in line_lower for keyword in ['sl', 'stop loss', 'stop']):
                    if not any(exclude in line_lower for exclude in ['move', 'change', 'hit', 'reached']):
                        sl = self._extract_price(line_clean)
                        
            # Enhanced take profit detection
            if any(keyword in line_lower for keyword in ['tp', 'target', '✔️']):
                if not any(exclude in line_lower for exclude in ['move', 'change', 'hit', 'reached', 'close']):
                    tp_price = self._extract_price(line_clean)
                    if tp_price and tp_price not in tps:
                        tps.append(tp_price)
                        
            # Risk/Reward detection (enhanced)
            if not r_r:
                if any(keyword in line_lower for keyword in ['r/r', 'risk-reward', 'risk/reward']):
                    r_r = self._extract_risk_reward(line_clean)
                
        # Enhanced final validation
        if not symbol:
            return None
            
        # Must have entry price
        if not entry:
            return None
            
        # Must have either stop loss or take profit
        if not sl and not tps:
            return None
            
        # Set default position if not found (try to infer from context)
        if not position:
            # Try to infer from symbol patterns or default to BUY
            position = "BUY"
            
        # Format signal message
        signal_text = f"📊 #{symbol}\n"
        signal_text += f"📉 Position: {position}\n"
        if r_r:
            signal_text += f"❗️ R/R : {r_r}\n"
        signal_text += f"💲 Entry Price : {entry}\n"
        for idx, tp in enumerate(tps):
            signal_text += f"✔️ TP{idx+1} : {tp}\n"
        if sl:
            signal_text += f"🚫 Stop Loss : {sl}"
            
        return {
            'symbol': symbol,
            'position': position,
            'entry': entry,
            'stop_loss': sl,
            'take_profits': tps,
            'risk_reward': r_r,
            'formatted_signal': signal_text,
            'original_message': text,
            'source_channel': str(message.chat_id)
        }
    
    def _extract_symbol(self, line):
        """Extract trading symbol from line with enhanced patterns"""
        line_upper = line.upper().strip()
        
        # Remove common prefixes and emojis
        line_clean = re.sub(r'[📊🔥✅❌#$]', '', line_upper).strip()
        
        # Enhanced patterns for different formats
        patterns = [
            # Forex pairs
            r'\b(EUR[A-Z]{3})\b',
            r'\b(GBP[A-Z]{3})\b', 
            r'\b(USD[A-Z]{3})\b',
            r'\b(AUD[A-Z]{3})\b',
            r'\b(NZD[A-Z]{3})\b',
            r'\b(CAD[A-Z]{3})\b',
            r'\b(CHF[A-Z]{3})\b',
            r'\b(JPY[A-Z]{3})\b',
            r'\b([A-Z]{3}USD)\b',
            r'\b([A-Z]{3}CAD)\b',
            r'\b([A-Z]{3}AUD)\b',
            r'\b([A-Z]{3}GBP)\b',
            r'\b([A-Z]{3}EUR)\b',
            r'\b([A-Z]{3}CHF)\b',
            r'\b([A-Z]{3}JPY)\b',
            
            # Crypto patterns
            r'\b([A-Z]{3,8}USDT?)\b',
            r'\b([A-Z]{3,8}BTC)\b',
            r'\b([A-Z]{3,8}ETH)\b',
            
            # Gold patterns
            r'\b(XAUUSD)\b',
            r'\b(GOLD)\b',
            r'\b(XAU[A-Z]*)\b',
            
            # General 6-letter pairs
            r'\b([A-Z]{6})\b',
            
            # Fallback patterns
            r'\b([A-Z]{3,8})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line_clean)
            if match:
                symbol = match.group(1)
                # Validate symbol length and format
                if 3 <= len(symbol) <= 8:
                    return symbol
        
        return ""
    
    def _extract_position(self, line_lower):
        """Extract position type from line with enhanced detection"""
        # Skip lines that contain update keywords
        if any(word in line_lower for word in ['close', 'profit', 'update', 'move', 'change']):
            return ""
            
        # Buy patterns
        buy_patterns = ['buy', 'long', 'buy limit', 'buy!']
        for pattern in buy_patterns:
            if pattern in line_lower:
                return "BUY"
                
        # Sell patterns  
        sell_patterns = ['sell', 'short', 'sell limit', 'sell!']
        for pattern in sell_patterns:
            if pattern in line_lower:
                return "SELL"
                
        return ""
    
    def _extract_price(self, line):
        """Extract price from line with enhanced patterns for different formats"""
        # Enhanced patterns for different price formats
        price_patterns = [
            # Format: "E: 1.78250" or "Entry: 1.78250"
            r'(?:entry|e)\s*:?\s*(\d+\.\d+)',
            # Format: "TP: 1.76850" or "Tp: 1.76850"
            r'(?:tp\d*|target)\s*:?\s*(\d+\.\d+)',
            # Format: "SL: 1.78700" or "Sl: 1.78700" 
            r'(?:sl|stop)\s*:?\s*(\d+\.\d+)',
            # Format: "Entry Price : 3355.00"
            r'entry\s*price\s*:?\s*(\d+\.?\d*)',
            # Format: "Stop Loss : 3360.00"
            r'stop\s*loss\s*:?\s*(\d+\.?\d*)',
            # Format: "USDCAD SELL 1.37480" or "GOLD BUY 3373.33"
            r'(?:buy|sell)\s+(\d+\.\d+)',
            # Format: "GOLD BUY LIMIT 3350" or just "GOLD BUY 3350"
            r'(?:buy|sell)\s+(?:limit\s+)?(\d+\.?\d*)',
            # Simple format after symbol and position: "SYMBOL BUY/SELL PRICE"
            r'[A-Z]{3,8}\s+(?:buy|sell)\s+(\d+\.?\d*)',
            # General decimal pattern
            r'(\d+\.\d{2,8})',
            # Large integer (like 3350 for gold)
            r'\b(\d{4,})\b'
        ]
        
        line_lower = line.lower()
        
        for pattern in price_patterns:
            match = re.search(pattern, line_lower)
            if match:
                price_str = match.group(1)
                try:
                    price = float(price_str)
                    # Reasonable price ranges for different markets
                    if 0.000001 <= price <= 50000:  # Extended range for gold
                        return price_str
                except ValueError:
                    continue
        
        return ""
    
    def _extract_risk_reward(self, line):
        """Extract risk/reward ratio"""
        patterns = [
            r'r/r[:\s]*(\d+[:\s/]\d+)',
            r'risk[:\s/]*(\d+[:\s/]\d+)',
            r'(\d+[:\s/]\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line.lower())
            if match:
                return match.group(1)
        return ""
    
    def save_signal_to_db(self, signal_data):
        """Save parsed signal to database"""
        try:
            from app import app, db
            from models import Signal
            
            with app.app_context():
                signal = Signal(
                    symbol=signal_data['symbol'],
                    position=signal_data['position'],
                    entry=signal_data['entry'],
                    stop_loss=signal_data['stop_loss'],
                    take_profits=json.dumps(signal_data['take_profits']),
                    risk_reward=signal_data['risk_reward'],
                    source_channel=signal_data['source_channel'],
                    formatted_signal=signal_data['formatted_signal'],
                    original_message=signal_data['original_message'],
                    timestamp=datetime.utcnow()
                )
                
                db.session.add(signal)
                db.session.commit()
                self.logger.info(f"Signal saved: {signal_data['symbol']} {signal_data['position']}")
                
        except Exception as e:
            self.logger.error(f"Error saving signal to database: {str(e)}")
    
    async def signal_handler(self, event):
        """Handle new messages from monitored channels"""
        try:
            self.logger.info(f"New message received from channel {event.chat_id}: {event.message.message[:100]}...")
            
            signal_data = self.parse_signal(event.message)
            if signal_data:
                self.logger.info(f"Signal parsed successfully: {signal_data['symbol']} {signal_data['position']}")
                
                # Save to database
                self.save_signal_to_db(signal_data)
                
                # Forward to destination channel
                if self.to_channel:
                    await self.client.send_message(
                        self.to_channel, 
                        signal_data['formatted_signal']
                    )
                    self.logger.info(f"Signal forwarded to {self.to_channel}")
                else:
                    self.logger.warning("No destination channel configured")
            else:
                self.logger.debug(f"Message did not match signal pattern from channel {event.chat_id}: {event.message.message[:100]}...")
                    
        except Exception as e:
            self.logger.error(f"Error handling signal: {str(e)}")
    
    def start(self):
        """Start the Telegram bot"""
        try:
            self.running = True
            asyncio.run(self._run_bot())
        except Exception as e:
            self.logger.error(f"Error starting bot: {str(e)}")
            self.running = False
    
    async def _run_bot(self):
        """Internal method to run the bot"""
        try:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            
            # Register event handler
            @self.client.on(events.NewMessage(chats=self.from_channels))
            async def handler(event):
                await self.signal_handler(event)
            
            # Start client
            await self.client.start()
            self.logger.info("Telegram bot started successfully")
            
            # Keep running
            await self.client.run_until_disconnected()
            
        except Exception as e:
            self.logger.error(f"Bot error: {str(e)}")
        finally:
            self.running = False
    
    def stop(self):
        """Stop the Telegram bot"""
        try:
            if self.client and self.client.is_connected():
                self.client.disconnect()
            self.running = False
            self.logger.info("Bot stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping bot: {str(e)}")
    
    def is_running(self):
        """Check if bot is currently running"""
        return self.running and self.client and self.client.is_connected()
