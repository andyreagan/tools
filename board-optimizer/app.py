# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "flask==3.0.0",
#     "pulp==2.7.0",
# ]
# ///

from flask import Flask, jsonify, request, send_from_directory
import os
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, value, LpStatus
from typing import List, Dict
from itertools import product

app = Flask(__name__, static_folder='frontend/dist', static_url_path='')

def optimize_cuts(available_boards: List[float], required_cuts: List[float]) -> List[Dict]:
    """
    Auto-select algorithm based on problem size.
    Uses exhaustive search for small problems, LP for large ones.
    """
    # For efficiency, limit search if there are too many boards/cuts
    if len(available_boards) > 8 or len(required_cuts) > 15:
        return optimize_cuts_lp(available_boards, required_cuts)
    else:
        return optimize_cuts_exhaustive(available_boards, required_cuts)

def optimize_cuts_exhaustive(available_boards: List[float], required_cuts: List[float]) -> List[Dict]:
    """
    Find all valid cutting combinations using exhaustive search with backtracking.
    Returns all solutions ranked by:
    1. Number of whole boards kept (descending)
    2. Longest remaining length (descending)
    3. Total waste (ascending)
    """
    all_solutions = []

    # Use backtracking to find all valid solutions
    def backtrack(board_idx: int, remaining_boards: List[float], remaining_cuts: List[float],
                  current_assignment: List[List[float]], board_indices: List[int]):
        # Base case: all cuts have been assigned
        if not remaining_cuts:
            # Record this solution
            solution = create_solution_dict(available_boards, current_assignment, board_indices)
            if solution:
                # Check if this is a unique solution (different cut distribution)
                if not is_duplicate_solution(solution, all_solutions):
                    all_solutions.append(solution)
            return

        # If we've tried all boards and still have cuts, this path fails
        if board_idx >= len(remaining_boards):
            return

        # Try assigning different subsets of remaining cuts to current board
        board_length = remaining_boards[board_idx]

        # Generate all valid combinations of cuts that fit on this board
        valid_combos = find_valid_combinations(remaining_cuts, board_length)

        for combo in valid_combos:
            # Assign this combination to current board
            new_assignment = [row[:] for row in current_assignment]
            new_assignment[board_idx] = combo

            # Remove used cuts from remaining
            new_remaining_cuts = remaining_cuts[:]
            for cut in combo:
                new_remaining_cuts.remove(cut)

            # Continue with next board
            backtrack(board_idx + 1, remaining_boards, new_remaining_cuts,
                     new_assignment, board_indices)

        # Also try skipping this board (leaving it empty)
        backtrack(board_idx + 1, remaining_boards, remaining_cuts, current_assignment, board_indices)

    # Start backtracking
    initial_assignment = [[] for _ in available_boards]
    board_indices = list(range(len(available_boards)))

    backtrack(0, available_boards, required_cuts, initial_assignment, board_indices)

    # Sort by: whole boards kept (desc), max remaining (desc), total waste (asc)
    all_solutions.sort(key=lambda x: (x['whole_boards_kept'], x['max_remaining'], -x['total_waste']),
                       reverse=True)

    # Return top 50 solutions
    return all_solutions[:50]

def find_valid_combinations(cuts: List[float], max_length: float) -> List[List[float]]:
    """Find all valid combinations of cuts that fit within max_length"""
    from itertools import combinations

    valid_combos = [[]]  # Include empty combination

    # Try all possible subset sizes
    for size in range(1, len(cuts) + 1):
        for combo in combinations(cuts, size):
            if sum(combo) <= max_length:
                valid_combos.append(list(combo))

    return valid_combos

def is_duplicate_solution(solution: Dict, solutions: List[Dict]) -> bool:
    """Check if this solution is essentially the same as an existing one"""
    for existing in solutions:
        if len(solution['boards']) != len(existing['boards']):
            continue

        # Compare the cut distributions (order-independent)
        solution_cuts = sorted([tuple(sorted(b['cuts'])) for b in solution['boards'] if b['cuts']])
        existing_cuts = sorted([tuple(sorted(b['cuts'])) for b in existing['boards'] if b['cuts']])

        if solution_cuts == existing_cuts:
            return True

    return False

