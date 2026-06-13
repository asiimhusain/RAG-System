export class ThemeManager {
    static init() {
        const isDark = localStorage.getItem('theme') === 'dark' || 
            (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
        
        if (isDark) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }

    static toggle() {
        const html = document.documentElement;
        html.classList.toggle('dark');
        localStorage.setItem('theme', html.classList.contains('dark') ? 'dark' : 'light');
    }
}

export class Toast {
    static show(message, type = 'success') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        const color = type === 'success' ? 'bg-green-500' : 'bg-red-500';
        toast.className = `transform transition-all duration-300 translate-y-full opacity-0 ${color} text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-3`;
        
        toast.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" class="hover:text-gray-200">&times;</button>
        `;

        container.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.classList.remove('translate-y-full', 'opacity-0');
        });

        // Auto remove
        setTimeout(() => {
            toast.classList.add('opacity-0', 'translate-y-full');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

export class Modal {
    static init() {
        document.querySelectorAll('[data-modal-target]').forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                Modal.show(trigger.getAttribute('data-modal-target'));
            });
        });

        document.querySelectorAll('[data-modal-close], .modal-overlay').forEach(closer => {
            closer.addEventListener('click', (e) => {
                if(e.target !== closer && !closer.hasAttribute('data-modal-close')) return;
                e.preventDefault();
                const overlay = closer.closest('.modal-overlay');
                if (overlay) Modal.hide(overlay.id);
            });
        });
    }

    static show(id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            // small trick to force reflow for opacity transition if needed
            requestAnimationFrame(() => {
                modal.classList.remove('opacity-0');
            });
        }
    }

    static hide(id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.add('opacity-0');
            setTimeout(() => {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
            }, 300);
        }
    }
}
