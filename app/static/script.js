function openTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
}

// Handle File Upload Previews
function setupUpload(areaId, inputId, previewId) {
    const area = document.getElementById(areaId);
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);

    area.onclick = () => input.click();

    input.onchange = () => {
        const file = input.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.src = e.target.result;
                preview.hidden = false;
                area.hidden = true;
            };
            reader.readAsDataURL(file);
        }
    };
}

setupUpload('hide-upload', 'hide-file', 'hide-preview');
setupUpload('reveal-upload', 'reveal-file', 'reveal-preview');

async function hideMessage() {
    const fileInput = document.getElementById('hide-file');
    const message = document.getElementById('hide-message').value;
    const password = document.getElementById('hide-password').value;
    const resultDiv = document.getElementById('hide-result');

    if (!fileInput.files[0] || !message) {
        alert("Please select an image and write a message!");
        return;
    }

    const formData = new FormData();
    formData.append('image', fileInput.files[0]);
    formData.append('message', message);
    formData.append('password', password);

    resultDiv.style.display = 'block';
    resultDiv.innerHTML = "🔮 Casting spell...";

    try {
        const response = await fetch('/hide', { method: 'POST', body: formData });
        const data = await response.json();

        if (data.success) {
            resultDiv.innerHTML = `
                <p>✨ Secret Hidden Successfully!</p>
                <a href="${data.image_url}" download class="action-btn" style="display:block; text-align:center; margin-top:10px; text-decoration:none; font-size:1rem;">Download Image 📥</a>
            `;
        } else {
            resultDiv.innerHTML = `❌ Error: ${data.error}`;
        }
    } catch (e) {
        resultDiv.innerHTML = `❌ Error: ${e.message}`;
    }
}

async function revealMessage() {
    const fileInput = document.getElementById('reveal-file');
    const password = document.getElementById('reveal-password').value;
    const resultDiv = document.getElementById('reveal-result');
    const lockoutDiv = document.getElementById('lockout-timer');

    if (!fileInput.files[0]) {
        alert("Please select an image!");
        return;
    }

    const formData = new FormData();
    formData.append('image', fileInput.files[0]);
    formData.append('password', password);

    resultDiv.style.display = 'block';
    resultDiv.innerHTML = "🔍 Decrypting...";
    lockoutDiv.hidden = true;

    try {
        const response = await fetch('/reveal', { method: 'POST', body: formData });
        const data = await response.json();

        if (response.status === 403 && data.error === 'LOCKED_OUT') {
            startLockout(data.remaining);
            resultDiv.innerHTML = "";
        } else if (response.status === 401 && data.error === 'PASSWORD_REQUIRED') {
            resultDiv.innerHTML = "🔒 Password required for this image!";
        } else if (response.status === 401 && data.error === 'WRONG_PASSWORD') {
            resultDiv.innerHTML = "❌ Wrong Password!";
        } else if (data.message) {
            resultDiv.innerHTML = `
                <h3 style="margin-bottom:5px;">Secret Revealed:</h3>
                <p style="font-size:1.2rem; color:#00E5FF;">${data.message}</p>
            `;
        } else {
            resultDiv.innerHTML = `❌ Error: ${data.error || "Unknown error"}`;
        }
    } catch (e) {
        resultDiv.innerHTML = `❌ Error: ${e.message}`;
    }
}

function startLockout(seconds) {
    const lockoutDiv = document.getElementById('lockout-timer');
    const timerSpan = document.getElementById('timer');
    lockoutDiv.hidden = false;

    let remaining = Math.ceil(seconds);
    timerSpan.innerText = remaining;

    const interval = setInterval(() => {
        remaining--;
        timerSpan.innerText = remaining;
        if (remaining <= 0) {
            clearInterval(interval);
            lockoutDiv.hidden = true;
        }
    }, 1000);
}

// --- Particle Animation ---
const canvas = document.getElementById('particles');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let particles = [];
const particleCount = 100;

class Particle {
    constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.vx = (Math.random() - 0.5) * 0.5;
        this.vy = (Math.random() - 0.5) * 0.5;
        this.size = Math.random() * 2 + 1;
        this.color = Math.random() > 0.5 ? '#00FF9D' : '#00E5FF';
    }

    update() {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
        if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
    }

    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
    }
}

for (let i = 0; i < particleCount; i++) {
    particles.push(new Particle());
}

function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach(p => {
        p.update();
        p.draw();

        // Draw connections
        particles.forEach(p2 => {
            const dx = p.x - p2.x;
            const dy = p.y - p2.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < 100) {
                ctx.beginPath();
                ctx.strokeStyle = `rgba(0, 255, 157, ${0.1 - distance / 1000})`;
                ctx.lineWidth = 0.5;
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }
        });
    });

    requestAnimationFrame(animate);
}

window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

animate();
