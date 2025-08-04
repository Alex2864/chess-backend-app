# filename: main.py (Final version that uses the explicit path)
from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
from stockfish import Stockfish
import os # Import the 'os' module to read environment variables

# --- Initialization ---
app = Flask(__name__)
CORS(app, resources={r"/suggest": {"origins": "*"}})

# THIS IS THE CRITICAL NEW SECTION:
# Get the path to the Stockfish executable from the environment variable
stockfish_path = os.environ.get("STOCKFISH_PATH", "stockfish") # Default to 'stockfish' if not found

try:
    # Initialize Stockfish with the explicit path
    stockfish = Stockfish(path=stockfish_path)
    print(f"Stockfish engine initialized successfully from path: {stockfish_path}")
except Exception as e:
    print(f"CRITICAL: Error initializing Stockfish from path '{stockfish_path}': {e}")
    stockfish = None

# --- (The rest of your code is exactly the same) ---

def format_evaluation(eval_data):
    if eval_data['type'] == 'cp':
        return f"{eval_data['value'] / 100.0:+.2f}"
    elif eval_data['type'] == 'mate':
        return f"Mate in {abs(eval_data['value'])}"
    return "N/A"

@app.route('/')
def home():
    status = "healthy" if stockfish is not None else "degraded (Stockfish not running)"
    return jsonify({ "message": "Python Chess Engine API with Stockfish is running.", "status": status })

@app.route('/suggest', methods=['POST'])
def suggest():
    if stockfish is None:
        return jsonify({"error": "Stockfish engine is not available."}), 503
    try:
        data = request.get_json()
        fen = data['fen']
        elo = int(data['elo'])

        board = chess.Board(fen)
        if board.is_game_over():
            return jsonify({ "best_move": None, "explanation": "The game is over.", "evaluation": "N/A" })

        if elo <= 1000: skill_level, depth = 1, 5
        elif elo <= 1400: skill_level, depth = 5, 8
        elif elo <= 1800: skill_level, depth = 10, 12
        elif elo <= 2200: skill_level, depth = 15, 15
        else: skill_level, depth = 20, 20

        stockfish.set_skill_level(skill_level)
        stockfish.set_depth(depth)
        stockfish.set_fen_position(fen)
        best_move = stockfish.get_best_move()

        if best_move is None:
            return jsonify({ "best_move": None, "explanation": "No legal moves available.", "evaluation": "N/A" })

        evaluation_data = stockfish.get_evaluation()
        evaluation_str = format_evaluation(evaluation_data)
        explanation = f"Stockfish (ELO approx. {elo}) suggests this move after analyzing to a depth of {depth}."

        return jsonify({
            "best_move": best_move,
            "explanation": explanation,
            "evaluation": evaluation_str
        })
    except Exception as e:
        print(f"An error occurred in /suggest: {e}")
        return jsonify({ "error": "An internal server error occurred." }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
