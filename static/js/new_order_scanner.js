console.log("New Order Scanner Loaded");

const codeReader = new ZXing.BrowserMultiFormatReader();

let selectedDeviceId = null;
let scannerRunning = false;

const startBtn = document.getElementById("startCamera");
const stopBtn = document.getElementById("stopCamera");

const barcodeResult = document.getElementById("barcodeResult");
const barcodeInput = document.getElementById("barcodeInput");

const orderTable = document.getElementById("orderTable");

// -------------------------
// Load Cameras
// -------------------------
async function loadCameras() {

    try {

        await navigator.mediaDevices.getUserMedia({ video: true });

        const devices = await codeReader.listVideoInputDevices();

        if (devices.length === 0) {

            alert("No camera found.");
            return false;

        }

        const backCamera = devices.find(device =>
            device.label.toLowerCase().includes("back")
        );

        selectedDeviceId = backCamera
            ? backCamera.deviceId
            : devices[0].deviceId;

        return true;

    }

    catch (err) {

        console.error(err);

        alert("Unable to access camera.");

        return false;

    }

}

// -------------------------
// Search Product
// -------------------------
async function lookupProduct(barcode) {

    try {

        const response = await fetch(`/api/search_product/${barcode}`);

        const data = await response.json();

        if (!data.found) {

            alert("Product not found.");

            return;

        }

        addProduct(data, barcode);

    }

    catch (err) {

        console.error(err);

    }

}

// -------------------------
// Add Product To Table
// -------------------------
function addProduct(product, barcode) {

    const existingRow = document.querySelector(
        `tr[data-barcode="${barcode}"]`
    );

    // Already exists
    if (existingRow) {

        const qtyInput = existingRow.querySelector(".qty");

        let qty = parseInt(qtyInput.value);

        qty++;

        qtyInput.value = qty;

        const totalCell = existingRow.querySelector(".line-total");

        totalCell.innerText =
            "₹" + (qty * Number(product.price)).toFixed(2);

        updateSummary();

        return;

    }

    // Create row
    const row = document.createElement("tr");

    row.dataset.barcode = barcode;

    row.innerHTML = `

        <td>${product.product_name}</td>

        <td class="price">${Number(product.price).toFixed(2)}</td>

        <td>

            <div class="btn-group">

                <button class="btn btn-outline-secondary minus">-</button>

                <input
                    type="text"
                    class="form-control text-center qty"
                    value="1"
                    style="width:60px;">

                <button class="btn btn-outline-secondary plus">+</button>

            </div>

        </td>

        <td class="line-total">

            ₹${Number(product.price).toFixed(2)}

        </td>

        <td>

            <button class="btn btn-danger btn-sm remove">

                <i class="bi bi-trash"></i>

            </button>

        </td>

    `;

    orderTable.appendChild(row);

    updateSummary();

}

// -------------------------
// Update Summary
// -------------------------
function updateSummary() {

    const rows = document.querySelectorAll("#orderTable tr");

    let items = 0;

    let total = 0;

    rows.forEach(row => {

        const qty = parseInt(
            row.querySelector(".qty").value
        );

        const price = parseFloat(
            row.querySelector(".price").innerText
        );

        items += qty;

        total += qty * price;

    });

    document.getElementById("totalItems").innerText = items;

    document.getElementById("subtotal").innerText =
        "₹" + total.toFixed(2);

    document.getElementById("grandTotal").innerText =
        "₹" + total.toFixed(2);

}

// -------------------------
// Scanner
// -------------------------
startBtn.addEventListener("click", async () => {

    if (scannerRunning) return;

    const success = await loadCameras();

    if (!success) return;

    scannerRunning = true;

    codeReader.decodeOnceFromVideoDevice(
        selectedDeviceId,
        "reader"
    )
    .then(result => {

        const barcode = result.getText();

        barcodeResult.innerText = barcode;

        barcodeInput.value = barcode;

        lookupProduct(barcode);

        stopScanner();

    })
    .catch(err => {

        console.error(err);

    });

});

// -------------------------
// Manual Search
// -------------------------
barcodeInput.addEventListener("change", () => {

    const barcode = barcodeInput.value.trim();

    if (barcode !== "") {

        lookupProduct(barcode);

    }

});

// -------------------------
// Stop Scanner
// -------------------------
function stopScanner() {

    if (!scannerRunning) return;

    codeReader.reset();

    scannerRunning = false;

}

stopBtn.addEventListener("click", stopScanner);

// -------------------------
// Table Events
// -------------------------
document.addEventListener("click", function (e) {

    const row = e.target.closest("tr");

    if (!row) return;

    const qtyInput = row.querySelector(".qty");

    const price = parseFloat(
        row.querySelector(".price").innerText
    );

    if (e.target.classList.contains("plus")) {

        qtyInput.value++;

    }

    if (e.target.classList.contains("minus")) {

        if (qtyInput.value > 1)
            qtyInput.value--;

    }

    if (e.target.closest(".remove")) {

        row.remove();

        updateSummary();

        return;

    }

    row.querySelector(".line-total").innerText =
        "₹" + (qtyInput.value * price).toFixed(2);

    updateSummary();

});