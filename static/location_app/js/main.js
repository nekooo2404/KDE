const SAMPLE_TWEET = 'Dạo bộ qua Marina Bay rồi ghé Merlion trước khi tiếp tục xuống Orchard Road.';
const WORLD_ATLAS_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json';

const elements = {};
let worldMapPromise;
let worldCitiesPromise;
let citySearchTimer;
let keywordExtractTimer;
let lastExtractedKeywords = [];

document.addEventListener('DOMContentLoaded', () => {
    cacheDomElements();
    bindEvents();
    resetResults();
    renderMap(null, []);
});

function cacheDomElements() {
    elements.predictBtn = document.getElementById('predictBtn');
    elements.resolveUrlBtn = document.getElementById('resolveUrlBtn');
    elements.sampleBtn = document.getElementById('sampleBtn');
    elements.tweetText = document.getElementById('tweetText');
    elements.tweetUrl = document.getElementById('tweetUrl');
    elements.cityBias = document.getElementById('cityBias');
    elements.cityBiasSuggestions = document.getElementById('cityBiasSuggestions');
    elements.loading = document.getElementById('loading');
    elements.loadingLabel = document.getElementById('loadingLabel');
    elements.statusMessage = document.getElementById('statusMessage');
    elements.predictedCity = document.getElementById('predictedCity');
    elements.confidence = document.getElementById('confidence');
    elements.biasApplied = document.getElementById('biasApplied');
    elements.termsCount = document.getElementById('termsCount');
    elements.matchedTerms = document.getElementById('matchedTerms');
    elements.tweetPreview = document.getElementById('tweetPreview');
    elements.scoreList = document.getElementById('scoreList');
    elements.mapMeta = document.getElementById('mapMeta');
    elements.keywordChipList = document.getElementById('keywordChipList');
    elements.keywordCount = document.getElementById('keywordCount');
}

function bindEvents() {
    elements.predictBtn.addEventListener('click', handlePrediction);
    elements.resolveUrlBtn.addEventListener('click', handleResolveTweetUrl);
    elements.sampleBtn.addEventListener('click', applySampleTweet);
    elements.cityBias.addEventListener('input', queueCitySearch);

    // Auto-extract keywords khi người dùng gõ (debounce 450ms)
    elements.tweetText.addEventListener('input', () => {
        window.clearTimeout(keywordExtractTimer);
        keywordExtractTimer = window.setTimeout(() => {
            queueKeywordExtract(elements.tweetText.value);
        }, 450);
    });

    elements.tweetText.addEventListener('keydown', (event) => {
        if (event.ctrlKey && event.key === 'Enter') {
            handlePrediction();
        }
    });

    elements.tweetUrl.addEventListener('paste', () => {
        window.setTimeout(() => {
            if (looksLikeTweetUrl(elements.tweetUrl.value)) {
                handleResolveTweetUrl();
            }
        }, 0);
    });

    elements.tweetText.addEventListener('paste', (event) => {
        const pastedText = event.clipboardData?.getData('text') || '';
        if (!looksLikeTweetUrl(pastedText)) {
            return;
        }

        event.preventDefault();
        elements.tweetUrl.value = pastedText.trim();
        handleResolveTweetUrl();
    });

    // Extract ngay khi load trang (nếu textarea đã có giá trị)
    if (elements.tweetText.value.trim()) {
        queueKeywordExtract(elements.tweetText.value);
    }
}

function queueCitySearch() {
    const query = elements.cityBias.value.trim();
    if (query.length < 2) {
        elements.cityBiasSuggestions.innerHTML = '';
        return;
    }

    window.clearTimeout(citySearchTimer);
    citySearchTimer = window.setTimeout(() => {
        fetchCitySuggestions(query);
    }, 180);
}

// ---------------------------------------------------------------------------
// Keyword extraction
// ---------------------------------------------------------------------------

function queueKeywordExtract(text) {
    if (!text.trim()) {
        renderKeywordChips([]);
        return;
    }
    if (elements.keywordChipList) {
        elements.keywordChipList.innerHTML = '<span class="chip-loading">Đang lọc keyword…</span>';
    }
    fetchKeywords(text);
}

async function fetchKeywords(text) {
    try {
        const response = await fetch('/api/extract-keywords/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ text }),
        });
        const data = await response.json();
        if (data.success) {
            lastExtractedKeywords = data.keywords || [];
            renderKeywordChips(lastExtractedKeywords);
        }
    } catch (_err) {
        // Lỗi không ảnh hưởng UI chính
    }
}

function renderKeywordChips(keywords) {
    if (!elements.keywordChipList) return;

    if (elements.keywordCount) {
        elements.keywordCount.textContent = keywords.length;
    }

    if (!keywords.length) {
        elements.keywordChipList.innerHTML = '<span class="chip-empty">Không tìm thấy keyword địa lý nào.</span>';
        return;
    }

    elements.keywordChipList.innerHTML = keywords
        .map((kw) => `<span class="keyword-chip">${escapeHtml(kw)}</span>`)
        .join('');
}

