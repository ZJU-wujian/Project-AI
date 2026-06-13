const canvas = document.getElementById('gameBoard');
const ctx = canvas.getContext('2d');
const nextCanvas = document.getElementById('nextPiece');
const nextCtx = nextCanvas.getContext('2d');
const particleCanvas = document.getElementById('particleCanvas');
const particleCtx = particleCanvas.getContext('2d');

if (!CanvasRenderingContext2D.prototype.roundRect) {
   CanvasRenderingContext2D.prototype.roundRect = function(x, y, w, h, r) {
      if (w < 2 * r) r = w / 2;
      if (h < 2 * r) r = h / 2;
      this.beginPath();
      this.moveTo(x + r, y);
      this.arcTo(x + w, y, x + w, y + h, r);
      this.arcTo(x + w, y + h, x, y + h, r);
      this.arcTo(x, y + h, x, y, r);
      this.arcTo(x, y, x + w, y, r);
      this.closePath();
      return this;
   };
}

const COLS = 10;
const ROWS = 20;
const BLOCK_SIZE = 30;

canvas.width = COLS * BLOCK_SIZE;
canvas.height = ROWS * BLOCK_SIZE;
particleCanvas.width = canvas.width;
particleCanvas.height = canvas.height;

const COLORS = {
   I: '#55efc4',
   O: '#ffeaa7',
   T: '#a29bfe',
   S: '#81ecec',
   Z: '#ff7675',
   J: '#74b9ff',
   L: '#fab1a0'
};

