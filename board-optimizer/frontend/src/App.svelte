<script>
  // Board input format: "length x count x price x priority"
  let boardInputs = [
    { length: 96, count: 2, price: 0, priority: 5 },
    { length: 87, count: 2, price: 0, priority: 5 }
  ];

  // Cut input format: "length x count"
  let cutInputs = [
    { length: 27.5, count: 1 },
    { length: 25, count: 1 },
    { length: 39.75, count: 1 }
  ];

  let results = null;
  let error = null;
  let loading = false;
  let algorithm = 'auto'; // 'auto', 'exhaustive', or 'lp'
  let minRemnantLength = 0; // Minimum usable remnant length
  let kerfWidth = 0.125; // Kerf (saw blade) width

  function addBoard() {
    boardInputs = [...boardInputs, { length: 96, count: 1, price: 0, priority: 5 }];
  }

  function removeBoard(index) {
    boardInputs = boardInputs.filter((_, i) => i !== index);
  }

  function addCut() {
    cutInputs = [...cutInputs, { length: 12, count: 1 }];
  }

  function removeCut(index) {
    cutInputs = cutInputs.filter((_, i) => i !== index);
  }

  async function optimize() {
    error = null;
    results = null;
    loading = true;

    try {
      // Expand inputs: if count is 3, add 3 copies of that length
      const boards = boardInputs
        .filter(b => b.length > 0 && b.count > 0)
        .flatMap(b => Array(b.count).fill(b.length));

      const cuts = cutInputs
        .filter(c => c.length > 0 && c.count > 0)
        .flatMap(c => Array(c.count).fill(c.length));

      if (boards.length === 0) {
        throw new Error('Please enter at least one board');
      }

      if (cuts.length === 0) {
        throw new Error('Please enter at least one cut');
      }

      // Prepare board data with metadata
      const boardData = boardInputs
        .filter(b => b.length > 0 && b.count > 0)
        .flatMap(b => Array(b.count).fill({
          length: b.length,
          price: b.price || 0,
          priority: b.priority || 5
        }));

      // Call API
      const response = await fetch('/api/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          available_boards: boards,
          board_data: boardData,
          required_cuts: cuts,
          algorithm: algorithm,
          min_remnant_length: minRemnantLength,
          kerf_width: kerfWidth,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to optimize');
      }

      results = data.results;
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  function addExampleData() {
    boardInputs = [
      { length: 96, count: 2, price: 12.50, priority: 5 },
      { length: 87, count: 2, price: 10.00, priority: 7 }
    ];
    cutInputs = [
      { length: 27.5, count: 1 },
      { length: 25, count: 1 },
      { length: 39.75, count: 1 },
      { length: 42, count: 1 },
      { length: 18.5, count: 1 },
      { length: 33, count: 1 }
    ];
    minRemnantLength = 12;
    kerfWidth = 0.125;
  }

  function printSolution(result, optionNumber) {
    // Create a new window with the solution
    const printWindow = window.open('', '_blank', 'width=800,height=600');

    const boardsHtml = result.boards.map(board => {
      const cutsText = board.cuts.join('" + ');
      return `
        <div class="board">
          <div class="board-title">Board #${board.board_index + 1} (${board.original_length}")</div>
          <div class="cuts">Cuts: ${cutsText}"</div>
          <div class="remaining">Remaining: ${board.remaining}"</div>
        </div>
      `;
    }).join('');

    const html = `<!DOCTYPE html>
      <html>
      <head>
        <title>Cutting Pattern - Option ${optionNumber}</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
          }
          h1 {
            font-size: 20px;
            margin-bottom: 10px;
          }
          .stats {
            margin-bottom: 20px;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 4px;
          }
          .stat {
            display: inline-block;
            margin-right: 20px;
          }
          .board {
            margin-bottom: 15px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
          }
          .board-title {
            font-weight: bold;
            margin-bottom: 5px;
          }
          .cuts {
            margin: 5px 0;
          }
          .remaining {
            color: #666;
            font-style: italic;
          }
          @media print {
            body {
              padding: 10px;
            }
          }
        </style>
      </head>
      <body>
        <h1>Cutting Pattern - Option ${optionNumber}</h1>
        <div class="stats">
          <div class="stat"><strong>Whole boards preserved:</strong> ${result.whole_boards_kept}</div>
          <div class="stat"><strong>Longest remaining:</strong> ${result.max_remaining}"</div>
          <div class="stat"><strong>Total waste:</strong> ${result.total_waste}"</div>
        </div>
        ${boardsHtml}
      </body>
      </html>`;

    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.onload = function() {
      printWindow.print();
    };
  }
</script>

<main>
  <h1>Board Cut Optimizer</h1>

  <div class="input-section">
    <div class="input-group">
      <div class="section-header">
        <div>
          <strong>Available Boards (inches)</strong>
          <span class="help-text">Enter length, quantity, price, and priority (1-10, higher = prefer)</span>
        </div>
        <button on:click={addBoard} class="add-button">+ Add Board</button>
      </div>
      <div class="item-list">
        {#each boardInputs as board, idx}
          <div class="item-row board-row">
            <div class="input-pair">
              <div class="input-wrapper">
                <label for="board-length-{idx}">Length</label>
                <input
                  id="board-length-{idx}"
                  type="number"
                  step="0.125"
                  bind:value={board.length}
                  placeholder="96"
                />
              </div>
              <span class="times">×</span>
              <div class="input-wrapper">
                <label for="board-count-{idx}">Count</label>
                <input
                  id="board-count-{idx}"
                  type="number"
                  min="1"
                  bind:value={board.count}
                  placeholder="1"
                />
              </div>
              <span class="separator">@</span>
              <div class="input-wrapper">
                <label for="board-price-{idx}">Price ($)</label>
                <input
                  id="board-price-{idx}"
                  type="number"
                  step="0.01"
                  min="0"
                  bind:value={board.price}
                  placeholder="0.00"
                />
              </div>
              <span class="separator">•</span>
              <div class="input-wrapper input-wrapper-small">
                <label for="board-priority-{idx}">Priority</label>
                <input
                  id="board-priority-{idx}"
                  type="number"
                  min="1"
                  max="10"
                  bind:value={board.priority}
                  placeholder="5"
                />
              </div>
            </div>
            {#if boardInputs.length > 1}
              <button on:click={() => removeBoard(idx)} class="remove-button">×</button>
            {/if}
          </div>
        {/each}
      </div>
    </div>

    <div class="input-group">
      <div class="section-header">
        <div>
          <strong>Required Cuts (inches)</strong>
          <span class="help-text">Enter length and quantity for each cut</span>
        </div>
        <button on:click={addCut} class="add-button">+ Add Cut</button>
      </div>
      <div class="item-list">
        {#each cutInputs as cut, idx}
          <div class="item-row">
            <div class="input-pair">
              <div class="input-wrapper">
                <label for="cut-length-{idx}">Length</label>
                <input
                  id="cut-length-{idx}"
                  type="number"
                  step="0.125"
                  bind:value={cut.length}
                  placeholder="12"
                />
              </div>
              <span class="times">×</span>
              <div class="input-wrapper">
                <label for="cut-count-{idx}">Count</label>
                <input
                  id="cut-count-{idx}"
                  type="number"
                  min="1"
                  bind:value={cut.count}
                  placeholder="1"
                />
              </div>
            </div>
            {#if cutInputs.length > 1}
              <button on:click={() => removeCut(idx)} class="remove-button">×</button>
            {/if}
          </div>
        {/each}
      </div>
    </div>

    <div class="settings-group">
      <div class="settings-row">
        <div class="input-wrapper">
          <label for="kerf-width">
            <strong>Kerf Width (inches)</strong>
            <span class="help-text">Saw blade thickness (material lost per cut)</span>
          </label>
          <input
            id="kerf-width"
            type="number"
            step="0.001"
            min="0"
            bind:value={kerfWidth}
            placeholder="0.125"
          />
        </div>
        <div class="input-wrapper">
          <label for="min-remnant">
            <strong>Minimum Remnant Length (inches)</strong>
            <span class="help-text">Smallest usable piece (shorter = waste)</span>
          </label>
          <input
            id="min-remnant"
            type="number"
            step="0.125"
            min="0"
            bind:value={minRemnantLength}
            placeholder="0"
          />
        </div>
      </div>
    </div>

    <div class="algorithm-selector">
      <div>
        <strong>Algorithm</strong>
        <span class="help-text">Choose optimization approach</span>
      </div>
      <div class="radio-group">
        <label class="radio-label">
          <input type="radio" bind:group={algorithm} value="auto" />
          <span>Auto (recommended)</span>
          <span class="radio-description">Exhaustive for small, LP for large</span>
        </label>
        <label class="radio-label">
          <input type="radio" bind:group={algorithm} value="exhaustive" />
          <span>Exhaustive Search</span>
          <span class="radio-description">Find ALL solutions (slower for large problems)</span>
        </label>
        <label class="radio-label">
          <input type="radio" bind:group={algorithm} value="lp" />
          <span>Linear Programming</span>
          <span class="radio-description">Find optimal solutions (faster)</span>
        </label>
      </div>
    </div>

    <div class="button-group">
      <button on:click={optimize} disabled={loading}>
        {loading ? 'Optimizing...' : 'Optimize Cuts'}
      </button>
      <button on:click={addExampleData} class="secondary">
        Load Example
      </button>
    </div>
  </div>

  {#if error}
    <div class="error">
      <strong>Error:</strong> {error}
    </div>
  {/if}

  {#if loading}
    <div class="loading">
      <p>Calculating optimal cutting patterns...</p>
    </div>
  {/if}

  {#if results && results.length > 0}
    <div class="results">
      <h2>Optimization Results</h2>
      <p class="results-info">
        Found <strong>{results.length}</strong> valid cutting pattern{results.length !== 1 ? 's' : ''}.
        Results are ranked by: (1) boards preserved, (2) longest remaining piece, (3) total waste.
      </p>

      {#each results as result, idx}
        {@const maxBoardLength = Math.max(...result.boards.map(b => b.original_length))}
        <div class="result-card">
          <div class="result-header">
            <div class="result-title-row">
              <h3>Option {idx + 1}</h3>
              <button on:click={() => printSolution(result, idx + 1)} class="print-button">
                🖨️ Print
              </button>
            </div>
            <div class="result-stats">
              {#if result.total_cost !== undefined && result.total_cost > 0}
                <span class="stat stat-highlight">
                  <strong>${result.total_cost.toFixed(2)}</strong> total cost
                </span>
              {/if}
              <span class="stat">
                <strong>{result.whole_boards_kept}</strong> whole board{result.whole_boards_kept !== 1 ? 's' : ''} preserved
              </span>
              <span class="stat">
                <strong>{result.max_remaining}"</strong> longest remaining piece
              </span>
              <span class="stat">
                <strong>{result.total_waste}"</strong> total waste
              </span>
              {#if result.usable_remnants !== undefined}
                <span class="stat stat-positive">
                  <strong>{result.usable_remnants}</strong> usable remnant{result.usable_remnants !== 1 ? 's' : ''}
                </span>
              {/if}
            </div>
          </div>

          <div class="boards-list">
            {#each result.boards as board}
              <div class="board-item">
                <div class="board-header">
                  <strong>Board #{board.board_index + 1}</strong>
                  <span class="board-length">{board.original_length}"</span>
                </div>

                <!-- Visual representation of the board -->
                <div class="board-visual">
                  <div class="board-bar" style="width: {(board.original_length / maxBoardLength) * 100}%">
                    {#each board.cuts as cut}
                      <div
                        class="cut-segment"
                        style="width: {(cut / board.original_length) * 100}%"
                        title="{cut} inches"
                      >
                        <span class="cut-label">{cut}"</span>
                      </div>
                    {/each}
                    {#if board.remaining > 0}
                      <div
                        class="remaining-segment"
                        style="width: {(board.remaining / board.original_length) * 100}%"
                        title="Remaining: {board.remaining} inches"
                      >
                        <span class="remaining-label">{board.remaining}"</span>
                      </div>
                    {/if}
                  </div>
                </div>

                <div class="cuts-list">
                  <span class="label">Cuts:</span>
                  {#each board.cuts as cut, cutIdx}
                    <span class="cut-badge">{cut}"</span>
                    {#if cutIdx < board.cuts.length - 1}
                      <span class="separator">+</span>
                    {/if}
                  {/each}
                </div>
                <div class="remaining">
                  <span class="label">Remaining:</span>
                  <span class="remaining-value">{board.remaining}"</span>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</main>

<style>
  main {
    width: 100%;
  }

  .input-section {
    background: #f7fafc;
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 2rem;
  }

  .input-group {
    margin-bottom: 1.5rem;
  }

  .input-group:last-of-type {
    margin-bottom: 1rem;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  label {
    display: block;
    color: #2d3748;
  }

  .help-text {
    display: block;
    font-size: 0.875rem;
    color: #718096;
    font-weight: normal;
  }

  .add-button {
    background-color: #48bb78;
    font-size: 0.875rem;
    padding: 0.4em 0.8em;
  }

  .add-button:hover {
    background-color: #38a169;
  }

  .item-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .item-row {
    display: flex;
    gap: 0.75rem;
    align-items: flex-end;
  }

  .input-pair {
    flex: 1;
    display: flex;
    gap: 0.75rem;
    align-items: flex-end;
  }

  .input-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .input-wrapper label {
    font-size: 0.75rem;
    color: #718096;
    margin-bottom: 0.25rem;
  }

  .input-wrapper input {
    width: 100%;
  }

  .times, .separator {
    color: #a0aec0;
    font-weight: bold;
    padding-bottom: 0.5rem;
    font-size: 1.2rem;
  }

  .input-wrapper-small {
    max-width: 80px;
  }

  .board-row .input-pair {
    flex-wrap: wrap;
  }

  .settings-group {
    margin-bottom: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e2e8f0;
  }

  .settings-row {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
  }

  .settings-row .input-wrapper {
    flex: 1;
    min-width: 200px;
  }

  .remove-button {
    background-color: #fc8181;
    color: white;
    border: none;
    border-radius: 4px;
    width: 32px;
    height: 38px;
    font-size: 1.5rem;
    line-height: 1;
    cursor: pointer;
    padding: 0;
    margin-bottom: 1px;
  }

  .remove-button:hover {
    background-color: #f56565;
  }

  .algorithm-selector {
    margin-bottom: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e2e8f0;
  }

  .radio-group {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 0.5rem;
  }

  .radio-label {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.75rem;
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .radio-label:hover {
    border-color: #cbd5e0;
    background: #f7fafc;
  }

  .radio-label input[type="radio"] {
    margin-top: 0.25rem;
    cursor: pointer;
    width: auto;
  }

  .radio-label input[type="radio"]:checked {
    accent-color: #1a73e8;
  }

  .radio-label > span:first-of-type {
    flex: 1;
    font-weight: 500;
    color: #2d3748;
  }

  .radio-description {
    display: block;
    font-size: 0.75rem;
    color: #718096;
    font-weight: normal;
    margin-top: 0.25rem;
  }

  .button-group {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
  }

  button.secondary {
    background-color: #e2e8f0;
    color: #2d3748;
  }

  button.secondary:hover {
    background-color: #cbd5e0;
  }

  .results {
    margin-top: 2rem;
  }

  .results-info {
    color: #718096;
    margin-bottom: 1.5rem;
  }

  .result-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .result-header {
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e2e8f0;
  }

  .result-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .result-header h3 {
    font-size: 1.25rem;
    margin: 0;
    color: #1a202c;
  }

  .print-button {
    background-color: #4a5568;
    color: white;
    font-size: 0.875rem;
    padding: 0.5em 1em;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .print-button:hover {
    background-color: #2d3748;
  }

  .result-stats {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
  }

  .stat {
    color: #4a5568;
    font-size: 0.9rem;
  }

  .stat strong {
    color: #1a73e8;
    font-size: 1.1rem;
  }

  .stat-highlight strong {
    color: #38a169;
    font-size: 1.2rem;
  }

  .stat-positive strong {
    color: #38a169;
  }

  .boards-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .board-item {
    background: #f7fafc;
    padding: 1rem;
    border-radius: 6px;
    border-left: 4px solid #1a73e8;
  }

  .board-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .board-visual {
    margin-bottom: 1rem;
    background: white;
    padding: 0.5rem;
    border-radius: 4px;
  }

  .board-bar {
    display: flex;
    height: 50px;
    border: 2px solid #cbd5e0;
    border-radius: 4px;
    overflow: hidden;
  }

  .cut-segment {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-right: 2px solid white;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 0.8rem;
    transition: all 0.2s;
    position: relative;
  }

  .cut-segment:hover {
    filter: brightness(1.2);
    z-index: 1;
  }

  .cut-segment:last-of-type {
    border-right: none;
  }

  .cut-label {
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 0 0.25rem;
  }

  .remaining-segment {
    background: repeating-linear-gradient(
      45deg,
      #e2e8f0,
      #e2e8f0 10px,
      #edf2f7 10px,
      #edf2f7 20px
    );
    display: flex;
    align-items: center;
    justify-content: center;
    color: #4a5568;
    font-weight: 600;
    font-size: 0.8rem;
  }

  .remaining-label {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 0 0.25rem;
  }

  .board-length {
    background: #1a73e8;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.875rem;
  }

  .cuts-list {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
  }

  .label {
    color: #718096;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .cut-badge {
    background: white;
    border: 1px solid #cbd5e0;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .separator {
    color: #cbd5e0;
  }

  .remaining {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .remaining-value {
    background: #edf2f7;
    color: #2d3748;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-weight: 500;
    font-size: 0.875rem;
  }

  @media (max-width: 768px) {
    .button-group {
      flex-direction: column;
    }

    .result-stats {
      flex-direction: column;
      gap: 0.5rem;
    }
  }
</style>
