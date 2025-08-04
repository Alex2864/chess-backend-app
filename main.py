# filename: main.py (Definitive Final Version)
from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
from stockfish import Stockfish
import os

app = Flask(__name__)
CORS(app, resources={r"/suggest": {"origins": "*"}})
stockfish_path = os.environ.get("STOCKFISH_PATH", "stockfish")

try:
    stockfish = Stockfish(path=stockfish_path)
    print(f"Stockfish engine initialized successfully from path: {stockfish_path}")
except Exception as e:
    print(f"CRITICAL: Error initializing Stockfish from path '{stockfish_path}': {e}")
    stockfish = None

def get_strategic_explanation(board, best_move_uci, principal_variation_uci):
    move = chess.Move.from_uci(best_move_uci)
    simple_explanation = ""
    if board.gives_check(move): simple_explanation = "This move puts the opponent's king in check, forcing a response."
    elif board.is_capture(move):
        piece_name = chess.piece_name(board.piece_at(move.to_square).piece_type) if board.piece_at(move.to_square) else "piece"
        simple_explanation = f"This is a good move because it captures the opponent's {piece_name}."
    elif board.is_castling(move): simple_explanation = "Castling is a great move that improves king safety and connects your rooks."
    else: simple_explanation = "This is a solid move that improves your position and piece coordination."

    pv_explanation = ""
    if principal_variation_uci and len(principal_variation_uci) > 1:
        try:
            temp_board = board.copy()
            pv_moves_san = [temp_board.san(chess.Move.from_uci(m)) for m in principal_variation_uci]
            pv_explanation += f"\n\nThe engine's long-term plan is to follow with: "
            pv_explanation += f"1. You play **{pv_moves_san[0]}**. "
            if len(pv_moves_san) > 1: pv_explanation += f"Opponent will likely respond with **{pv_moves_san[1]}**. "
            if len(pv_moves_san) > 2: pv_explanation += f"You can then continue with **{pv_moves_san[2]}**. "
        except Exception as e:
            print(f"Error generating PV explanation: {e}")
            pv_explanation = ""
    return simple_explanation + pv_explanation

def format_evaluation(eval_data):
    if eval_data['type'] == 'cp': return f"{eval_data['value'] / 100.0:+.2f}"
    if eval_data['type'] == 'mate': return f"Mate in {abs(eval_data['value'])}"
    return "N/A"

@app.route('/')
def home():
    status = "healthy" if stockfish is not None else "degraded (Stockfish not running)"
    return jsonify({ "message": "Python Chess Engine API with Stockfish is running.", "status": status })

@app.route('/suggest', methods=['POST'])
def suggest():
    if stockfish is None: return jsonify({"error": "Stockfish engine is not available."}), 503
    try:
        data = request.get_json()
        fen = data['fen']
        elo = int(data['elo'])

        board = chess.Board(fen)
        if board.is_game_over(): return jsonify({ "best_move": None, "explanation": "The game is over.", "evaluation": "N/A" })

        # --- UPDATED ELO MAPPING ---
        if elo <= 1200: skill_level, depth = 3, 5
        elif elo <= 1600: skill_level, depth = 8, 8
        elif elo <= 2000: skill_level, depth = 13, 12
        elif elo <= 2500: skill_level, depth = 18, 15
        elif elo <= 3000: skill_level, depth = 20, 18 # Pro level
        else: skill_level, depth = 20, 22           # Max / Grandmaster level

        stockfish.set_skill_level(skill_level)
        stockfish.set_depth(depth)
        stockfish.set_fen_position(fen)
        top_moves = stockfish.get_top_moves(1)
        if not top_moves: return jsonify({ "best_move": None, "explanation": "No legal moves available.", "evaluation": "N/A" })

        best_move_info = top_moves[0]
        best_move_uci = best_move_info["Move"]
        principal_variation_uci = best_move_info.get("Line", {}).get("moves", [])
        explanation = get_strategic_explanation(board, best_move_uci, principal_variation_uci)
        evaluation_str = format_evaluation({"type": "cp" if best_move_info["Centipawn"] is not None else "mate", "value": best_move_info["Centipawn"] or best_move_info["Mate"]})

        return jsonify({
            "best_move": best_move_uci,
            "explanation": explanation,
            "evaluation": evaluation_str
        })
    except Exception as e:
        print(f"An error occurred in /suggest: {e}")
        return jsonify({ "error": "An internal server error occurred." }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
