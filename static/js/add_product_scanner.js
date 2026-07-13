console.log("Scanner JS Loaded");

const codeReader = new ZXing.BrowserMultiFormatReader();

let selectedDeviceId = null;
let scannerRunning = false;

const startBtn = document.getElementById("startCamera");
const stopBtn = document.getElementById("stopCamera");

const barcodeResult = document.getElementById("barcodeResult");
const skuInput = document.getElementById("sku");

// -------------------------
// Load Camera
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

    } catch (err) {

        console.error(err);
        alert("Unable to access camera.");

        return false;
    }
}

// -------------------------
// Lookup Product
// -------------------------
async function lookupProduct(barcode) {

    try {

        console.log("Searching:", barcode);

        const response = await fetch(`/api/search_product/${barcode}`);

        const data = await response.json();

        console.log(data);

        if (data.source === "openfoodfacts") {
            alert("Product found in Open Food Facts.\nPlease verify the details before saving.");
        }

        if (!data.found) {

            alert("Product was not found in your inventory or Open Food Facts.\n\nPlease enter the details manually.");
            return;
        }

        document.getElementById("product_name").value =
            data.product_name || "";

        document.getElementById("brand").value =
            data.brand || "";

        document.getElementById("price").value =
            data.price || "";

        document.getElementById("quantity").value =
            data.quantity || "";

        document.getElementById("supplier").value =
            data.supplier || "";

        document.getElementById("description").value =
            data.description || "";

        // Match category if possible
        const category = document.getElementById("category");

        for (const option of category.options) {

            if (
                data.category &&
                data.category.toLowerCase().includes(option.text.toLowerCase())
            ) {
                category.value = option.value;
                break;
            }

        }

        console.log("Product loaded successfully.");

    } catch (err) {

        console.error(err);

    }

}

// -------------------------
// Start Scanner
// -------------------------
startBtn.addEventListener("click", async () => {

    if (scannerRunning) return;

    const success = await loadCameras();

    if (!success) return;

    scannerRunning = true;

    console.log("Starting scanner...");

    codeReader.decodeOnceFromVideoDevice(
        selectedDeviceId,
        "reader"
    )
    .then(result => {

    const barcode = result.getText();

    console.log("Scanned:", barcode);

    barcodeResult.value = barcode;
    skuInput.value = barcode;

    lookupProduct(barcode);

    })
    
    .catch(err => {

        console.error(err);

    });

});

// -------------------------
// Manual Barcode Entry
// -------------------------
skuInput.addEventListener("change", function () {

    const barcode = skuInput.value.trim();

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

document.getElementById("clearForm").addEventListener("click", function () {

    // Clear the form
    document.querySelector("form").reset();

    // Clear scanner fields
    document.getElementById("barcodeResult").value = "";
    document.getElementById("sku").value = "";

    // Clear any auto-filled fields
    document.getElementById("product_name").value = "";
    document.getElementById("brand").value = "";
    document.getElementById("price").value = "";
    document.getElementById("quantity").value = "";
    document.getElementById("supplier").value = "";
    document.getElementById("description").value = "";

    // Reset category to first option
    document.getElementById("category").selectedIndex = 0;

});