const SHAPES = {
   I: [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
   O: [[1,1],[1,1]],
   T: [[0,1,0],[1,1,1],[0,0,0]],
   S: [[0,1,1],[1,1,0],[0,0,0]],
   Z: [[1,1,0],[0,1,1],[0,0,0]],
   J: [[1,0,0],[1,1,1],[0,0,0]],
   L: [[0,0,1],[1,1,1],[0,0,0]]
};

let board = [];
let currentPiece = null;
let nextPieceType = null;
let score = 0;
let level = 1;
let lines = 0;
let highScore = parseInt(localStorage.getItem('tetrisHighScore')) || 0;
let gameLoop = null;
let dropInterval = 800;
let isPlaying = false;
let isPaused = false;
let isGameOver = false;
let particles = [];
let bag = [];

document.getElementById('highScore').textContent = highScore;

function createBoard() {
   board = [];
   for (let y = 0; y < ROWS; y++) {
      board[y] = [];
      for (let x = 0; x < COLS; x++) {
         board[y][x] = null;
      }
   }
}

function getFromBag() {
   if (bag.length === 0) {
      bag = ['I', 'O', 'T', 'S', 'Z', 'J', 'L'];
      for (let i = bag.length - 1; i > 0; i--) {
         const j = Math.floor(Math.random() * (i + 1));
         [bag[i], bag[j]] = [bag[j], bag[i]];
      }
   }
   return bag.pop();
}

function createPiece(type) {
   const shape = SHAPES[type].map(row => [...row]);
   return {
      type,
      shape,
      x: Math.floor((COLS - shape[0].length) / 2),
      y: 0,
      rotation: 0
   };
}

function rotate(shape) {
   const N = shape.length;
   const rotated = [];
   for (let y = 0; y < N; y++) {
      rotated[y] = [];
      for (let x = 0; x < N; x++) {
         rotated[y][x] = shape[N - 1 - x][y];
      }
   }
   return rotated;
}

function isValidPosition(piece, offsetX = 0, offsetY = 0, shape = null) {
   const s = shape || piece.shape;
   for (let y = 0; y < s.length; y++) {
      for (let x = 0; x < s[y].length; x++) {
         if (s[y][x]) {
            const newX = piece.x + x + offsetX;
            const newY = piece.y + y + offsetY;
            if (newX < 0 || newX >= COLS || newY >= ROWS) return false;
            if (newY >= 0 && board[newY][newX]) return false;
         }
      }
   }
   return true;
}

function placePiece() {
   const s = currentPiece.shape;
   for (let y = 0; y < s.length; y++) {
      for (let x = 0; x < s[y].length; x++) {
         if (s[y][x]) {
            const boardY = currentPiece.y + y;
            const boardX = currentPiece.x + x;
            if (boardY >= 0 && boardY < ROWS) {
               board[boardY][boardX] = currentPiece.type;
            }
         }
      }
   }
   document.querySelector('.board-wrapper').classList.add('shake');
   setTimeout(() => {
      document.querySelector('.board-wrapper').classList.remove('shake');
   }, 150);
}

function clearLines() {
   let cleared = 0;
   const clearedRows = [];

   for (let y = ROWS - 1; y >= 0; y--) {
      if (board[y].every(cell => cell !== null)) {
         clearedRows.push(y);
         for (let x = 0; x < COLS; x++) {
            createParticles(x * BLOCK_SIZE + BLOCK_SIZE / 2, y * BLOCK_SIZE + BLOCK_SIZE / 2, COLORS[board[y][x]] || '#ffffff');
         }
      }
   }

   if (clearedRows.length > 0) {
      clearedRows.sort((a, b) => b - a);
      for (const row of clearedRows) {
         board.splice(row, 1);
         const newRow = [];
         for (let x = 0; x < COLS; x++) {
            newRow.push(null);
         }
         board.unshift(newRow);
         cleared++;
      }

      const points = [0, 100, 300, 500, 800];
      score += (points[cleared] || 800) * level;
      lines += cleared;

      const newLevel = Math.floor(lines / 10) + 1;
      if (newLevel !== level) {
         level = newLevel;
         updateDropInterval();
      }

      updateUI();
   }
}

function updateDropInterval() {
   const intervals = [800, 700, 600, 500, 400, 300, 200, 150, 100, 50];
   dropInterval = intervals[Math.min(level - 1, intervals.length - 1)];
   if (gameLoop) {
      clearInterval(gameLoop);
      gameLoop = setInterval(gameStep, dropInterval);
   }
}

function getGhostPosition() {
   if (!currentPiece) return null;
   let ghostY = 0;
   while (isValidPosition(currentPiece, 0, ghostY + 1)) {
      ghostY++;
   }
   return ghostY;
}

function gameStep() {
   if (!isPlaying || isPaused || isGameOver) return;

   if (isValidPosition(currentPiece, 0, 1)) {
      currentPiece.y++;
   } else {
      placePiece();
      clearLines();
      spawnPiece();
   }

   draw();
}

function spawnPiece() {
   currentPiece = createPiece(nextPieceType || getFromBag());
   nextPieceType = getFromBag();

   if (!isValidPosition(currentPiece)) {
      gameOver();
   }

   drawNextPiece();
}

function gameOver() {
   isPlaying = false;
   isGameOver = true;
   if (gameLoop) clearInterval(gameLoop);

   if (score > highScore) {
      highScore = score;
      localStorage.setItem('tetrisHighScore', highScore);
      document.getElementById('highScore').textContent = highScore;
   }

   showOverlay('游戏结束', `最终分数: ${score}`, '重新开始');
}

function drawBlock(context, x, y, color, size = BLOCK_SIZE, ghost = false) {
   const padding = 2;
   const blockX = x * size + padding;
   const blockY = y * size + padding;
   const blockSize = size - padding * 2;
   const radius = 4;

   if (ghost) {
      context.fillStyle = color;
      context.globalAlpha = 0.15;
      context.beginPath();
      context.roundRect(blockX, blockY, blockSize, blockSize, radius);
      context.fill();
      context.globalAlpha = 1;
      return;
    }

   context.fillStyle = color;
   context.beginPath();
   context.roundRect(blockX, blockY, blockSize, blockSize, radius);
   context.fill();

   const gradient = context.createLinearGradient(blockX, blockY, blockX + blockSize, blockY + blockSize);
   gradient.addColorStop(0, 'rgba(255, 255, 255, 0.25)');
   gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0)');
   gradient.addColorStop(1, 'rgba(0, 0, 0, 0.1)');
   context.fillStyle = gradient;
   context.beginPath();
   context.roundRect(blockX, blockY, blockSize, blockSize, radius);
   context.fill();

   context.fillStyle = 'rgba(255, 255, 255, 0.5)';
   context.beginPath();
   context.roundRect(blockX + 2, blockY + 2, blockSize - 4, 2, 1);
   context.fill();
}

function drawGrid() {
   ctx.strokeStyle = 'rgba(100, 100, 180, 0.1)';
   ctx.lineWidth = 0.5;

   for (let x = 0; x <= COLS; x++) {
      ctx.beginPath();
      ctx.moveTo(x * BLOCK_SIZE, 0);
      ctx.lineTo(x * BLOCK_SIZE, ROWS * BLOCK_SIZE);
      ctx.stroke();
   }

   for (let y = 0; y <= ROWS; y++) {
      ctx.beginPath();
      ctx.moveTo(0, y * BLOCK_SIZE);
      ctx.lineTo(COLS * BLOCK_SIZE, y * BLOCK_SIZE);
      ctx.stroke();
   }
}

