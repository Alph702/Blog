/**
 * Confetti Cannon module.
 * Adapted from provided script to use modern JS and GSAP v3.
 */

// utilities
function getLength(x0, y0, x1, y1) {
    const x = x1 - x0;
    const y = y1 - y0;
    return Math.sqrt(x * x + y * y);
}

function getDegAngle(x0, y0, x1, y1) {
    const y = y1 - y0;
    const x = x1 - x0;
    return Math.atan2(y, x) * (180 / Math.PI);
}

// some constants
const DECAY = 4;        // confetti decay in seconds
const SPREAD = 60;      // degrees to spread from the angle of the cannon
const GRAVITY = 1200;

export class ConfettiCannon {
    constructor(canvasId = 'confetti-canvas') {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;

        this.dpr = window.devicePixelRatio || 1;
        this.ctx = this.canvas.getContext('2d');

        this.confettiSpriteIds = [];
        this.confettiSprites = {};

        this.drawVector = false;
        this.vector = [{ x: 0, y: 0 }, { x: 0, y: 0 }];
        this.pointer = { x: 0, y: 0 };

        this.render = this.render.bind(this);
        this.handleMousedown = this.handleMousedown.bind(this);
        this.handleMouseup = this.handleMouseup.bind(this);
        this.handleMousemove = this.handleMousemove.bind(this);
        this.handleTouchstart = this.handleTouchstart.bind(this);
        this.handleTouchmove = this.handleTouchmove.bind(this);
        this.setCanvasSize = this.setCanvasSize.bind(this);

        this.setupListeners();
        this.setCanvasSize();

        // Initial demo fire
        this.timer = setTimeout(() => {
            const rect = this.canvas.getBoundingClientRect();
            const x = (rect.width / 2) * this.dpr;
            const y = (rect.height * 0.8) * this.dpr;
            this.vector[0] = { x, y: y + 50 * this.dpr };
            this.vector[1] = { x, y };
            this.handleMouseup();
        }, 1000);
    }

    setupListeners() {
        gsap.ticker.add(this.render);

        this.canvas.addEventListener('mousedown', this.handleMousedown);
        window.addEventListener('mouseup', this.handleMouseup);
        window.addEventListener('mousemove', this.handleMousemove);

        this.canvas.addEventListener('touchstart', this.handleTouchstart, { passive: false });
        window.addEventListener('touchend', this.handleMouseup);
        window.addEventListener('touchmove', this.handleTouchmove, { passive: false });
        window.addEventListener('resize', this.setCanvasSize);
    }

