 # filename: main.py (The new, smarter version)
from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
from stockfish import Stockfish

# --- Initialization ---
app = Flask(__name__)
CORS(app)

# Initialize Stockfish. The library will automatically find the engine.
# We create one instance and reuse it for efficiency.
# Parameters can be set per-move later.
try:
    stockfish = Stockfish()
    print("Stockfish engine initialized successfully.")
except Exception as e:
    print(f"Error initializing Stockfish: {e}")
    stockfish = None

# --- Helper Function ---
def format_evaluation(eval_data):
    if eval_data['type'] == 'cp':
        # Centipawns to standard pawn advantage format (e.g., +0.25)
        pawn_advantage = eval_data['value'] / 100.0
        return f"{pawn_advantage:+.2f}"
    elif eval_data['type'] == 'mate':
        # Mate in X moves
        return f"Mate in {abs(eval_data['value'])}"
    return "N/A"

# --- API Routes (Endpoints) ---

@app.route('/')
def home():
    status = "healthy" if stockfish is not None else "degraded (Stockfish not running)"
    return jsonify({
        "message": "Python Chess Engine API with Stockfish is running.",
        "status": status
    })

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
            return jsonify({
                "best_move": None,
                "explanation": "The game is over.",
                "evaluation": "N/A"
            })

        # --- Map ELO to Stockfish Skill Level (0-20) and Depth ---
        # Lower ELO means less thinking time (lower depth) and more errors (lower skill).
        if elo <= 1000:
            skill_level = 1
            depth = 5
        elif elo <= 1400:
            skill_level = 5
            depth = 8
        elif elo <= 1800:
            skill_level = 10
            depth = 12
        elif elo <= 2200:
            skill_level = 15
            depth = 15
        else: # Grandmaster level
            skill_level = 20
            depth = 20

        stockfish.set_skill_level(skill_level)
        stockfish.set_depth(depth)

        # Set the position and get the best move
        stockfish.set_fen_position(fen)
        best_move = stockfish.get_best_move()

        if best_move is None:
             return jsonify({
                "best_move": None,
                "explanation": "No legal moves available.",
                "evaluation": "N/A"
            })

        # Get the evaluation after finding the best move
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
        return jsonify({
            "error": "An internal server error occurred while analyzing the position.",
            "best_move": None,
            "explanation": str(e),
            "evaluation": "N/A"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
