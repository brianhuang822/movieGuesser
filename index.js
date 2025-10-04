// State management
let allMovies = [];
let currentMovie = null;
let isRevealed = false;

// DOM elements
const movieContainer = document.getElementById('movieContainer');
const getMovieBtn = document.getElementById('getMovieBtn');
const minYearInput = document.getElementById('minYear');
const maxYearInput = document.getElementById('maxYear');
const themeButtons = document.querySelectorAll('.theme-btn');

// Initialize
async function init() {
    setupThemeToggle();
    loadTheme();
    await loadMovies();
    setupEventListeners();
}

// Theme management
function setupThemeToggle() {
    themeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const theme = btn.dataset.theme;
            setTheme(theme);

            themeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    themeButtons.forEach(btn => {
        if (btn.dataset.theme === savedTheme) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// Load movies from db.json
async function loadMovies() {
    try {
        showLoading();
        const response = await fetch('./db.json');

        if (!response.ok) {
            throw new Error('Failed to load movies database');
        }

        allMovies = await response.json();
        showEmptyState();
    } catch (error) {
        showError('Error loading movies: ' + error.message);
    }
}

// Event listeners
function setupEventListeners() {
    getMovieBtn.addEventListener('click', getNewMovie);
}

// Display states
function showLoading() {
    movieContainer.innerHTML = '<div class="loading">Loading movies...</div>';
}

function showError(message) {
    movieContainer.innerHTML = `<div class="error">${message}</div>`;
}

function showEmptyState() {
    movieContainer.innerHTML = '<div class="empty-state">Click "Get New Movie" to start guessing!</div>';
}

// Filter movies by year range
function filterMoviesByYear() {
    const minYear = parseInt(minYearInput.value);
    const maxYear = parseInt(maxYearInput.value);

    if (isNaN(minYear) || isNaN(maxYear)) {
        return [];
    }

    if (minYear > maxYear) {
        showError('Minimum year cannot be greater than maximum year');
        return [];
    }

    return allMovies.filter(movie => {
        const movieYear = parseInt(movie.year);
        return movieYear >= minYear && movieYear <= maxYear;
    });
}

// Get random movie
function getNewMovie() {
    const filteredMovies = filterMoviesByYear();

    if (filteredMovies.length === 0) {
        showError('No movies found in the selected year range');
        return;
    }

    const randomIndex = Math.floor(Math.random() * filteredMovies.length);
    currentMovie = filteredMovies[randomIndex];
    isRevealed = false;

    displayMovie();
}

// Display movie
function displayMovie() {
    if (!currentMovie) {
        showEmptyState();
        return;
    }

    const movieCard = document.createElement('div');
    movieCard.className = 'movie-card';

    const movieContent = document.createElement('div');
    movieContent.className = 'movie-content';

    // Obfuscated plot section
    const obfuscatedSection = document.createElement('div');
    obfuscatedSection.className = 'plot-section';

    const obfuscatedLabel = document.createElement('div');
    obfuscatedLabel.className = 'plot-label';
    obfuscatedLabel.textContent = 'Obfuscated Plot';

    const obfuscatedText = document.createElement('div');
    obfuscatedText.className = 'plot-text';
    obfuscatedText.textContent = currentMovie.obfuscated_plot;

    obfuscatedSection.appendChild(obfuscatedLabel);
    obfuscatedSection.appendChild(obfuscatedText);
    movieContent.appendChild(obfuscatedSection);

    // Reveal section (initially hidden)
    const revealSection = document.createElement('div');
    revealSection.className = 'reveal-section hidden';
    revealSection.id = 'revealSection';

    const movieTitle = document.createElement('div');
    movieTitle.className = 'movie-title';
    movieTitle.textContent = currentMovie.name;

    const movieYear = document.createElement('div');
    movieYear.className = 'movie-year';
    movieYear.textContent = `Year: ${currentMovie.year}`;

    const plotSection = document.createElement('div');
    plotSection.className = 'plot-section';

    const plotLabel = document.createElement('div');
    plotLabel.className = 'plot-label';
    plotLabel.textContent = 'Full Plot';

    const plotText = document.createElement('div');
    plotText.className = 'plot-text';
    plotText.textContent = currentMovie.plot;

    plotSection.appendChild(plotLabel);
    plotSection.appendChild(plotText);

    revealSection.appendChild(movieTitle);
    revealSection.appendChild(movieYear);
    revealSection.appendChild(plotSection);

    movieContent.appendChild(revealSection);
    movieCard.appendChild(movieContent);

    // Button group
    const buttonGroup = document.createElement('div');
    buttonGroup.className = 'button-group';

    const revealBtn = document.createElement('button');
    revealBtn.className = 'button';
    revealBtn.textContent = 'Reveal Answer';
    revealBtn.id = 'revealBtn';
    revealBtn.addEventListener('click', revealAnswer);

    const tryAnotherBtn = document.createElement('button');
    tryAnotherBtn.className = 'button hidden';
    tryAnotherBtn.textContent = 'Try Another';
    tryAnotherBtn.id = 'tryAnotherBtn';
    tryAnotherBtn.addEventListener('click', getNewMovie);

    buttonGroup.appendChild(revealBtn);
    buttonGroup.appendChild(tryAnotherBtn);
    movieCard.appendChild(buttonGroup);

    movieContainer.innerHTML = '';
    movieContainer.appendChild(movieCard);
}

// Reveal answer
function revealAnswer() {
    if (isRevealed) return;

    isRevealed = true;

    const revealSection = document.getElementById('revealSection');
    const revealBtn = document.getElementById('revealBtn');
    const tryAnotherBtn = document.getElementById('tryAnotherBtn');

    if (revealSection) {
        revealSection.classList.remove('hidden');
    }

    if (revealBtn) {
        revealBtn.classList.add('hidden');
    }

    if (tryAnotherBtn) {
        tryAnotherBtn.classList.remove('hidden');
    }
}

// Start the app
init();
