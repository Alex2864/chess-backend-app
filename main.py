# filename: main.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
import random

# --- Initialization ---
app = Flask(__name__)
# Enable CORS to allow your frontend to communicate with this backend from any website
CORS(app)

print("Chess engine starting...")

# --- Chess Logic ---
def get_best_move_simple(board, skill_level):
    """Simple move selection based on skill level"""
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    # For higher skill levels, prefer captures and checks
    if skill_level > 15:
        good_moves = []
        for move in legal_moves:
            # Check for captures
            if board.is_capture(move):
                good_moves.append(move)
            # Check for checks (without making the move)
            if board.gives_check(move):
                good_moves.append(move)
        
        if good_moves:
            return random.choice(good_moves)

    # Otherwise, return a random legal move
    return random.choice(legal_moves)

# --- API Routes (Endpoints) ---

# This is a "health check" route. It's good practice to have one.
@app.route('/')
def home():
    return jsonify({
        "message": "Python Chess Engine API is running.",
        "status": "healthy"
    })

# This is your main endpoint that the frontend will call.
@app.route('/suggest', methods=['POST'])
def suggest():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        fen = data['fen']
        level = int(data['elo'])

        board = chess.Board(fen)
        
        if board.is_game_over():
            return jsonify({
                "best_move": None,
                "explanation": "The game is over.",
                "evaluation": "N/A"
            })

        skill_level = min(max((level - 800) // 60, 0), 20)
        best_move = get_best_move_simple(board, skill_level)
        move_uci = best_move.uci()
        explanation = f"Recommended move for ELO {level} (Skill: {skill_level}/20)."
        
        return jsonify({
            "best_move": move_uci,
            "explanation": explanation,
            "evaluation": "N/A"
        })
        
    except KeyError as e:
        return jsonify({"error": f"Missing key in request: {str(e)}"}), 400
    except Exception as e:
        print(f"An error occurred: {e}") # This will show in Render's logs for debugging
        return jsonify({"error": "An internal server error occurred."}), 500

# This part below is NOT needed by Render, but it's harmless to leave it.
# Render will use its own command to start the server.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