def create_solution_dict(available_boards: List[float], assignment: List[List[float]],
                        board_indices: List[int]) -> Dict:
    """Create a solution dictionary from an assignment"""
    board_details = []
    remaining_lengths = []
    boards_used = 0

    for i, (board_length, cuts) in enumerate(zip(available_boards, assignment)):
        if cuts:
            boards_used += 1
            total_cut = sum(cuts)
            remaining = board_length - total_cut
            remaining_lengths.append(remaining)

            board_details.append({
                'board_index': board_indices[i],
                'original_length': board_length,
                'cuts': sorted(cuts, reverse=True),
                'remaining': round(remaining, 2)
            })

    if not board_details:
        return None

    max_remaining = max(remaining_lengths) if remaining_lengths else 0
    whole_boards_kept = len(available_boards) - boards_used

    return {
        'board_indices': [bd['board_index'] for bd in board_details],
        'boards': board_details,
        'whole_boards_kept': whole_boards_kept,
        'max_remaining': round(max_remaining, 2),
        'total_waste': round(sum(remaining_lengths), 2)
    }

def optimize_cuts_lp(available_boards: List[float], required_cuts: List[float]) -> List[Dict]:
    """LP-based optimization for larger problems"""
    results = []

    # Try different board subsets
    from itertools import combinations

    # Solution 1: Use all boards, minimize waste
    solution = solve_with_lp(available_boards, required_cuts, minimize_boards=True)
    if solution:
        results.append(solution)

    # Solution 2: Minimize boards used
    solution = solve_with_lp(available_boards, required_cuts, minimize_boards=False)
    if solution and not is_duplicate_solution(solution, results):
        results.append(solution)

    # Try different board combinations
    for num_boards in range(len(available_boards) - 1, max(1, len(available_boards) - 5), -1):
        for board_combo in list(combinations(range(len(available_boards)), num_boards))[:20]:
            subset_boards = [available_boards[i] for i in board_combo]
            solution = solve_with_lp(subset_boards, required_cuts, minimize_boards=False,
                                    board_indices=list(board_combo))
            if solution and not is_duplicate_solution(solution, results):
                results.append(solution)
                if len(results) >= 50:
                    break
        if len(results) >= 50:
            break

    results.sort(key=lambda x: (x['whole_boards_kept'], x['max_remaining'], -x['total_waste']),
                 reverse=True)

    return results[:50]

def solve_with_lp(available_boards: List[float], required_cuts: List[float],
                  minimize_boards: bool = True, board_indices: List[int] = None) -> Dict:
    """
    Solve the cutting stock problem using linear programming with PuLP.
    """
    if board_indices is None:
        board_indices = list(range(len(available_boards)))

    n_boards = len(available_boards)
    n_cuts = len(required_cuts)

    # Create the problem
    prob = LpProblem("Board_Cutting", LpMinimize)

    # Decision variables: x[i][j] = 1 if cut j is assigned to board i
    x = [[LpVariable(f"x_{i}_{j}", cat=LpBinary) for j in range(n_cuts)]
         for i in range(n_boards)]

    # Variable: y[i] = 1 if board i is used
    y = [LpVariable(f"y_{i}", cat=LpBinary) for i in range(n_boards)]

    # Constraint: Each cut must be assigned to exactly one board
    for j in range(n_cuts):
        prob += lpSum(x[i][j] for i in range(n_boards)) == 1, f"Cut_{j}_assigned"

    # Constraint: Total cuts on a board cannot exceed board length
    for i in range(n_boards):
        prob += lpSum(required_cuts[j] * x[i][j] for j in range(n_cuts)) <= available_boards[i], f"Board_{i}_capacity"

    # Constraint: Link board usage with cut assignment
    for i in range(n_boards):
        for j in range(n_cuts):
            prob += x[i][j] <= y[i], f"Link_{i}_{j}"

    # Objective: Minimize number of boards used or minimize waste
    if minimize_boards:
        prob += lpSum(y[i] for i in range(n_boards))
    else:
        # Minimize waste (maximize utilization)
        prob += -lpSum(required_cuts[j] * x[i][j] for i in range(n_boards) for j in range(n_cuts))

    # Solve
    prob.solve()

    if LpStatus[prob.status] == 'Optimal':
        # Extract solution
        board_details = []
        boards_used = 0
        remaining_lengths = []

        for i in range(n_boards):
            cuts_made = []
            for j in range(n_cuts):
                if value(x[i][j]) == 1:
                    cuts_made.append(required_cuts[j])

            if cuts_made:
                boards_used += 1
                total_cut = sum(cuts_made)
                remaining = available_boards[i] - total_cut
                remaining_lengths.append(remaining)

                board_details.append({
                    'board_index': board_indices[i],
                    'original_length': available_boards[i],
                    'cuts': sorted(cuts_made, reverse=True),
                    'remaining': round(remaining, 2)
                })

        max_remaining = max(remaining_lengths) if remaining_lengths else 0
        whole_boards_kept = n_boards - boards_used

        return {
            'board_indices': [bd['board_index'] for bd in board_details],
            'boards': board_details,
            'whole_boards_kept': whole_boards_kept,
            'max_remaining': round(max_remaining, 2),
            'total_waste': round(sum(remaining_lengths), 2)
        }

    return None

