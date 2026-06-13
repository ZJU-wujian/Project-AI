const BOARD_SIZE = 15;
const EMPTY = 0;
const BLACK = 1;
const WHITE = 2;

let board = [];
let currentPlayer = BLACK;
let gameMode = 'pvp'; // 'pvp' or 'pvc'
let gameOver = false;
let playerWins = 0;
let computerWins = 0;
let draws = 0;

const boardElement = document.getElementById('board');
const statusElement = document.getElementById('status');
const startGameBtn = document.getElementById('startGame');
const hintBtn = document.getElementById('hintBtn');
const modeSelect = document.getElementById('modeSelect');
const playerWinsElement = document.getElementById('playerWins');
const computerWinsElement = document.getElementById('computerWins');
const drawsElement = document.getElementById('draws');

// Load scores from localStorage
function loadScores() {
    playerWins = parseInt(localStorage.getItem('playerWins')) || 0;
    computerWins = parseInt(localStorage.getItem('computerWins')) || 0;
    draws = parseInt(localStorage.getItem('draws')) || 0;
    updateScoreDisplay();
}

// Save scores to localStorage
function saveScores() {
    localStorage.setItem('playerWins', playerWins);
    localStorage.setItem('computerWins', computerWins);
    localStorage.setItem('draws', draws);
}

// Update score display
function updateScoreDisplay() {
    playerWinsElement.textContent = playerWins;
    computerWinsElement.textContent = computerWins;
    drawsElement.textContent = draws;
}

// Initialize board
function initBoard() {
    board = Array(BOARD_SIZE).fill().map(() => Array(BOARD_SIZE).fill(EMPTY));
    boardElement.innerHTML = '';
    for (let i = 0; i < BOARD_SIZE; i++) {
        for (let j = 0; j < BOARD_SIZE; j++) {
            const cell = document.createElement('div');
            cell.classList.add('cell');
            cell.dataset.row = i;
            cell.dataset.col = j;
            cell.addEventListener('click', handleCellClick);
            boardElement.appendChild(cell);
        }
    }
}

// Handle cell click
function handleCellClick(event) {
    if (gameOver) return;
    const row = parseInt(event.target.dataset.row);
    const col = parseInt(event.target.dataset.col);
    if (board[row][col] !== EMPTY) return;

    // Check for three-three restriction for first move
    if (currentPlayer === BLACK && isThreeThree(row, col, BLACK)) {
        statusElement.textContent = '先手不能形成两个活三！';
        return;
    }

    makeMove(row, col, currentPlayer);
    if (checkWin(row, col, currentPlayer)) {
        gameOver = true;
        if (gameMode === 'pvc') {
            if (currentPlayer === BLACK) {
                playerWins++;
            } else {
                computerWins++;
            }
        } else {
            statusElement.textContent = `玩家 ${currentPlayer === BLACK ? '黑' : '白'} 获胜！`;
        }
        saveScores();
        updateScoreDisplay();
        return;
    }

    if (isDraw()) {
        gameOver = true;
        draws++;
        statusElement.textContent = '平局！';
        saveScores();
        updateScoreDisplay();
        return;
    }

    switchPlayer();
    if (gameMode === 'pvc' && currentPlayer === WHITE) {
        setTimeout(computerMove, 500);
    }
}

// Make a move
function makeMove(row, col, player) {
    board[row][col] = player;
    const cell = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
    cell.classList.add(player === BLACK ? 'black' : 'white');
    cell.textContent = player === BLACK ? '●' : '○';
}

// Switch player
function switchPlayer() {
    currentPlayer = currentPlayer === BLACK ? WHITE : BLACK;
    statusElement.textContent = `当前玩家: ${currentPlayer === BLACK ? '黑' : '白'}`;
}

// Check for win
function checkWin(row, col, player) {
    const directions = [
        [0, 1], [1, 0], [1, 1], [1, -1]
    ];
    for (const [dx, dy] of directions) {
        let count = 1;
        for (let d = 1; d <= 4; d++) {
            const x = row + dx * d;
            const y = col + dy * d;
            if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE || board[x][y] !== player) break;
            count++;
        }
        for (let d = 1; d <= 4; d++) {
            const x = row - dx * d;
            const y = col - dy * d;
            if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE || board[x][y] !== player) break;
            count++;
        }
        if (count >= 5) return true;
    }
    return false;
}

// Check for draw
function isDraw() {
    for (let i = 0; i < BOARD_SIZE; i++) {
        for (let j = 0; j < BOARD_SIZE; j++) {
            if (board[i][j] === EMPTY) return false;
        }
    }
    return true;
}

