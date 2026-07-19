let html5QrCode;
let cart = {};
let scanning = false;
let lastBarcode = "";
let lastScanTime = 0;

function addProduct(product) {

    if (!product.success) {
        alert("Product not found!");
        return;
    }

    const barcode = product.barcode;

    if (cart[barcode]) {

        cart[barcode].qty++;

    } else {

        cart[barcode] = {
            barcode: product.barcode,
            name: product.name,
            price: Number(product.price),
            qty: 1
        };

    }

    renderCart();
}

function renderCart(){

    const tbody=document.getElementById("orderItems");

    tbody.innerHTML="";

    let subtotal=0;

    let items=0;

    for(const barcode in cart){

        const p=cart[barcode];

        const total=p.price*p.qty;

        subtotal+=total;

        items+=p.qty;

        tbody.innerHTML+=`

        <tr>

            <td>${p.name}</td>

            <td>₹${p.price}</td>

            <td>${p.qty}</td>

            <td>₹${total}</td>

            <td>

                <button
                class="btn btn-danger btn-sm"
                onclick="removeProduct('${barcode}')">

                    <i class="bi bi-trash"></i>

                </button>

            </td>

        </tr>

        `;

    }

    if(items===0){

        tbody.innerHTML=`

        <tr>

            <td colspan="5" class="text-center">

                No product scanned.

            </td>

        </tr>

        `;

    }

    document.getElementById("itemCount").innerHTML=items;

    document.getElementById("subtotal").innerHTML="₹"+subtotal;

    document.getElementById("tax").innerHTML="₹0";

    document.getElementById("total").innerHTML="₹"+subtotal;

}

function removeProduct(barcode){

    delete cart[barcode];

    renderCart();

}

function onScanSuccess(decodedText){

    const now=Date.now();

    if(decodedText===lastBarcode && now-lastScanTime<1500){

        return;

    }

    lastBarcode=decodedText;

    lastScanTime=now;

    if(scanning) return;

    scanning=true;

    fetch("/staff/get_product",{

        method:"POST",

        headers:{

            "Content-Type":"application/json"

        },

        body:JSON.stringify({

            barcode:decodedText

        })

    })

    .then(res=>res.json())

    .then(data=>{

        addProduct(data);

        scanning=false;

    })

    .catch(err=>{

        console.log(err);

        console.log(document.getElementById("orderItems"));
        console.log(document.getElementById("itemCount"));
        console.log(document.getElementById("subtotal"));
        console.log(document.getElementById("tax"));
        console.log(document.getElementById("total"));

        scanning=false;

    });

}

function completeOrder() {

    if (Object.keys(cart).length === 0) {

        alert("Cart is empty.");

        return;

    }

    fetch("/staff/complete_order", {

        method: "POST",

        headers: {

            "Content-Type": "application/json"

        },

        body: JSON.stringify({

            payment_method:
                document.getElementById("paymentMethod").value,

            cart: Object.values(cart)

        })

    })

    .then(response => response.json())

    .then(data => {

        console.log(data);

        alert(data.message);

        if (data.success) {

            window.location.href = "/staff/receipt/" + data.sale_id;

            cart = {};

            renderCart();

        }

    });

}

document.addEventListener("DOMContentLoaded", startScanner);

async function startScanner(){

    html5QrCode = new Html5Qrcode("reader");

    const cameras = await Html5Qrcode.getCameras();

    if(cameras.length===0){

        document.getElementById("status").innerHTML="No Camera Found";

        return;

    }

    const camera =
        cameras.find(c=>c.label.toLowerCase().includes("camo"))
        || cameras[0];

    await html5QrCode.start(

        camera.id,

        {
            fps: 10,
            qrbox: {
                width: 300,
                height: 120
            },
            aspectRatio: 2.5
        },

        onScanSuccess

    );

}

document.getElementById("completeOrder").addEventListener("click", function completeOrder() {

    console.log("Complete Order clicked");

    console.log(cart);

    if (Object.keys(cart).length === 0) {

        alert("Cart is empty.");

        return;

    }

    console.log("Sending request...");

    fetch("/staff/complete_order", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            payment_method: document.getElementById("paymentMethod").value,

            cart: Object.values(cart)

        })

    })

    .then(response => {
        console.log(response);
        return response.json();
    })

    .then(data => {

        console.log("JSON:", data);

        if (data.success) {

            alert(data.message);

            window.location.href = "/staff/receipt/" + data.sale_id;
            
            //window.location.href = "/staff/receipt/" + data.sale_id;
            //above is the code to to open the tab on the same page
            // OR, if you prefer a new tab:
            // window.open("/staff/receipt/" + data.sale_id, "_blank");

        } else {

            alert(data.message);

        }

    })
    .catch(err => {

        console.error(err);

    });

});