@app.route('/')
def serve_app():
    """Serve the Svelte app"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/optimize', methods=['POST'])
def optimize():
    """API endpoint for board optimization"""
    try:
        data = request.json
        available_boards = data.get('available_boards', [])
        board_data = data.get('board_data', [])
        required_cuts = data.get('required_cuts', [])
        algorithm = data.get('algorithm', 'auto')
        min_remnant_length = data.get('min_remnant_length', 0)
        kerf_width = data.get('kerf_width', 0.125)

        if not available_boards or not required_cuts:
            return jsonify({'error': 'Please provide both available boards and required cuts'}), 400

        # Validate inputs
        try:
            available_boards = [float(x) for x in available_boards]
            required_cuts = [float(x) for x in required_cuts]
            min_remnant_length = float(min_remnant_length)
            kerf_width = float(kerf_width)
        except (ValueError, TypeError):
            return jsonify({'error': 'All measurements must be valid numbers'}), 400

        # Account for kerf width in cuts
        cuts_with_kerf = [cut + kerf_width for cut in required_cuts]

        # Check if cuts can possibly fit
        total_needed = sum(cuts_with_kerf)
        total_available = sum(available_boards)

        if total_needed > total_available:
            return jsonify({
                'error': f'Total cuts needed ({total_needed}") (including kerf) exceeds available board length ({total_available}")'
            }), 400

        # Create board metadata map
        board_metadata = {}
        if board_data and len(board_data) == len(available_boards):
            for i, meta in enumerate(board_data):
                board_metadata[i] = {
                    'price': meta.get('price', 0),
                    'priority': meta.get('priority', 5)
                }

        # Choose algorithm based on user selection
        if algorithm == 'exhaustive':
            results = optimize_cuts_exhaustive(available_boards, cuts_with_kerf)
        elif algorithm == 'lp':
            results = optimize_cuts_lp(available_boards, cuts_with_kerf)
        else:  # 'auto'
            results = optimize_cuts(available_boards, cuts_with_kerf)

        if not results:
            return jsonify({'error': 'No valid cutting combinations found'}), 404

        # Post-process results: add cost, usable remnants, and re-sort by priority
        for result in results:
            total_cost = 0
            usable_remnants = 0
            total_priority_score = 0

            for board in result['boards']:
                board_idx = board['board_index']
                if board_idx in board_metadata:
                    total_cost += board_metadata[board_idx]['price']
                    total_priority_score += board_metadata[board_idx]['priority']

                # Check if remnant is usable
                if board['remaining'] >= min_remnant_length:
                    usable_remnants += 1

            result['total_cost'] = round(total_cost, 2)
            result['usable_remnants'] = usable_remnants
            result['priority_score'] = total_priority_score

        # Re-sort by: priority (desc), cost (asc), whole boards kept (desc), max remaining (desc)
        results.sort(key=lambda x: (-x.get('priority_score', 0),
                                     x.get('total_cost', 999999),
                                     -x['whole_boards_kept'],
                                     -x['max_remaining']))

        return jsonify({
            'success': True,
            'results': results[:50]  # Return top 50 results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
