"""
================================================================================
qr_generator.py - QR Code Generator for Stealth Deck
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
QR code generator for sharing data and URLs.
Generates QR codes optimized for small displays.

Features:
- QR code generation
- Multiple data types (URL, text, WiFi)
- Display optimization
- Error correction levels
- Size adjustment

================================================================================
"""

import logging
from typing import Optional
from pathlib import Path
import qrcode
from qrcode.image.pure import PyPNGImage
from PIL import Image


class QRGenerator:
    """
    QR code generator.
    
    Generates QR codes for various data types.
    """
    
    def __init__(self):
        """Initialize QR generator."""
        self.logger = logging.getLogger('qr_generator')
        
        self.default_size = 10
        self.default_border = 2
        self.default_error_correction = qrcode.constants.ERROR_CORRECT_M
        
        self.output_dir = Path('/tmp/stealth-deck/qr')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, data: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Generate QR code from data.
        
        Args:
            data: Data to encode
            filename: Output filename (optional)
            
        Returns:
            Path to generated QR code image
        """
        try:
            self.logger.info(f"Generating QR code for: {data[:50]}...")
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=self.default_error_correction,
                box_size=self.default_size,
                border=self.default_border
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            if filename is None:
                import hashlib
                data_hash = hashlib.md5(data.encode()).hexdigest()[:8]
                filename = f"qr_{data_hash}.png"
            
            output_path = self.output_dir / filename
            
            img.save(str(output_path))
            
            self.logger.info(f"QR code saved: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"QR generation failed: {e}")
            return None
    
    def generate_url(self, url: str) -> Optional[str]:
        """
        Generate QR code for URL.
        
        Args:
            url: URL to encode
            
        Returns:
            Path to QR code image
        """
        return self.generate(url, "qr_url.png")
    
    def generate_text(self, text: str) -> Optional[str]:
        """
        Generate QR code for text.
        
        Args:
            text: Text to encode
            
        Returns:
            Path to QR code image
        """
        return self.generate(text, "qr_text.png")
    
    def generate_wifi(self, ssid: str, password: str, 
                     security: str = "WPA") -> Optional[str]:
        """
        Generate QR code for WiFi credentials.
        
        Args:
            ssid: WiFi SSID
            password: WiFi password
            security: Security type (WPA, WEP, nopass)
            
        Returns:
            Path to QR code image
        """
        wifi_string = f"WIFI:T:{security};S:{ssid};P:{password};;"
        
        return self.generate(wifi_string, "qr_wifi.png")
    
    def generate_for_display(self, data: str, max_size: int = 240) -> Optional[str]:
        """
        Generate QR code optimized for display.
        
        Args:
            data: Data to encode
            max_size: Maximum dimension in pixels
            
        Returns:
            Path to QR code image
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=5,
                border=1
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            width, height = img.size
            
            if width > max_size or height > max_size:
                img = img.resize((max_size, max_size), Image.Resampling.LANCZOS)
            
            output_path = self.output_dir / "qr_display.png"
            img.save(str(output_path))
            
            self.logger.info(f"Display QR code saved: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Display QR generation failed: {e}")
            return None
    
    def cleanup_old(self) -> int:
        """
        Clean up old QR code files.
        
        Returns:
            Number of files deleted
        """
        try:
            deleted = 0
            
            for file in self.output_dir.glob("*.png"):
                file.unlink()
                deleted += 1
            
            if deleted > 0:
                self.logger.info(f"Cleaned up {deleted} QR code files")
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    qr = QRGenerator()
    
    url_qr = qr.generate_url("https://github.com/stealth-deck")
    print(f"URL QR: {url_qr}")
    
    text_qr = qr.generate_text("Hello from Stealth Deck!")
    print(f"Text QR: {text_qr}")
    
    wifi_qr = qr.generate_wifi("MyNetwork", "password123")
    print(f"WiFi QR: {wifi_qr}")
