class PDFManager {
    constructor() {
        this.apiBase = '/api';
        this.selectedFile = null;
        this.currentDocumentId = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDocuments(); // Carregar documentos automaticamente
    }

    setupEventListeners() {
        // File upload
        const uploadArea = document.getElementById('upload-area');
        uploadArea.addEventListener('click', () => {
            document.getElementById('file-input').click();
        });

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            this.handleFileSelect(file);
        });

        const fileInput = document.getElementById('file-input');
        fileInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        const uploadBtn = document.getElementById('upload-btn');
        uploadBtn.addEventListener('click', () => this.uploadDocument());

        const removeFileBtn = document.getElementById('remove-file');
        removeFileBtn.addEventListener('click', () => this.clearSelectedFile());

        const refreshBtn = document.getElementById('refresh-documents');
        refreshBtn.addEventListener('click', () => this.loadDocuments());

        // Modal
        const modalClose = document.getElementById('modal-close');
        modalClose.addEventListener('click', () => this.closeModal());

        const modalOverlay = document.getElementById('modal-overlay');
        modalOverlay.addEventListener('click', () => this.closeModal());

        const downloadBtn = document.getElementById('download-document');
        downloadBtn.addEventListener('click', () => this.downloadDocument());

        const deleteBtn = document.getElementById('delete-document');
        deleteBtn.addEventListener('click', () => this.deleteDocument());

        // Hamburger menu
        const hamburger = document.getElementById('hamburger');
        hamburger.addEventListener('click', () => {
            document.getElementById('nav-menu').classList.toggle('active');
        });
    }

    handleFileSelect(file) {
        if (!file) return;

        // Validate file type
        if (file.type !== 'application/pdf') {
            this.showNotification('Por favor, selecione apenas arquivos PDF', 'error');
            return;
        }

        // Validate file size (50MB)
        if (file.size > 50 * 1024 * 1024) {
            this.showNotification('Arquivo muito grande. Máximo 50MB', 'error');
            return;
        }

        this.selectedFile = file;
        this.showSelectedFile(file);
    }

    showSelectedFile(file) {
        const selectedFileDiv = document.getElementById('selected-file');
        const fileName = selectedFileDiv.querySelector('.file-name');
        const fileSize = selectedFileDiv.querySelector('.file-size');

        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);

        selectedFileDiv.style.display = 'block';
        document.getElementById('upload-area').style.display = 'none';
        document.getElementById('upload-btn').disabled = false;
    }

    clearSelectedFile() {
        this.selectedFile = null;
        document.getElementById('selected-file').style.display = 'none';
        document.getElementById('upload-area').style.display = 'block';
        document.getElementById('upload-btn').disabled = true;
        document.getElementById('file-input').value = '';
        document.getElementById('upload-progress').style.display = 'none';
    }

    async uploadDocument() {
        if (!this.selectedFile) {
            this.showNotification('Selecione um arquivo', 'error');
            return;
        }

        const uploadBtn = document.getElementById('upload-btn');
        const progressDiv = document.getElementById('upload-progress');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');

        this.setButtonLoading(uploadBtn, true);
        progressDiv.style.display = 'block';

        try {
            // Step 1: Get presigned URL
            progressFill.style.width = '10%';
            progressText.textContent = '10% - Obtendo URL de upload...';

            const presignResponse = await fetch(`${this.apiBase}/presign-upload`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: this.selectedFile.name,
                    contentType: 'application/pdf'
                })
            });

            if (!presignResponse.ok) {
                const error = await presignResponse.json();
                throw new Error(error.detail || 'Erro ao obter URL de upload');
            }

            const { uploadUrl, documentId } = await presignResponse.json();

            // Step 2: Upload to S3
            progressFill.style.width = '30%';
            progressText.textContent = '30% - Enviando arquivo...';

            const uploadResponse = await fetch(uploadUrl, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/pdf',
                },
                body: this.selectedFile
            });

            if (!uploadResponse.ok) {
                throw new Error('Erro no upload para o S3');
            }

            progressFill.style.width = '70%';
            progressText.textContent = '70% - Upload concluído, notificando servidor...';

            // Step 3: Notify backend
            const notifyResponse = await fetch(`${this.apiBase}/notify-upload`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    documentId: documentId,
                    sizeBytes: this.selectedFile.size,
                    status: 'uploaded'
                })
            });

            if (!notifyResponse.ok) {
                throw new Error('Erro ao notificar upload');
            }

            progressFill.style.width = '100%';
            progressText.textContent = '100% - Concluído!';

            this.showNotification('Documento enviado com sucesso!', 'success');
            this.clearSelectedFile();
            
            // Reload documents
            setTimeout(() => {
                this.loadDocuments();
            }, 1000);

        } catch (error) {
            console.error('Upload error:', error);
            this.showNotification('Erro no upload: ' + error.message, 'error');
            progressDiv.style.display = 'none';
        } finally {
            this.setButtonLoading(uploadBtn, false);
        }
    }

    async loadDocuments() {
        const documentsGrid = document.getElementById('documents-grid');
        const documentsLoading = document.getElementById('documents-loading');
        const documentsEmpty = document.getElementById('documents-empty');

        documentsLoading.style.display = 'block';
        documentsEmpty.style.display = 'none';
        documentsGrid.innerHTML = '';

        try {
            const response = await fetch(`${this.apiBase}/documents`);

            if (!response.ok) {
                throw new Error('Erro ao carregar documentos');
            }

            const data = await response.json();
            const documents = data.documents || [];

            if (documents.length === 0) {
                documentsEmpty.style.display = 'block';
            } else {
                this.renderDocuments(documents);
            }

        } catch (error) {
            console.error('Load documents error:', error);
            this.showNotification('Erro ao carregar documentos: ' + error.message, 'error');
        } finally {
            documentsLoading.style.display = 'none';
        }
    }

    renderDocuments(documents) {
        const documentsGrid = document.getElementById('documents-grid');
        documentsGrid.innerHTML = '';

        documents.forEach(doc => {
            const docCard = this.createDocumentCard(doc);
            documentsGrid.appendChild(docCard);
        });
    }

    createDocumentCard(doc) {
        const card = document.createElement('div');
        card.className = 'document-card';

        const filename = doc.originalFilename || doc.filename || 'Documento';
        const sizeText = doc.sizeBytes ? this.formatFileSize(doc.sizeBytes) : 'N/A';
        const dateText = doc.uploadedAt ? this.formatDate(doc.uploadedAt) : '';

        card.innerHTML = `
            <div class="document-icon">📄</div>
            <div class="document-info">
                <h4 class="document-title">${this.escapeHtml(filename)}</h4>
                <p class="document-meta">📅 ${dateText}</p>
                <p class="document-size">📦 ${sizeText}</p>
            </div>
            <div class="document-actions">
                <button class="btn-icon view-btn" title="Visualizar detalhes">👁️</button>
            </div>
        `;

        const viewBtn = card.querySelector('.view-btn');
        viewBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.viewDocument(doc);
        });

        card.addEventListener('click', () => {
            this.viewDocument(doc);
        });

        return card;
    }

    viewDocument(doc) {
        this.currentDocumentId = doc.documentId;
        
        const modal = document.getElementById('document-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalFilename = document.getElementById('modal-filename');
        const modalSize = document.getElementById('modal-size');
        const modalDate = document.getElementById('modal-date');
        const modalDocId = document.getElementById('modal-doc-id');

        modalTitle.textContent = 'Detalhes do Documento';
        modalFilename.textContent = doc.originalFilename || doc.filename;
        modalSize.textContent = doc.sizeBytes ? this.formatFileSize(doc.sizeBytes) : 'N/A';
        modalDate.textContent = doc.uploadedAt ? this.formatDate(doc.uploadedAt) : 'N/A';
        modalDocId.textContent = doc.documentId;

        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    async downloadDocument() {
        if (!this.currentDocumentId) {
            this.showNotification('Documento não selecionado', 'error');
            return;
        }

        try {
            const response = await fetch(
                `${this.apiBase}/documents/${this.currentDocumentId}/download`
            );

            if (!response.ok) {
                throw new Error('Erro ao obter URL de download');
            }

            const { downloadUrl } = await response.json();

            // Open download URL
            window.open(downloadUrl, '_blank');
            this.showNotification('Download iniciado!', 'success');

        } catch (error) {
            console.error('Download error:', error);
            this.showNotification('Erro ao fazer download: ' + error.message, 'error');
        }
    }

    async deleteDocument() {
        if (!this.currentDocumentId) {
            this.showNotification('Documento não selecionado', 'error');
            return;
        }

        if (!confirm('Tem certeza que deseja deletar este documento? Esta ação não pode ser desfeita.')) {
            return;
        }

        try {
            const response = await fetch(
                `${this.apiBase}/documents/${this.currentDocumentId}`,
                { method: 'DELETE' }
            );

            if (!response.ok) {
                throw new Error('Erro ao deletar documento');
            }

            this.showNotification('Documento deletado com sucesso!', 'success');
            this.closeModal();
            this.loadDocuments();

        } catch (error) {
            console.error('Delete error:', error);
            this.showNotification('Erro ao deletar documento: ' + error.message, 'error');
        }
    }

    closeModal() {
        const modal = document.getElementById('document-modal');
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        this.currentDocumentId = null;
    }

    setButtonLoading(button, loading) {
        const btnText = button.querySelector('.btn-text');
        const btnLoading = button.querySelector('.btn-loading');
        
        if (loading) {
            btnText.style.display = 'none';
            btnLoading.style.display = 'flex';
            button.disabled = true;
        } else {
            btnText.style.display = 'block';
            btnLoading.style.display = 'none';
            button.disabled = false;
        }
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${this.getNotificationIcon(type)}</span>
                <span class="notification-message">${this.escapeHtml(message)}</span>
                <button class="notification-close">×</button>
            </div>
        `;

        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });

        container.appendChild(notification);

        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    getNotificationIcon(type) {
        switch (type) {
            case 'success': return '✓';
            case 'error': return '✗';
            case 'info': return 'ℹ';
            default: return 'ℹ';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            return new Date(dateString).toLocaleString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateString;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new PDFManager();
});
