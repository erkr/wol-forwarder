"""HTTP API server for WOL Forwarder status monitoring."""

import logging
from flask import Flask, jsonify, request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wol_packet_listener import WoLPacketListener

logger = logging.getLogger(__name__)


def create_api_server(listener: "WoLPacketListener") -> Flask:
    """
    Create and configure Flask API server.
    
    Args:
        listener: WoLPacketListener instance to expose status from
    
    Returns:
        Flask app instance
    """
    app = Flask(__name__)

    @app.route('/config', methods=['GET'])
    def get_config():
        """Return current WOL forwarder config."""
        try:
            status = listener.get_config()
            return jsonify({
                'success': True,
                'data': status
            }), 200
        except Exception as e:
            logger.exception("Error retrieving config: %s", e)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint."""
        return jsonify({
            'status': 'ok' if listener.running else 'stopped',
            'listening': listener.running
        }), 200 if listener.running else 503

    @app.route('/stats', methods=['GET'])
    def get_stats():
        """Return packet statistics only."""
        try:
            status = listener.get_stats()
            return jsonify({
                'success': True,
                'data': status
            }), 200
        except Exception as e:
            logger.exception("Error retrieving stats: %s", e)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/dns', methods=['GET'])
    def get_dns_cache():
        """Return DNS cache state."""
        try:
            status = listener.get_dns_cache()
            return jsonify({
                'success': True,
                'data': status
            }), 200
        except Exception as e:
            logger.exception("Error retrieving DNS Cache: %s", e)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            'success': False,
            'error': 'Endpoint not found',
            'available_endpoints': ['/config', '/health', '/stats', '/dns']
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

    logger.debug("HTTP API server configured successfully")
    return app