// ---------------------------------------------------------------------------
// City search autocomplete
// ---------------------------------------------------------------------------

async function fetchCitySuggestions(query) {
    try {
        const response = await fetch(`/api/city-search/?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        if (!response.ok || !data.success) {
            return;
        }

        elements.cityBiasSuggestions.innerHTML = (data.suggestions || [])
            .map((city) => `<option value="${escapeHtml(city)}"></option>`)
            .join('');
    } catch (error) {
        elements.cityBiasSuggestions.innerHTML = '';
    }
}

// ---------------------------------------------------------------------------
// Prediction
// ---------------------------------------------------------------------------

async function handlePrediction() {
    const tweet = elements.tweetText.value.trim();
    const cityBias = elements.cityBias.value.trim();

    if (!tweet) {
        setStatus('Cần có nội dung bài đăng trước khi dự đoán.', 'error');
        return;
    }

    setLoading(true, 'Đang phân tích và dự đoán vị trí…');

    try {
        const data = await postJson('/api/predict/', { tweet, cityBias, useAiFallback: true });
        displayResults(data);
        const src = data.prediction_source === 'embedding' ? ' (Embedding)' : ' (KDE)';
        setStatus(`Đã dự đoán xong. Thành phố khả nghi nhất: ${data.predicted_city}${src}.`, 'success');
    } catch (error) {
        resetResults();
        setStatus(error.message, 'error');
    } finally {
        setLoading(false);
    }
}

// ---------------------------------------------------------------------------
// Resolve tweet URL
// ---------------------------------------------------------------------------

async function handleResolveTweetUrl() {
    const tweetUrl = elements.tweetUrl.value.trim();

    if (!tweetUrl) {
        setStatus('Hãy dán liên kết bài đăng để hệ thống đọc nội dung.', 'error');
        return;
    }

    setLoading(true, 'Đang đọc nội dung bài đăng từ liên kết...');

    try {
        const data = await postJson('/api/resolve-tweet/', { tweetUrl });
        elements.tweetText.value = data.tweet_text;
        queueKeywordExtract(data.tweet_text);
        setStatus(
            data.author_name
                ? `Đã nạp bài đăng từ ${data.author_name}${data.author_handle ? ` (${data.author_handle})` : ''}.`
                : 'Đã nạp nội dung bài đăng từ liên kết.',
            'success',
        );
    } catch (error) {
        setStatus(error.message, 'error');
    } finally {
        setLoading(false);
    }
}

function applySampleTweet() {
    elements.tweetText.value = SAMPLE_TWEET;
    elements.tweetUrl.value = '';
    elements.cityBias.value = '';
    elements.cityBiasSuggestions.innerHTML = '';
    queueKeywordExtract(SAMPLE_TWEET);
    setStatus('Đã nạp ví dụ mẫu. Bấm "Dự đoán vị trí" để xem kết quả.', 'neutral');
}

// ---------------------------------------------------------------------------
// Display results
// ---------------------------------------------------------------------------

function displayResults(data) {
    elements.predictedCity.textContent = data.predicted_city;

    const sourceLabel = data.prediction_source === 'embedding' ? 'Embedding' : 'KDE';
    elements.confidence.textContent = `Độ tin cậy: ${formatPercent(data.confidence)} (${sourceLabel})`;

    elements.biasApplied.textContent = data.city_bias
        ? `Ưu tiên thành phố: ${data.city_bias}`
        : 'Ưu tiên thành phố: không áp dụng';
    elements.termsCount.textContent = `Số term khớp: ${data.terms_found} trên ${formatNumber(data.total_cities)} thành phố`;
    elements.tweetPreview.textContent = data.tweet_preview || 'Không có đoạn xem trước.';

    renderTerms(data.terms || []);
    renderScores(data.top_cities || [], data.predicted_city);
    renderMap(data.predicted_city, data.top_cities || []);
}

function resetResults() {
    elements.predictedCity.textContent = 'Chưa có dự đoán';
    elements.confidence.textContent = 'Độ tin cậy: 0%';
    elements.biasApplied.textContent = 'Ưu tiên thành phố: không áp dụng';
    elements.termsCount.textContent = 'Số term khớp: 0';
    elements.tweetPreview.textContent = 'Nội dung bài đăng sẽ được hiển thị ở đây sau khi phân tích.';
    renderTerms([]);
    renderScores([], '');
    renderMap(null, []);
}

function renderTerms(terms) {
    if (!terms.length) {
        elements.matchedTerms.innerHTML = '<span class="token empty-token">Chưa có từ khóa nào</span>';
        return;
    }

    elements.matchedTerms.innerHTML = terms
        .map((term) => `<span class="token">${escapeHtml(term)}</span>`)
        .join('');
}

function renderScores(topCities, predictedCity) {
    if (!topCities.length) {
        elements.scoreList.innerHTML = '<p class="empty-copy">Chưa có điểm số để hiển thị.</p>';
        return;
    }

    const maxScore = topCities[0]?.score || 0;

    elements.scoreList.innerHTML = topCities
        .map((entry) => {
            const width = maxScore > 0 ? (entry.score / maxScore) * 100 : 0;
            const winnerClass = entry.city === predictedCity ? 'is-winner' : '';

            return `
                <div class="score-row ${winnerClass}">
                    <div class="score-row-head">
                        <span>${escapeHtml(entry.city)}</span>
                        <strong>${entry.score.toFixed(4)}</strong>
                    </div>
                    <div class="score-bar-track">
                        <div class="score-bar-fill" style="width: ${width}%"></div>
                    </div>
                </div>
            `;
        })
        .join('');
}

// ---------------------------------------------------------------------------
// Map rendering
// ---------------------------------------------------------------------------

async function renderMap(predictedCity, topCities) {
    const mapNode = document.getElementById('map');
    mapNode.innerHTML = '';

    const width = mapNode.clientWidth || 520;
    const height = Math.max(320, Math.round(width * 0.62));
    const shell = d3.select(mapNode)
        .append('div')
        .attr('class', 'map-shell')
        .style('height', `${height}px`);

    const baseSvg = shell.append('svg')
        .attr('class', 'map-base-layer')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('role', 'presentation');

    const overlaySvg = shell.append('svg')
        .attr('class', 'map-overlay-layer')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('role', 'img')
        .attr('aria-label', 'Bản đồ thế giới thể hiện tất cả thành phố trong dataset cùng các ứng viên hàng đầu');

    const canvasNode = shell.append('canvas')
        .attr('class', 'map-city-canvas')
        .node();

    prepareCanvas(canvasNode, width, height);
    drawMapBackdrop(baseSvg, width, height);

    try {
        const [world, cityData] = await Promise.all([loadWorldMap(), loadWorldCities()]);
        const projection = d3.geoNaturalEarth1()
            .fitExtent([[16, 18], [width - 16, height - 18]], world);
        const path = d3.geoPath(projection);

        drawWorldGeometry(baseSvg, world, path);
        drawCityCloud(canvasNode, projection, cityData.cities || []);
        drawHighlights(overlaySvg, projection, topCities, predictedCity);

        if (elements.mapMeta) {
            elements.mapMeta.textContent = `Hiển thị ${formatNumber(cityData.total_cities || 0)} thành phố toàn cầu. Điểm sáng là các ứng viên mạnh nhất.`;
        }
    } catch (error) {
        mapNode.innerHTML = `
            <div class="map-fallback">
                <strong>Không tải được bản đồ thế giới.</strong>
                <p>Trình duyệt không lấy được dữ liệu bản đồ hoặc dataset thành phố lúc này. Bạn vẫn có thể xem bảng điểm ở bên dưới.</p>
            </div>
        `;
    }
}

function prepareCanvas(canvasNode, width, height) {
    const devicePixelRatio = window.devicePixelRatio || 1;
    canvasNode.width = Math.round(width * devicePixelRatio);
    canvasNode.height = Math.round(height * devicePixelRatio);
    canvasNode.style.width = `${width}px`;
    canvasNode.style.height = `${height}px`;

    const context = canvasNode.getContext('2d');
    context.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
    context.clearRect(0, 0, width, height);
}

function drawMapBackdrop(svg, width, height) {
    svg.append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', width)
        .attr('height', height)
        .attr('rx', 24)
        .attr('fill', '#dbeefa');
}

function drawWorldGeometry(svg, world, path) {
    svg.append('path')
        .datum({ type: 'Sphere' })
        .attr('class', 'map-sphere')
        .attr('d', path)
        .attr('fill', '#dbeefa');

    svg.append('path')
        .datum(d3.geoGraticule10())
        .attr('class', 'map-graticule')
        .attr('d', path)
        .attr('fill', 'none')
        .attr('stroke', 'rgba(38, 70, 83, 0.16)')
        .attr('stroke-width', 0.6);

    svg.append('g')
        .selectAll('.country')
        .data(world.features)
        .enter()
        .append('path')
        .attr('class', 'country')
        .attr('d', path)
        .attr('fill', '#f7efe1')
        .attr('stroke', 'rgba(38, 70, 83, 0.18)')
        .attr('stroke-width', 0.7);
}

function drawCityCloud(canvasNode, projection, cities) {
    const width = parseFloat(canvasNode.style.width);
    const height = parseFloat(canvasNode.style.height);
    const context = canvasNode.getContext('2d');

    context.clearRect(0, 0, width, height);

    for (const city of cities) {
        const [lat, lng, population] = city;
        const point = projection([lng, lat]);
        if (!point) {
            continue;
        }

        const radius = population > 5000000 ? 1.9 : population > 1000000 ? 1.5 : population > 100000 ? 1.05 : 0.65;
        const alpha = population > 5000000 ? 0.5 : population > 1000000 ? 0.34 : population > 100000 ? 0.22 : 0.12;

        context.beginPath();
        context.arc(point[0], point[1], radius, 0, Math.PI * 2);
        context.fillStyle = `rgba(38, 70, 83, ${alpha})`;
        context.fill();
    }
}

function drawHighlights(svg, projection, topCities, predictedCity) {
    if (!topCities.length) {
        return;
    }

    svg.append('defs')
        .append('filter')
        .attr('id', 'highlight-glow')
        .html(`
            <feGaussianBlur stdDeviation="5" result="coloredBlur"></feGaussianBlur>
            <feMerge>
                <feMergeNode in="coloredBlur"></feMergeNode>
                <feMergeNode in="SourceGraphic"></feMergeNode>
            </feMerge>
        `);

    const cityLayer = svg.append('g').attr('class', 'city-layer');
    const cityNodes = cityLayer.selectAll('.city-node')
        .data(topCities.slice(0, 12))
        .enter()
        .append('g')
        .attr('class', 'city-node')
        .attr('transform', (entry) => {
            const point = projection([entry.lng, entry.lat]);
            return `translate(${point[0]}, ${point[1]})`;
        });

    cityNodes.append('circle')
        .attr('class', 'city-glow')
        .attr('r', (entry, index) => (entry.city === predictedCity ? 22 : Math.max(8, 15 - index * 0.6)))
        .attr('fill', (entry) => (entry.city === predictedCity ? 'rgba(185, 56, 24, 0.22)' : 'rgba(38, 70, 83, 0.18)'))
        .attr('filter', 'url(#highlight-glow)');

    cityNodes.append('circle')
        .attr('r', (entry, index) => (entry.city === predictedCity ? 8.5 : Math.max(4.5, 7 - index * 0.18)))
        .attr('fill', (entry) => (entry.city === predictedCity ? '#b93818' : '#264653'))
        .attr('fill-opacity', 0.96)
        .attr('stroke', '#fffaf0')
        .attr('stroke-width', 2);

    cityNodes.append('text')
        .attr('y', -14)
        .attr('text-anchor', 'middle')
        .attr('class', 'map-label')
        .text((entry) => entry.city);

    cityNodes.append('text')
        .attr('y', 22)
        .attr('text-anchor', 'middle')
        .attr('class', 'map-score')
        .text((entry) => entry.score.toFixed(3));
}

// ---------------------------------------------------------------------------
// Data loaders
// ---------------------------------------------------------------------------

async function loadWorldMap() {
    if (!worldMapPromise) {
        worldMapPromise = d3.json(WORLD_ATLAS_URL).then((topology) =>
            topojson.feature(topology, topology.objects.countries),
        );
    }

    return worldMapPromise;
}

async function loadWorldCities() {
    if (!worldCitiesPromise) {
        worldCitiesPromise = fetch('/api/world-cities/')
            .then(async (response) => {
                if (!response.ok) {
                    throw new Error('Không tải được dataset thành phố toàn cầu.');
                }
                return response.json();
            });
    }

    return worldCitiesPromise;
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------

async function postJson(url, payload) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(payload),
    });

    let data = {};
    try {
        data = await response.json();
    } catch (error) {
        throw new Error('Máy chủ trả về dữ liệu không đọc được.');
    }

    if (!response.ok || !data.success) {
        throw new Error(data.error || 'Không thể xử lý yêu cầu.');
    }

    return data;
}

function setLoading(isLoading, label = 'Đang xử lý yêu cầu...') {
    elements.loading.hidden = !isLoading;
    elements.loadingLabel.textContent = label;
    elements.predictBtn.disabled = isLoading;
    elements.resolveUrlBtn.disabled = isLoading;
}

function setStatus(message, tone) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = `status-message is-${tone}`;
}

function looksLikeTweetUrl(value) {
    return /^https?:\/\/(www\.)?(twitter\.com|x\.com)\/[A-Za-z0-9_]+\/status\/\d+/i.test(
        (value || '').trim(),
    );
}

function formatPercent(value) {
    return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function formatNumber(value) {
    return new Intl.NumberFormat('vi-VN').format(Number(value || 0));
}

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let index = 0; index < cookies.length; index += 1) {
            const cookie = cookies[index].trim();
            if (cookie.substring(0, name.length + 1) === `${name}=`) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
