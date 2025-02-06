from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from config import Config
import logging
import os
import secrets

# Import our trading components
from exchange import BlofingExchange
from scanner import CoinScanner

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))
logger = logging.getLogger(__name__)

class ConfigurationForm(FlaskForm):
    timeframe = StringField('Timeframe', validators=[DataRequired()])
    position_size = FloatField('Position Size', validators=[DataRequired(), NumberRange(min=0)])
    leverage = IntegerField('Leverage', validators=[DataRequired(), NumberRange(min=1, max=100)])
    isolated = BooleanField('Isolated Margin')
    symbol = StringField('Symbol', validators=[DataRequired()])
    max_positions = IntegerField('Max Positions', validators=[DataRequired(), NumberRange(min=1, max=10)])
    top_coins_to_scan = IntegerField('Top Coins to Scan', validators=[DataRequired(), NumberRange(min=1, max=50)])
    submit = SubmitField('Save Configuration')

@app.route('/')
def index():
    try:
        form = ConfigurationForm(obj=Config)

        # Initialize exchange and scanner for coin data
        exchange = BlofingExchange()
        scanner = CoinScanner(exchange, Config)

        try:
            monitored_coins = scanner.get_top_volume_coins()
            logger.info(f"Successfully fetched {len(monitored_coins)} monitored coins")
        except Exception as e:
            logger.error(f"Error fetching monitored coins: {str(e)}")
            monitored_coins = []
            flash("Error fetching monitored coins. Please check the logs.", "error")

        try:
            positions = exchange.get_positions()
            logger.info(f"Successfully fetched {len(positions)} positions")
        except Exception as e:
            logger.error(f"Error fetching positions: {str(e)}")
            positions = []
            flash("Error fetching positions. Please check the logs.", "error")

        return render_template('dashboard.html', 
                            form=form,
                            monitored_coins=monitored_coins,
                            positions=positions,
                            config=Config)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        flash(f"An error occurred: {str(e)}", "error")
        return render_template('dashboard.html', 
                            form=ConfigurationForm(),
                            monitored_coins=[],
                            positions=[])

@app.route('/update_config', methods=['POST'])
def update_config():
    form = ConfigurationForm()
    if form.validate_on_submit():
        try:
            # Update configuration with proper type conversion
            Config.TIMEFRAME = str(form.timeframe.data)
            Config.POSITION_SIZE = float(form.position_size.data)
            Config.LEVERAGE = int(form.leverage.data)
            Config.ISOLATED = bool(form.isolated.data)
            Config.SYMBOL = str(form.symbol.data)
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

@app.route('/api/monitored_coins')
def get_monitored_coins():
    try:
        exchange = BlofingExchange()
        scanner = CoinScanner(exchange, Config)
        monitored_coins = scanner.get_top_volume_coins()
        return jsonify({"coins": monitored_coins})
    except Exception as e:
        logger.error(f"Error in /api/monitored_coins: {str(e)}")
        return jsonify({"error": str(e)}), 500

def start_web_interface():
    """Start the web interface without debug mode in the thread"""
    try:
        app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start web interface: {str(e)}")