document.addEventListener('DOMContentLoaded', () => {
// --- DOM Element Selectors ---
    const uploadSection = document.getElementById('upload-section');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultsArea = document.getElementById('results-preview-area');
    const errorArea = document.getElementById('error-message-area');
    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn');
    const startOverBtn = document.getElementById('start-over-btn');
    const downloadBtnExcel = document.getElementById('download-btn-excel');
    const fileNameDisplay = document.getElementById('file-name-display');
    const errorDetails = document.getElementById('error-details');
    const themeSlider = document.getElementById('theme-slider');

    let selectedFile = null;
    let currentResultData = null;

// --- Theme Switcher Logic ---
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            document.body.classList.add('dark-mode');
            themeSlider.checked = true;
        } else {
            document.body.classList.remove('dark-mode');
            themeSlider.checked = false;
        }
    };

    themeSlider.addEventListener('change', () => {
        const theme = themeSlider.checked ? 'dark' : 'light';
        localStorage.setItem('theme', theme);
        applyTheme(theme);
    });
    
// Apply saved theme on page load
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);


// --- Event Listeners ---
    fileInput.addEventListener('change', handleFileSelect);
    uploadBtn.addEventListener('click', startPipeline);
    startOverBtn.addEventListener('click', resetUI);
    downloadBtnExcel.addEventListener('click', downloadAsExcel);

    function handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            if (file.type !== 'application/pdf') {
                showError('Only PDF files are allowed.');
                resetFileInput();
                return;
            }
            selectedFile = file;
            fileNameDisplay.textContent = file.name;
            uploadBtn.disabled = false;
        }
    }

// --- UI State Management ---
    function resetUI() {
        uploadSection.classList.remove('hidden');
        loadingIndicator.classList.add('hidden');
        resultsArea.classList.add('hidden');
        errorArea.classList.add('hidden');
        resetFileInput();
    }

    function resetFileInput() {
        fileInput.value = '';
        selectedFile = null;
        currentResultData = null;
        fileNameDisplay.textContent = '';
        uploadBtn.disabled = true;
    }

    function showLoading() {
        uploadSection.classList.add('hidden');
        errorArea.classList.add('hidden');
        resultsArea.classList.add('hidden');
        loadingIndicator.classList.remove('hidden');
    }
    
    function showError(message) {
        uploadSection.classList.add('hidden');
        loadingIndicator.classList.add('hidden');
        errorDetails.textContent = message;
        errorArea.classList.remove('hidden');
        
// Add a start over button in the error area
        const tryAgainBtn = document.createElement('button');
        tryAgainBtn.textContent = 'Try Again';
        tryAgainBtn.className = 'button-primary';
        tryAgainBtn.style.marginTop = '20px';
        tryAgainBtn.onclick = resetUI;
        if (!errorArea.querySelector('button')) {
            errorArea.appendChild(tryAgainBtn);
        }
    }

// --- Main Pipeline Logic ---
    async function startPipeline() {
        if (!selectedFile) return;

        showLoading();

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/process-pdf', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'An unknown backend error occurred.');
            }

            currentResultData = result;
            renderResults(result);

        } catch (error) {
            console.error("Pipeline Error:", error);
            showError(error.message);
        }
    }

    function renderResults(data) {
        const tableBody = document.getElementById('preview-table-body');
        tableBody.innerHTML = ''; 
// Clear previous results

        const attributes = {
            "Product Title": data.product_title,
            "EAN/UPC Code": data.ean_upc,
            "Color": data.color,
            "Material": data.material,
            "Battery": data.battery,
            "Power": data.power,
            "Dimensions": data.dimensions,
            "Description": data.description
        };

        for (const [key, value] of Object.entries(attributes)) {
            const row = `<tr>
                <td>${key}</td>
                <td>${value || 'N/A'}</td>
            </tr>`;
            tableBody.innerHTML += row;
        }

        loadingIndicator.classList.add('hidden');
        resultsArea.classList.remove('hidden');
    }

    function downloadAsExcel() {
        if (!currentResultData) return;
        const headers = ["Attribute", "Value"];
        const data = [
            ["Product Title", currentResultData.product_title],
            ["EAN/UPC Code", currentResultData.ean_upc],
            ["Color", currentResultData.color],
            ["Material", currentResultData.material],
            ["Battery", currentResultData.battery],
            ["Power", currentResultData.power],
            ["Dimensions", currentResultData.dimensions],
            ["Description", currentResultData.description],
            ["Image URL", currentResultData.image_url_1]
        ];
        let csvContent = headers.join(",") + "\n" + data.map(row => 
            row.map(field => `"${String(field || '').replace(/"/g, '""')}"`).join(",")
        ).join("\n");
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", `${(currentResultData.product_title || 'product').replace(/\s+/g, '_')}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});
