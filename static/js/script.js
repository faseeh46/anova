// script.js
let imageUploaded = false;
let barcodeData = '';

document.getElementById('image').onchange = function(event) {
    let formData = new FormData(document.getElementById('upload-image-form'));
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('barcode').textContent = 'Error: ' + data.error;
            clearRowData();
        } else {
            barcodeData = data.barcode;
            document.getElementById('barcode').textContent = 'Barcode: ' + barcodeData;
            imageUploaded = true;
            console.log('Image uploaded and barcode data obtained:', barcodeData);  // Debugging statement
            triggerScanIfReady();
        }
    })
    .catch(error => console.error('Error:', error));
};

document.getElementById('csvfile').onchange = function(event) {
    let formData = new FormData(document.getElementById('upload-csv-form'));
    fetch('/upload_csv', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        csvUploaded = true;
        console.log('CSV file uploaded successfully');  // Debugging statement
        triggerScanIfReady();
    })
    .catch(error => console.error('Error:', error));
};

function triggerScanIfReady() {
    if (csvUploaded && imageUploaded) {
        console.log('Both CSV and image uploaded, fetching row data...');  // Debugging statement
        fetchRowData(barcodeData);
    } else if (csvUploaded) {
        console.log('CSV already uploaded, waiting for image upload to fetch row data...');  // Debugging statement
    } else {
        console.log('Waiting for both CSV and image uploads...');  // Debugging statement
    }
}

function fetchRowData(barcode) {
    console.log('Fetching row data for barcode:', barcode);  // Debugging statement
    fetch('/fetch_row', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ barcode: barcode })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('produit').textContent = 'Error: ' + data.error;
            clearRowData();
        } else {
            document.getElementById('produit').textContent = 'Produit: ' + data.produit;
            document.getElementById('ppv').textContent = 'PPV: ' + data.ppv;
            document.getElementById('pph').textContent = 'PPH: ' + data.pph;
            console.log('Row data fetched successfully:', data);  // Debugging statement
        }
    })
    .catch(error => console.error('Error:', error));
}

function clearRowData() {
    document.getElementById('produit').textContent = '';
    document.getElementById('ppv').textContent = '';
    document.getElementById('pph').textContent = '';
}
