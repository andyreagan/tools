# Board Cut Optimizer

A web application for optimizing board cutting patterns. Uses linear programming (PuLP) to find the best ways to cut boards while minimizing waste.

## Features

- **Advanced Optimization**: Choose between exhaustive search or linear programming
- **Cost Tracking**: Enter price per board to see total cost for each solution
- **Priority-Based Ranking**: Assign priorities (1-10) to boards to prefer certain stock
- **Kerf Width**: Account for saw blade thickness in calculations
- **Minimum Remnant Length**: Define smallest usable piece to track waste vs. usable remnants
- **Multiple Solutions**: Generates various cutting patterns ranked by:
  1. Board priority (higher priority boards preferred)
  2. Total cost (lowest first)
  3. Number of whole boards preserved (highest first)
  4. Longest remaining piece length (highest first)
- **Visual Results**: Proportional bar charts showing cuts and remaining lengths
- **Print-Friendly**: One-click print button for each solution
- **Single Server**: Svelte frontend is built and served by Flask

## Technology Stack

- **Backend**: Flask (Python)
- **Optimization**: PuLP (Linear Programming)
- **Frontend**: Svelte
- **Build Tool**: Vite

## Installation

### Prerequisites

- Python 3.8+
- Node.js 18+
- pip

### Setup

1. Clone or navigate to the project directory

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Build the frontend:
```bash
./build.sh
```

Or manually:
```bash
cd frontend
npm install
npm run build
cd ..
```

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser to:
```
http://localhost:5000
```

## Usage

1. Enter your available board lengths and quantities using the "Length × Count" format
2. Enter your required cut lengths and quantities
3. Choose your optimization algorithm:
   - **Auto (recommended)**: Automatically selects the best algorithm based on problem size
   - **Exhaustive Search**: Finds ALL possible solutions (slower for large problems)
   - **Linear Programming**: Finds optimal solutions quickly (may miss some valid patterns)
4. Click "Optimize Cuts"
5. Review the suggested cutting patterns, ranked by efficiency

## How It Works

The application uses two different algorithms depending on problem size:

### Exhaustive Search (Small Problems)
For problems with ≤8 boards and ≤15 cuts, the app uses **exhaustive backtracking** to find **ALL** valid cutting patterns:

1. **Backtracking**: Try every possible combination of cuts on each board
2. **Pruning**: Skip invalid combinations that exceed board length
3. **Deduplication**: Remove solutions that are functionally identical
4. **Ranking**: Sort by (1) boards preserved, (2) longest remaining piece, (3) total waste

This guarantees you see every possible way to make your cuts.

### Linear Programming (Large Problems)
For larger problems (>8 boards or >15 cuts), the app uses **PuLP** to find optimal solutions:

1. **Decision Variables**: Binary variables determine which cuts go on which boards
2. **Constraints**:
   - Each cut must be assigned to exactly one board
   - Total cuts on a board cannot exceed its length
   - Board usage is linked to cut assignments
3. **Multiple Objectives**: Generates solutions with different optimization goals
4. **Board Combinations**: Tries different subsets of boards to find variations

The results show you multiple options so you can choose based on your preferences (e.g., keeping whole boards intact, maximizing reusable remnants).

## Example

**Available Boards**: 96", 96", 87", 87"
**Required Cuts**: 27.5", 25", 39.75", 42", 18.5", 33"

The optimizer will find patterns like:
- **Option 1**: Uses 2 boards, preserves 2 whole boards
  - Board #1: 39.75" + 27.5" + 25" = 92.25" (3.75" remaining)
  - Board #2: 42" + 33" + 18.5" = 93.5" (2.5" remaining)

## Development

To work on the frontend with hot reloading:

```bash
cd frontend
npm run dev
```

This will start a development server on `http://localhost:5173`. Note that API calls will need the Flask backend running on port 5000.

## License

MIT
