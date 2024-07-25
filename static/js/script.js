// script.js

let imageUploaded = false;
let barcodeData = '';

document.getElementById('image').onchange = function(event) {
    console.log('Image file selected');
    let formData = new FormData(document.getElementById('upload-image-form'));
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            barcodeData = data.barcode;
            console.log('Image uploaded and barcode data obtained:', barcodeData);
            window.location.href = `/results?barcode=${barcodeData}`;
        }
    })
    .catch(error => console.error('Error:', error));
};

document.getElementById('csvfile').onchange = function(event) {
    console.log('CSV file selected');
    let formData = new FormData(document.getElementById('upload-csv-form'));
    fetch('/upload_csv', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        let csvUploaded = true;
        console.log('CSV file uploaded successfully');
        triggerScanIfReady();
    })
    .catch(error => console.error('Error:', error));
};

function triggerScanIfReady() {
    if (csvUploaded && imageUploaded) {
        console.log('Both CSV and image uploaded, fetching row data...');
        fetchRowData(barcodeData);
    } else if (csvUploaded) {
        console.log('CSV already uploaded, waiting for image upload to fetch row data...');
    } else {
        console.log('Waiting for both CSV and image uploads...');
    }
}

function fetchRowData(barcode) {
    console.log('Fetching row data for barcode:', barcode);
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
            alert('Error: ' + data.error);
        } else {
            document.getElementById('produit').textContent = 'Produit: ' + data.produit;
            document.getElementById('ppv').textContent = 'PPV: ' + data.ppv;
            document.getElementById('pph').textContent = 'PPH: ' + data.pph;
            console.log('Row data fetched successfully:', data);
        }
    })
    .catch(error => console.error('Error:', error));
}

function clearRowData() {
    document.getElementById('produit').textContent = '';
    document.getElementById('ppv').textContent = '';
    document.getElementById('pph').textContent = '';
}
