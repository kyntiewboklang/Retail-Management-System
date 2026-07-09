console.log("ZXing Scanner Loaded");

const codeReader = new ZXing.BrowserMultiFormatReader();

let selectedDeviceId = null;
let scannerRunning = false;

const startBtn = document.getElementById("startCamera");
const stopBtn = document.getElementById("stopCamera");

const barcodeResult = document.getElementById("barcodeResult");
const skuInput = document.getElementById("sku");

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
        alert("Unable to access the camera.");
        return false;
    }
}

startBtn.addEventListener("click", async () => {

    if (scannerRunning) return;

    const success = await loadCameras();

    if (!success) return;

    scannerRunning = true;

    console.log("Starting scanner...");

    codeReader.decodeFromVideoDevice(
    selectedDeviceId,
    "reader",
    (result, err) => {

        if (result) {
            console.log("SUCCESS:", result.getText());
        }

        if (err) {
            console.log(err);
        }
    });

});

async function lookupProduct(barcode) {

    try {

        const response = await fetch(`/lookup-barcode/${barcode}`);

        const data = await response.json();

        console.log(data);

        if (!data.found) {

            alert("Product not found.");

            return;

        }

        document.getElementById("product_name").value =
            data.product_name || "";

        document.getElementById("brand").value =
            data.brand || "";

        document.getElementById("description").value =
            data.description || "";

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

    } catch (err) {

        console.error(err);

    }

}

function stopScanner() {

    if (!scannerRunning) return;

    codeReader.reset();

    scannerRunning = false;
}

stopBtn.addEventListener("click", stopScanner);