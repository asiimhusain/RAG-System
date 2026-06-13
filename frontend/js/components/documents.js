import ApiService from '../services/api.js';
import { Toast, ThemeManager } from './utils.js';

class DocumentsUI {
    constructor() {
        this.dropZone = document.getElementById('drop-zone');
        this.fileInput = document.getElementById('file-input');
        this.statusBadge = document.getElementById('db-status');

        this.init();
        this.fetchStatus();
    }

    init() {
        lucide.createIcons();
        ThemeManager.init();

        const themeBtn = document.getElementById('theme-toggle');
        if (themeBtn) themeBtn.addEventListener('click', () => ThemeManager.toggle());

        // Drag & Drop
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('border-primary', 'bg-blue-50', 'dark:bg-blue-900/10');
        });

        this.dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('border-primary', 'bg-blue-50', 'dark:bg-blue-900/10');
        });

        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('border-primary', 'bg-blue-50', 'dark:bg-blue-900/10');
            if (e.dataTransfer.files.length) {
                this.handleUpload(e.dataTransfer.files[0]);
            }
        });

        this.dropZone.addEventListener('click', () => this.fileInput.click());

        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                this.handleUpload(e.target.files[0]);
            }
        });
    }

    async fetchStatus() {
        try {
            const data = await ApiService.getStatus();
            document.getElementById('stat-docs').innerText = data.document_count;
            document.getElementById('stat-status').innerText = data.status.toUpperCase();
            this.statusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span> ${data.document_count} Chunks Indexed`;
        } catch (e) {
            console.error(e);
            this.statusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-red-500 mr-2"></span> Offline`;
            document.getElementById('stat-status').innerText = 'ERROR';
        }
    }

    async handleUpload(file) {
        // UI processing update
        const originalContent = this.dropZone.innerHTML;
        this.dropZone.innerHTML = `
            <div class="flex flex-col items-center">
                <i data-lucide="loader" class="w-12 h-12 text-primary animate-spin mb-4"></i>
                <h3 class="text-lg font-bold">Uploading & Indexing...</h3>
                <p class="text-sm text-[var(--text-muted)] mt-1">Chunking and embedding vectors in background</p>
            </div>
        `;
        lucide.createIcons();

        try {
            await ApiService.uploadDocument(file);
            Toast.show(`Successfully queued ${file.name} for indexing!`);
            setTimeout(() => this.fetchStatus(), 2000); // refresh after slight delay
        } catch (error) {
            Toast.show(`Upload failed: ${error.message}`, 'error');
        } finally {
            this.dropZone.innerHTML = originalContent;
            lucide.createIcons();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new DocumentsUI();
});
