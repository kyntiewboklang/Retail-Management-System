const scanBtn = document.getElementById("scanBtn");
const reader = document.getElementById("reader");
const barcodeInput = document.getElementById("barcode");
const status = document.getElementById("status");

let html5QrCode = null;

scanBtn.addEventListener("click", async function () {

    reader.style.display = "block";

    html5QrCode = new Html5Qrcode("reader");

    try {

        const cameras = await Html5Qrcode.getCameras(); 
        console.log(cameras); 
        cameras.forEach((camera, index) => {
             console.log(index, camera.id, camera.label);
        });

        //const cameras = await Html5Qrcode.getCameras();

        if (!cameras.length) {

            status.innerHTML = "No camera found.";
            return;

        }

        const camoCamera = cameras.find(camera =>
            camera.label.toLowerCase().includes("camo")
        );

        if (!camoCamera) {
            alert("Camo camera not found!");
            return;
        }

        await html5QrCode.start(

            camoCamera.id,

            {
                fps: 10,
                qrbox: {
                    width: 300,
                    height: 120
                },
                aspectRatio: 2.5
            },

            function(decodedText) {

                barcodeInput.value = decodedText;

                status.innerHTML =
                    "<span class='text-success'>Barcode scanned successfully!</span>";

                html5QrCode.stop();

                reader.style.display = "none";

            }

        );

    }

    catch(err){

        console.log(err);

        status.innerHTML = err;

    }

});