function draw() {
   ctx.clearRect(0, 0, canvas.width, canvas.height);

   drawGrid();

   for (let y = 0; y < ROWS; y++) {
      for (let x = 0; x < COLS; x++) {
         if (board[y][x]) {
            drawBlock(ctx, x, y, COLORS[board[y][x]]);
         }
      }
   }

   if (currentPiece && isPlaying && !isPaused) {
      const ghostOffset = getGhostPosition();
      if (ghostOffset > 0) {
         const s = currentPiece.shape;
         for (let y = 0; y < s.length; y++) {
            for (let x = 0; x < s[y].length; x++) {
               if (s[y][x]) {
                  drawBlock(ctx, currentPiece.x + x, currentPiece.y + y + ghostOffset, COLORS[currentPiece.type], BLOCK_SIZE, true);
               }
            }
         }
      }

      const s = currentPiece.shape;
      for (let y = 0; y < s.length; y++) {
         for (let x = 0; x < s[y].length; x++) {
            if (s[y][x]) {
               drawBlock(ctx, currentPiece.x + x, currentPiece.y + y, COLORS[currentPiece.type]);
            }
         }
      }
   }
}

function drawNextPiece() {
   nextCtx.clearRect(0, 0, nextCanvas.width, nextCanvas.height);

   if (!nextPieceType) return;

   const shape = SHAPES[nextPieceType];
   const color = COLORS[nextPieceType];
   const blockSize = 25;

   const pieceWidth = shape[0].length * blockSize;
   const pieceHeight = shape.length * blockSize;
   const offsetX = (nextCanvas.width - pieceWidth) / 2;
   const offsetY = (nextCanvas.height - pieceHeight) / 2;

   for (let y = 0; y < shape.length; y++) {
      for (let x = 0; x < shape[y].length; x++) {
         if (shape[y][x]) {
            const px = offsetX / blockSize + x;
            const py = offsetY / blockSize + y;

            nextCtx.fillStyle = color;
            nextCtx.shadowColor = color;
            nextCtx.shadowBlur = 8;
            nextCtx.fillRect(offsetX + x * blockSize + 1, offsetY + y * blockSize + 1, blockSize - 2, blockSize - 2);

            nextCtx.shadowBlur = 0;
            const gradient = nextCtx.createLinearGradient(offsetX + x * blockSize, offsetY + y * blockSize, offsetX + (x + 1) * blockSize, offsetY + (y + 1) * blockSize);
            gradient.addColorStop(0, 'rgba(255, 255, 255, 0.3)');
            gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0)');
            gradient.addColorStop(1, 'rgba(0, 0, 0, 0.2)');
            nextCtx.fillStyle = gradient;
            nextCtx.fillRect(offsetX + x * blockSize + 1, offsetY + y * blockSize + 1, blockSize - 2, blockSize - 2);
         }
      }
   }
}

function updateUI() {
   document.getElementById('score').textContent = score;
   document.getElementById('level').textContent = level;
   document.getElementById('lines').textContent = lines;

   const progressInLevel = (lines % 10) / 10 * 100;
   document.getElementById('levelProgress').style.width = `${progressInLevel}%`;
}

function createParticles(x, y, color) {
   for (let i = 0; i < 8; i++) {
      particles.push({
         x, y,
         vx: (Math.random() - 0.5) * 8,
         vy: (Math.random() - 0.5) * 8 - 2,
         life: 1,
         decay: 0.02 + Math.random() * 0.02,
         size: 2 + Math.random() * 3,
         color
      });
   }
}

function updateParticles() {
   particleCtx.clearRect(0, 0, particleCanvas.width, particleCanvas.height);

   for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.1;
      p.life -= p.decay;

      if (p.life <= 0) {
         particles.splice(i, 1);
         continue;
      }

      particleCtx.globalAlpha = p.life;
      particleCtx.fillStyle = p.color;
      particleCtx.shadowColor = p.color;
      particleCtx.shadowBlur = 10;
      particleCtx.beginPath();
      particleCtx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      particleCtx.fill();
   }

   particleCtx.globalAlpha = 1;
   particleCtx.shadowBlur = 0;

   requestAnimationFrame(updateParticles);
}

function showOverlay(title, message, btnText) {
   const overlay = document.getElementById('overlay');
   document.getElementById('overlayTitle').textContent = title;
   document.getElementById('overlayMessage').textContent = message;
   document.getElementById('startBtn').textContent = btnText;
   overlay.classList.remove('hidden');
}

function hideOverlay() {
   document.getElementById('overlay').classList.add('hidden');
}

