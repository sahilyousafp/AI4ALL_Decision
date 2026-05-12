"""
HTML Generator for Ideology Agent UI with Compass Gauge
Embeds the questionnaire + compass visualization in the Folium map
"""

import json


def generate_ideology_ui_html() -> str:
    """Generate the complete HTML/CSS/JS for the ideology agent interface"""
    
    html = '''
<!-- Ideology Agent UI -->
<div id="ideology-panel" style="
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9998;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    padding: 0;
    width: 90%;
    max-width: 600px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: white;
    overflow: hidden;
">
    <!-- Tab Navigation -->
    <div style="display: flex; background: rgba(0,0,0,0.2); border-bottom: 1px solid rgba(255,255,255,0.2);">
        <button id="tab-questionnaire" class="ideology-tab" onclick="switchTab('questionnaire')" style="
            flex: 1;
            padding: 12px;
            border: none;
            background: transparent;
            color: white;
            cursor: pointer;
            font-weight: 500;
            border-bottom: 3px solid white;
        ">🎯 Ideology Quiz</button>
        <button id="tab-results" class="ideology-tab" onclick="switchTab('results')" style="
            flex: 1;
            padding: 12px;
            border: none;
            background: transparent;
            color: rgba(255,255,255,0.6);
            cursor: pointer;
            font-weight: 500;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
        ">📊 Your Result</button>
        <button id="tab-close" onclick="toggleIdeologyPanel()" style="
            padding: 12px 16px;
            border: none;
            background: transparent;
            color: white;
            cursor: pointer;
            font-size: 18px;
            margin-left: auto;
        ">✕</button>
    </div>

    <!-- Questionnaire Tab -->
    <div id="questionnaire-content" style="padding: 20px; max-height: 400px; overflow-y: auto;">
        <div id="question-container" style="animation: fadeIn 0.3s ease;">
            <!-- Questions will be injected here -->
        </div>
    </div>

    <!-- Results Tab -->
    <div id="results-content" style="padding: 20px; display: none; text-align: center;">
        <div style="margin-bottom: 20px;">
            <h3 style="margin: 0 0 10px 0; font-size: 18px;">Your Ideology Score</h3>
            <p style="margin: 0; opacity: 0.9; font-size: 14px;">Environmental Wellbeing vs Personal Comfort</p>
        </div>
        
        <!-- Compass Gauge -->
        <canvas id="compass-gauge" width="300" height="300" style="max-width: 100%; margin: 0 auto; display: block;"></canvas>
        
        <div id="score-interpretation" style="
            margin-top: 16px;
            padding: 12px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            font-size: 13px;
            line-height: 1.5;
        "></div>
        
        <button onclick="resetQuiz()" style="
            margin-top: 16px;
            padding: 10px 20px;
            background: white;
            color: #667eea;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s ease;
        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            Retake Quiz
        </button>
    </div>

    <!-- Minimized State -->
    <div id="ideology-minimized" style="
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9998;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 50px;
        padding: 12px 24px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        display: none;
        color: white;
        font-weight: 500;
        transition: all 0.3s ease;
    " onclick="toggleIdeologyPanel()">
        🎯 Ideology Assessment
    </div>
</div>

<style>
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .ideology-tab:hover {
        background: rgba(255,255,255,0.1);
    }
    
    .ideology-question-item {
        margin-bottom: 16px;
        animation: fadeIn 0.3s ease;
    }
    
    .ideology-option {
        width: 100%;
        padding: 12px 14px;
        margin: 8px 0;
        background: rgba(255,255,255,0.15);
        border: 2px solid transparent;
        border-radius: 8px;
        color: white;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.2s ease;
        text-align: left;
    }
    
    .ideology-option:hover {
        background: rgba(255,255,255,0.25);
        transform: translateX(4px);
    }
    
    .ideology-option.selected {
        background: rgba(255,255,255,0.35);
        border-color: white;
    }
    
    .ideology-progress {
        height: 6px;
        background: rgba(255,255,255,0.2);
        border-radius: 3px;
        margin-bottom: 16px;
        overflow: hidden;
    }
    
    .ideology-progress-bar {
        height: 100%;
        background: white;
        border-radius: 3px;
        transition: width 0.3s ease;
    }
</style>

<script>
    let ideologyResponses = [];
    let currentQuestion = 0;
    
    const ideologyQuestions = [
        {
            id: 1,
            text: "When considering land-use development (like airport expansion), what matters most?",
            options: [
                "Economic growth and job creation",
                "Environmental preservation and biodiversity"
            ]
        },
        {
            id: 2,
            text: "How do you view climate change impact on your lifestyle?",
            options: [
                "I'll adapt gradually when necessary",
                "I make significant daily changes to reduce emissions"
            ]
        },
        {
            id: 3,
            text: "Urban expansion vs green spaces—your preference?",
            options: [
                "More development = more opportunities",
                "Protect existing ecosystems and nature"
            ]
        },
        {
            id: 4,
            text: "Your stance on transportation infrastructure?",
            options: [
                "Build more highways and airports",
                "Invest in public transit and reduce emissions"
            ]
        },
        {
            id: 5,
            text: "How do you balance convenience with environmental cost?",
            options: [
                "Convenience and comfort are priorities",
                "Environmental impact is non-negotiable"
            ]
        }
    ];
    
    function switchTab(tab) {
        document.getElementById('questionnaire-content').style.display = tab === 'questionnaire' ? 'block' : 'none';
        document.getElementById('results-content').style.display = tab === 'results' ? 'block' : 'none';
        
        const tabs = document.querySelectorAll('.ideology-tab');
        tabs.forEach(t => {
            const isActive = (tab === 'questionnaire' && t.id === 'tab-questionnaire') ||
                            (tab === 'results' && t.id === 'tab-results');
            t.style.color = isActive ? 'white' : 'rgba(255,255,255,0.6)';
            t.style.borderBottomColor = isActive ? 'white' : 'transparent';
        });
    }
    
    function toggleIdeologyPanel() {
        const panel = document.getElementById('ideology-panel');
        const minimized = document.getElementById('ideology-minimized');
        
        if (panel.style.display === 'none') {
            panel.style.display = 'block';
            minimized.style.display = 'none';
        } else {
            panel.style.display = 'none';
            minimized.style.display = 'block';
        }
    }
    
    function renderQuestion(index) {
        if (index >= ideologyQuestions.length) {
            calculateAndShowResults();
            return;
        }
        
        const q = ideologyQuestions[index];
        const progress = ((index) / ideologyQuestions.length) * 100;
        
        let html = `
            <div class="ideology-progress">
                <div class="ideology-progress-bar" style="width: ${progress}%"></div>
            </div>
            <div class="ideology-question-item">
                <div style="font-size: 12px; opacity: 0.8; margin-bottom: 8px;">Question ${index + 1}/${ideologyQuestions.length}</div>
                <h4 style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.4;">${q.text}</h4>
                ${q.options.map((opt, idx) => `
                    <button class="ideology-option" onclick="selectOption(${index}, ${idx})">
                        <span style="display: inline-block; margin-right: 8px; font-weight: 600;">
                            ${idx === 0 ? '◯' : '◉'}
                        </span>
                        ${opt}
                    </button>
                `).join('')}
            </div>
        `;
        
        document.getElementById('question-container').innerHTML = html;
    }
    
    function selectOption(questionIdx, optionIdx) {
        ideologyResponses[questionIdx] = optionIdx;
        
        const buttons = document.querySelectorAll('.ideology-option');
        buttons.forEach((btn, idx) => {
            if (Math.floor(idx / 2) === questionIdx) {
                if (idx % 2 === optionIdx) {
                    btn.classList.add('selected');
                } else {
                    btn.classList.remove('selected');
                }
            }
        });
        
        // Auto-advance after 300ms
        setTimeout(() => {
            currentQuestion++;
            renderQuestion(currentQuestion);
        }, 300);
    }
    
    function calculateAndShowResults() {
        // Calculate score: 0-100, where each response of 1 (second option) = +20
        const score = ideologyResponses.reduce((sum, resp) => sum + (resp === 1 ? 20 : 0), 0);
        
        switchTab('results');
        drawCompassGauge(score);
        generateInterpretation(score);
    }
    
    function drawCompassGauge(score) {
        const canvas = document.getElementById('compass-gauge');
        const ctx = canvas.getContext('2d');
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = 80;
        
        // Clear
        ctx.fillStyle = 'rgba(255,255,255,0.1)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw outer circle
        ctx.strokeStyle = 'rgba(255,255,255,0.4)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.stroke();
        
        // Draw inner circle
        ctx.strokeStyle = 'rgba(255,255,255,0.2)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius * 0.7, 0, Math.PI * 2);
        ctx.stroke();
        
        // Draw labels
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        ctx.font = 'bold 11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('COMFORT', centerX, centerY - radius - 10);
        ctx.fillText('ENVIRONMENT', centerX, centerY + radius + 20);
        
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText('COMFORT', centerX - radius - 10, centerY + 4);
        ctx.textAlign = 'left';
        ctx.fillText('ENVIRONMENT', centerX + radius + 10, centerY + 4);
        
        // Draw needle pointing to score
        const angle = (score / 100) * Math.PI - Math.PI / 2;
        const needleX = centerX + Math.cos(angle) * (radius * 0.8);
        const needleY = centerY + Math.sin(angle) * (radius * 0.8);
        
        // Needle line
        ctx.strokeStyle = 'rgba(255,255,255,0.9)';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(needleX, needleY);
        ctx.stroke();
        
        // Center circle
        ctx.fillStyle = 'white';
        ctx.beginPath();
        ctx.arc(centerX, centerY, 6, 0, Math.PI * 2);
        ctx.fill();
        
        // Score display
        ctx.fillStyle = 'white';
        ctx.font = 'bold 24px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(score, centerX, centerY + 35);
        ctx.font = '11px sans-serif';
        ctx.fillStyle = 'rgba(255,255,255,0.8)';
        ctx.fillText('/ 100', centerX, centerY + 50);
    }
    
    function generateInterpretation(score) {
        let interpretation = '';
        
        if (score >= 80) {
            interpretation = "You strongly prioritize environmental protection. You likely oppose airport expansion due to ecosystem impact and prefer sustainable alternatives.";
        } else if (score >= 60) {
            interpretation = "You lean toward environmental considerations. You recognize growth benefits but want strong protections for natural areas and emissions reduction.";
        } else if (score >= 40) {
            interpretation = "You balance both perspectives. You see merit in development opportunities and environmental protection, supporting growth with conditions.";
        } else if (score >= 20) {
            interpretation = "You prioritize economic growth and convenience. You support airport expansion for jobs and connectivity, with reasonable environmental safeguards.";
        } else {
            interpretation = "You strongly favor development and personal comfort. You see airport expansion as essential for growth and see environmental concerns as secondary.";
        }
        
        document.getElementById('score-interpretation').innerText = interpretation;
    }
    
    function resetQuiz() {
        ideologyResponses = [];
        currentQuestion = 0;
        switchTab('questionnaire');
        renderQuestion(0);
    }
    
    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        renderQuestion(0);
    });
</script>
'''
    return html


if __name__ == "__main__":
    print(generate_ideology_ui_html())