// Check for three-three
function isThreeThree(row, col, player) {
    let threeCount = 0;
    const directions = [
        [0, 1], [1, 0], [1, 1], [1, -1]
    ];
    for (const [dx, dy] of directions) {
        if (isThreeInDirection(row, col, dx, dy, player)) threeCount++;
        if (isThreeInDirection(row, col, -dx, -dy, player)) threeCount++;
    }
    return threeCount >= 2;
}

// Check for three in direction
function isThreeInDirection(row, col, dx, dy, player) {
    let count = 1;
    let emptyEnds = 0;
    // Forward
    for (let d = 1; d <= 3; d++) {
        const x = row + dx * d;
        const y = col + dy * d;
        if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE) break;
        if (board[x][y] === player) count++;
        else if (board[x][y] === EMPTY) {
            emptyEnds++;
            break;
        } else break;
    }
    // Backward
    for (let d = 1; d <= 3; d++) {
        const x = row - dx * d;
        const y = col - dy * d;
        if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE) break;
        if (board[x][y] === player) count++;
        else if (board[x][y] === EMPTY) {
            emptyEnds++;
            break;
        } else break;
    }
    return count === 3 && emptyEnds === 2;
}

// Computer move (simple AI)
function computerMove() {
    let bestScore = -Infinity;
    let bestMove = null;
    for (let i = 0; i < BOARD_SIZE; i++) {
        for (let j = 0; j < BOARD_SIZE; j++) {
            if (board[i][j] === EMPTY) {
                board[i][j] = WHITE;
                const score = evaluateBoard();
                board[i][j] = EMPTY;
                if (score > bestScore) {
                    bestScore = score;
                    bestMove = [i, j];
                }
            }
        }
    }
    if (bestMove) {
        makeMove(bestMove[0], bestMove[1], WHITE);
        if (checkWin(bestMove[0], bestMove[1], WHITE)) {
            gameOver = true;
            computerWins++;
            statusElement.textContent = '电脑获胜！';
            saveScores();
            updateScoreDisplay();
            return;
        }
        switchPlayer();
    }
}

// Evaluate board for AI
function evaluateBoard() {
    let score = 0;
    // Simple evaluation: count potential lines
    for (let i = 0; i < BOARD_SIZE; i++) {
        for (let j = 0; j < BOARD_SIZE; j++) {
            if (board[i][j] !== EMPTY) {
                score += evaluatePosition(i, j, board[i][j]);
            }
        }
    }
    return score;
}

// Evaluate position
function evaluatePosition(row, col, player) {
    let score = 0;
    const directions = [
        [0, 1], [1, 0], [1, 1], [1, -1]
    ];
    for (const [dx, dy] of directions) {
        let count = 1;
        let blocked = 0;
        // Forward
        for (let d = 1; d <= 4; d++) {
            const x = row + dx * d;
            const y = col + dy * d;
            if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE) {
                blocked++;
                break;
            }
            if (board[x][y] === player) count++;
            else if (board[x][y] === EMPTY) break;
            else {
                blocked++;
                break;
            }
        }
        // Backward
        for (let d = 1; d <= 4; d++) {
            const x = row - dx * d;
            const y = col - dy * d;
            if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE) {
                blocked++;
                break;
            }
            if (board[x][y] === player) count++;
            else if (board[x][y] === EMPTY) break;
            else {
                blocked++;
                break;
            }
        }
        if (blocked < 2) {
            score += Math.pow(10, count);
        }
    }
    return score;
}

// Hint function
function getHint() {
    if (gameOver) return;
    let bestScore = -Infinity;
    let bestMove = null;
    for (let i = 0; i < BOARD_SIZE; i++) {
        for (let j = 0; j < BOARD_SIZE; j++) {
            if (board[i][j] === EMPTY) {
                board[i][j] = currentPlayer;
                const score = evaluateBoard();
                board[i][j] = EMPTY;
                if (score > bestScore) {
                    bestScore = score;
                    bestMove = [i, j];
                }
            }
        }
    }
    if (bestMove) {
        const cell = document.querySelector(`[data-row="${bestMove[0]}"][data-col="${bestMove[1]}"]`);
        cell.style.background = 'yellow';
        setTimeout(() => {
            cell.style.background = '';
        }, 2000);
        statusElement.textContent = `提示: 推荐落子 (${bestMove[0] + 1}, ${bestMove[1] + 1})`;
    }
}

// Start game
function startGame() {
    gameOver = false;
    currentPlayer = BLACK;
    initBoard();
    statusElement.textContent = '游戏开始！当前玩家: 黑';
}

// Event listeners
startGameBtn.addEventListener('click', startGame);
hintBtn.addEventListener('click', getHint);
modeSelect.addEventListener('change', (e) => {
    gameMode = e.target.value;
});

// Initialize
loadScores();
initBoard();