function startGame() {
   createBoard();
   score = 0;
   level = 1;
   lines = 0;
   isPlaying = true;
   isPaused = false;
   isGameOver = false;
   bag = [];
   nextPieceType = null;
   dropInterval = 800;
   updateUI();
   hideOverlay();
   spawnPiece();
   draw();

   if (gameLoop) clearInterval(gameLoop);
   gameLoop = setInterval(gameStep, dropInterval);
}

function togglePause() {
   if (!isPlaying || isGameOver) return;

   isPaused = !isPaused;
   if (isPaused) {
      showOverlay('已暂停', '点击继续游戏', '继续');
   } else {
      hideOverlay();
   }
}

document.getElementById('startBtn').addEventListener('click', () => {
   if (isPaused) {
      togglePause();
   } else {
      startGame();
   }
});

document.getElementById('pauseBtn').addEventListener('click', togglePause);

document.getElementById('resetBtn').addEventListener('click', () => {
   if (gameLoop) clearInterval(gameLoop);
   isPlaying = false;
   isPaused = false;
   isGameOver = false;
   currentPiece = null;
   createBoard();
   score = 0;
   level = 1;
   lines = 0;
   updateUI();
   draw();
   showOverlay('俄罗斯方块', '准备好了吗？', '开始游戏');
});

document.addEventListener('keydown', (e) => {
   if (!isPlaying || isPaused || isGameOver) {
      if (e.key === 'p' || e.key === 'P') {
         togglePause();
      }
      return;
   }

   switch (e.key) {
      case 'ArrowLeft':
         if (isValidPosition(currentPiece, -1, 0)) {
            currentPiece.x--;
         }
         break;
      case 'ArrowRight':
         if (isValidPosition(currentPiece, 1, 0)) {
            currentPiece.x++;
         }
         break;
      case 'ArrowDown':
         if (isValidPosition(currentPiece, 0, 1)) {
            currentPiece.y++;
            score += 1;
            updateUI();
         }
         break;
      case 'ArrowUp':
         const rotated = rotate(currentPiece.shape);
         if (isValidPosition(currentPiece, 0, 0, rotated)) {
            currentPiece.shape = rotated;
            currentPiece.rotation = (currentPiece.rotation + 1) % 4;
         }
         break;
      case ' ':
         e.preventDefault();
         let dropDistance = 0;
         while (isValidPosition(currentPiece, 0, dropDistance + 1)) {
            dropDistance++;
         }
         currentPiece.y += dropDistance;
         score += dropDistance * 2;
         updateUI();
         placePiece();
         clearLines();
         spawnPiece();
         break;
      case 'p':
      case 'P':
         togglePause();
         break;
   }

   draw();
});

const addMobileControl = (btnId, handler) => {
   const btn = document.getElementById(btnId);
   if (!btn) return;

   let interval = null;

   const start = (e) => {
      e.preventDefault();
      handler();
      draw();
   };

   btn.addEventListener('touchstart', start, { passive: false });
   btn.addEventListener('mousedown', start);
};

addMobileControl('btnLeft', () => {
   if (currentPiece && isValidPosition(currentPiece, -1, 0)) {
      currentPiece.x--;
   }
});

addMobileControl('btnRight', () => {
   if (currentPiece && isValidPosition(currentPiece, 1, 0)) {
      currentPiece.x++;
   }
});

addMobileControl('btnRotate', () => {
   if (currentPiece) {
      const rotated = rotate(currentPiece.shape);
      if (isValidPosition(currentPiece, 0, 0, rotated)) {
         currentPiece.shape = rotated;
         currentPiece.rotation = (currentPiece.rotation + 1) % 4;
      }
   }
});

addMobileControl('btnDown', () => {
   if (currentPiece && isValidPosition(currentPiece, 0, 1)) {
      currentPiece.y++;
      score += 1;
      updateUI();
   }
});

addMobileControl('btnDrop', () => {
   if (!currentPiece) return;
   let dropDistance = 0;
   while (isValidPosition(currentPiece, 0, dropDistance + 1)) {
      dropDistance++;
   }
   currentPiece.y += dropDistance;
   score += dropDistance * 2;
   updateUI();
   placePiece();
   clearLines();
   spawnPiece();
});

updateParticles();

createBoard();
draw();

const mobileControls = document.getElementById('mobileControls');
if (window.innerWidth <= 768) {
   mobileControls.style.display = 'flex';
}

window.addEventListener('resize', () => {
   if (window.innerWidth <= 768) {
      mobileControls.style.display = 'flex';
   } else {
      mobileControls.style.display = 'none';
   }
});