    setCanvasSize() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width * this.dpr;
        this.canvas.height = rect.height * this.dpr;
        this.ctx.scale(this.dpr, this.dpr);
    }

    getCanvasMousePos(event) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: (event.clientX - rect.left) * this.dpr,
            y: (event.clientY - rect.top) * this.dpr
        };
    }

    handleMousedown(event) {
        clearTimeout(this.timer);
        const pos = this.getCanvasMousePos(event);
        this.vector[0] = pos;
        this.drawVector = true;
    }

    handleTouchstart(event) {
        clearTimeout(this.timer);
        const touch = event.touches[0];
        const pos = this.getCanvasMousePos(touch);
        this.vector[0] = pos;
        this.drawVector = true;
    }

    handleMouseup(event) {
        if (!this.drawVector && !this.timer) return;
        this.drawVector = false;

        const x0 = this.vector[0].x;
        const y0 = this.vector[0].y;
        const x1 = this.vector[1].x;
        const y1 = this.vector[1].y;

        const length = getLength(x0, y0, x1, y1);
        const angle = getDegAngle(x0, y0, x1, y1) + 180;

        const particles = Math.min(length / 5 + 10, 100);
        const velocity = length * 5;
        this.addConfettiParticles(particles, angle, velocity, x0 / this.dpr, y0 / this.dpr);
    }

    handleMousemove(event) {
        const pos = this.getCanvasMousePos(event);
        this.vector[1] = pos;
        this.pointer = pos;
    }

    handleTouchmove(event) {
        const touch = event.changedTouches[0];
        const pos = this.getCanvasMousePos(touch);
        this.vector[1] = pos;
        this.pointer = pos;
    }

    drawVectorLine() {
        this.ctx.strokeStyle = '#00ff00';
        this.ctx.lineWidth = 2;

        this.ctx.beginPath();
        this.ctx.moveTo(this.vector[0].x / this.dpr, this.vector[0].y / this.dpr);
        this.ctx.lineTo(this.vector[1].x / this.dpr, this.vector[1].y / this.dpr);
        this.ctx.stroke();
    }

    addConfettiParticles(amount, angle, velocity, x, y) {
        let i = 0;
        while (i < amount) {
            const r = _.random(4, 6);
            const d = _.random(15, 25);

            // Site themed colors (neon greens and variations)
            const colors = ['#00ff00', '#00cc00', '#33ff33', '#ffffff', '#ccffcc'];
            const color = colors[_.random(0, colors.length - 1)];

            const tiltAngleIncremental = _.random(0.07, 0.05);
            const id = _.uniqueId('confetti_');

            this.confettiSprites[id] = {
                angle,
                velocity,
                x,
                y,
                r,
                d,
                color,
                tilt: _.random(10, -10),
                tiltAngleIncremental,
                tiltAngle: 0,
            };

            this.confettiSpriteIds.push(id);
            this.tweenConfettiParticle(id);
            i++;
        }
    }

    tweenConfettiParticle(id) {
        const sprite = this.confettiSprites[id];
        const minAngle = sprite.angle - SPREAD / 2;
        const maxAngle = sprite.angle + SPREAD / 2;

        const minVelocity = sprite.velocity / 4;
        const maxVelocity = sprite.velocity;

        const velocity = _.random(minVelocity, maxVelocity);
        const angle = _.random(minAngle, maxAngle) * (Math.PI / 180);

        // Manual physics since Physics2D is a paid plugin
        const vx = Math.cos(angle) * velocity;
        const vy = Math.sin(angle) * velocity;

        const physics = {
            vx,
            vy,
            gravity: GRAVITY,
            friction: _.random(0.95, 0.98) // Air resistance
        };

        gsap.to(sprite, {
            duration: DECAY,
            ease: "power4.out",
            onUpdate: () => {
                if (!this.confettiSprites[id]) return;
                physics.vy += physics.gravity * 0.016; // Simple gravity integration
                physics.vx *= physics.friction;
                physics.vy *= physics.friction;

                sprite.x += physics.vx * 0.016;
                sprite.y += physics.vy * 0.016;

                this.updateConfettiAnimation(id);
            },
            onComplete: () => {
                _.pull(this.confettiSpriteIds, id);
                delete this.confettiSprites[id];
            }
        });
    }

    updateConfettiAnimation(id) {
        const sprite = this.confettiSprites[id];
        sprite.tiltAngle += sprite.tiltAngleIncremental;
        sprite.tilt = (Math.sin(sprite.tiltAngle)) * sprite.r;
    }

    drawConfetti() {
        this.confettiSpriteIds.forEach(id => {
            const sprite = this.confettiSprites[id];
            if (!sprite) return;

            this.ctx.beginPath();
            this.ctx.lineWidth = sprite.r;
            this.ctx.strokeStyle = sprite.color;
            this.ctx.moveTo(sprite.x + sprite.tilt + sprite.r, sprite.y);
            this.ctx.lineTo(sprite.x + sprite.tilt, sprite.y + sprite.tilt + sprite.r);
            this.ctx.stroke();
        });
    }

    drawPointer() {
        if (!this.drawVector) return;
        const x = this.pointer.x / this.dpr;
        const y = this.pointer.y / this.dpr;

        this.ctx.beginPath();
        this.ctx.arc(x, y, 15, 0, 2 * Math.PI, false);
        this.ctx.lineWidth = 2;
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.stroke();
    }

    drawPower() {
        if (!this.drawVector) return;
        const x0 = this.vector[0].x / this.dpr;
        const y0 = this.vector[0].y / this.dpr;
        const x1 = this.vector[1].x / this.dpr;
        const y1 = this.vector[1].y / this.dpr;

        const length = getLength(x0, y0, x1, y1);
        const radius = Math.min(length / 2, 50);

        this.ctx.beginPath();
        this.ctx.arc(x0, y0, radius, 0, 2 * Math.PI, false);
        this.ctx.lineWidth = 2;
        this.ctx.strokeStyle = 'rgba(0, 255, 0, 0.5)';
        this.ctx.stroke();
    }

    render() {
        this.ctx.clearRect(0, 0, this.canvas.width / this.dpr, this.canvas.height / this.dpr);

        if (this.drawVector) {
            this.drawVectorLine();
            this.drawPower();
            this.drawPointer();
        }

        this.drawConfetti();
    }

    destroy() {
        gsap.ticker.remove(this.render);
        // Clean up listeners if needed
    }
}
