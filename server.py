from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange
import logging
import os
import secrets
from config import Config
from exchange import BlofingExchange
from scanner import CoinScanner
from bot_control import bot_controller
from trading_bot import run_trading_bot

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))
logger = logging.getLogger(__name__)

class ConfigurationForm(FlaskForm):
    timeframe = StringField('Timeframe', validators=[DataRequired()])
    position_size = FloatField('Position Size', validators=[DataRequired(), NumberRange(min=0)])
    leverage = IntegerField('Leverage', validators=[DataRequired(), NumberRange(min=1, max=100)])
    isolated = BooleanField('Isolated Margin')
    max_positions = IntegerField('Max Positions', validators=[DataRequired(), NumberRange(min=1, max=10)])
    top_coins_to_scan = IntegerField('Top Coins to Scan', validators=[DataRequired(), NumberRange(min=1, max=50)])
    submit = SubmitField('Save Configuration')

@app.route('/')
def index():
    try:
        form = ConfigurationForm(obj=Config)
        exchange = BlofingExchange()
        scanner = CoinScanner(exchange, Config)
        monitored_coins = []
        positions = []

        try:
            monitored_coins = scanner.get_monitored_coins()
        except Exception as e:
            logger.error(f"Error fetching monitored coins: {str(e)}")
            flash("Error fetching monitored coins. Please check the logs.", "error")

        try:
            positions = exchange.get_positions()
        except Exception as e:
            logger.error(f"Error fetching positions: {str(e)}")
            flash("Error fetching positions. Please check the logs.", "error")

        return render_template('dashboard.html',
                            form=form,
                            monitored_coins=monitored_coins,
                            positions=positions,
                            config=Config,
                            bot_running=bot_controller.is_running())
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        flash(f"An error occurred: {str(e)}", "error")
        return render_template('dashboard.html',
                            form=ConfigurationForm(),
                            monitored_coins=[],
                            positions=[],
                            config=Config,
                            bot_running=bot_controller.is_running())

@app.route('/update_config', methods=['POST'])
def update_config():
    """Update bot configuration"""
    form = ConfigurationForm()
    if form.validate_on_submit():
        try:
            Config.TIMEFRAME = form.timeframe.data
            Config.POSITION_SIZE = float(form.position_size.data)
            Config.LEVERAGE = int(form.leverage.data)
            Config.ISOLATED = bool(form.isolated.data)
            Config.MAX_POSITIONS = int(form.max_positions.data)
            Config.TOP_COINS_TO_SCAN = int(form.top_coins_to_scan.data)

            flash('Configuration updated successfully!', 'success')
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            flash(f'Error updating configuration: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
                logger.error(f"Form validation error - {field}: {error}")

    return redirect(url_for('index'))

@app.route('/start_bot', methods=['POST'])
def start_bot():
    try:
        if bot_controller.start_bot(run_trading_bot):
            logger.info("Bot started successfully")
            return jsonify({"success": True})
        logger.warning("Bot is already running")
        return jsonify({"success": False, "error": "Bot is already running"})
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    try:
        if bot_controller.stop_bot():
            logger.info("Bot stopped successfully")
            return jsonify({"success": True})
        logger.warning("Bot is not running")
        return jsonify({"success": False, "error": "Bot is not running"})
    except Exception as e:
        logger.error(f"Failed to stop bot: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

def start_server():
    """Start the Flask server"""
    try:
        logger.info("Starting web server on port 8080")
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        logger.error(f"Failed to start web server: {str(e)}")
        raise