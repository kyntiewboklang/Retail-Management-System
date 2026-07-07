const statusBox = document.getElementById("status");

const html5QrCode = new Html5Qrcode("reader");

function onScanSuccess(decodedText, decodedResult) {

    statusBox.className = "alert alert-success text-center mt-4";
    statusBox.innerHTML =
        "<strong>Barcode Detected</strong><br>" + decodedText;

    html5QrCode.stop().then(() => {

        window.location.href =
            "/new-orders?barcode=" +
            encodeURIComponent(decodedText);

    });

}

function onScanFailure(error) {
    // Ignore scan failures while searching
}

Html5Qrcode.getCameras().then(devices => {

    if (!devices.length) {

        statusBox.className = "alert alert-danger mt-4";
        statusBox.innerHTML = "No camera found.";

        return;
    }

    html5QrCode.start(

        { facingMode: "environment" },

        {
            fps: 15,

            qrbox: {
                width: 280,
                height: 150
            },

            aspectRatio: 1.777,

            rememberLastUsedCamera: true,

            supportedScanTypes: [
                Html5QrcodeScanType.SCAN_TYPE_CAMERA
            ]
        },

        onScanSuccess,

        onScanFailure

    );

}).catch(err => {

    statusBox.className = "alert alert-danger mt-4";
    statusBox.innerHTML = err;

});
